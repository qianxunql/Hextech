from pathlib import Path
import re

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from aiproject.config import get_settings
from aiproject.llms import build_chat_model
from aiproject.scraper import load_champion_pages_from_index_html, load_hextech_pages_from_index_html, parse_page_text
from aiproject.state import AgentState
from aiproject.text_index import search_text_documents


SYSTEM_PROMPT = (
    "你是“英雄联盟海克斯大乱斗助手”，专门基于知识库回答英雄联盟海克斯大乱斗相关问题。"
    "优先使用检索资料回答；如果资料不足，要明确说明不知道，不要编造。"
    "资料来源是 ARAM Hextech Wiki，不要把它称作英雄联盟官方数据。"
    "不要在回答中展示海克斯编号或内部 ID。"
    "回答要简洁、实战导向，适合玩家快速决策。"
)


def _exact_champion_context(question: str) -> list[tuple[str, str]]:
    try:
        pages = load_champion_pages_from_index_html("data/html/champions_index.html")
    except RuntimeError:
        return []

    question_lower = question.lower()
    matches: list[tuple[str, str]] = []
    for page in pages:
        aliases = [page.name]
        for line in page.text.splitlines():
            if "：" in line:
                _, value = line.split("：", 1)
                aliases.append(value.strip())

        if any(alias and alias.lower() in question_lower for alias in aliases):
            local_detail = Path("data/html/champions") / f"{page.name}.html"
            if local_detail.exists():
                html = local_detail.read_text(encoding="utf-8", errors="replace")
                matches.append((page.url, parse_page_text(html)))
            else:
                matches.append((page.url, page.text))

    return matches


def _compact_alias(name: str) -> str:
    compact = re.sub(r"[\W_]+", "", name)
    for token in ("你的", "他们", "它们", "这个", "那个", "之", "的", "出"):
        compact = compact.replace(token, "")
    if len(compact) >= 3:
        return f"{compact[0]}{compact[-1]}"
    return compact


def _hextech_aliases(pages) -> dict[str, set[str]]:
    alias_counts: dict[str, int] = {}
    raw_aliases: dict[str, set[str]] = {}
    for page in pages:
        aliases = {page.hextech_id, page.name}
        short_alias = _compact_alias(page.name)
        if len(short_alias) >= 2 and short_alias != page.name:
            aliases.add(short_alias)
        raw_aliases[page.hextech_id] = aliases
        for alias in aliases:
            alias_counts[alias.lower()] = alias_counts.get(alias.lower(), 0) + 1

    return {
        hextech_id: {alias for alias in aliases if alias_counts.get(alias.lower(), 0) == 1}
        for hextech_id, aliases in raw_aliases.items()
    }


def _exact_hextech_context(question: str) -> list[tuple[str, str]]:
    try:
        pages = load_hextech_pages_from_index_html("海克斯强化列表 _ ARAM Hextech Wiki.html")
    except RuntimeError:
        return []

    question_lower = question.lower()
    aliases_by_id = _hextech_aliases(pages)
    matches: list[tuple[str, str]] = []
    for page in pages:
        aliases = aliases_by_id.get(page.hextech_id, {page.hextech_id, page.name})
        if not any(alias and alias.lower() in question_lower for alias in aliases):
            continue

        local_detail = Path("data/html/hextech") / f"{page.hextech_id}.html"
        if local_detail.exists():
            html = local_detail.read_text(encoding="utf-8", errors="replace")
            detail_text = parse_page_text(html)
        else:
            detail_text = page.text

        text = "\n".join(
            [
                f"中文名：{page.name}",
                f"评级：{page.tier}",
                f"目录描述：{page.description}",
                "",
                detail_text,
            ]
        )
        matches.append((page.url, text))

    return matches


def _is_hextech_question(question: str) -> bool:
    keywords = ("海克斯", "强化", "符文", "棱彩", "黄金阶", "白银阶")
    return any(keyword in question for keyword in keywords)


def retrieve_node(state: AgentState) -> dict:
    question = state["messages"][-1].content
    settings = get_settings()
    champion_matches = _exact_champion_context(question)
    hextech_matches = _exact_hextech_context(question)
    exact_matches = [*champion_matches, *hextech_matches]

    docs = []
    text_context: list[str] = []
    text_sources: list[str] = []
    if settings.retrieval_mode == "text":
        text_context, text_sources = search_text_documents(question, k=8)
    elif not (hextech_matches and not champion_matches):
        try:
            from aiproject.vectorstore import get_vectorstore

            vectorstore = get_vectorstore(settings)
            docs = vectorstore.similarity_search(question, k=5)
            if _is_hextech_question(question):
                docs.extend(
                    vectorstore.similarity_search(
                        question,
                        k=5,
                        filter={"hextech": {"$ne": ""}},
                    )
                )
        except Exception:
            if not exact_matches:
                raise

    context = [text for _, text in exact_matches]
    seen_context: set[str] = set(context)
    for text in text_context:
        if text in seen_context:
            continue
        seen_context.add(text)
        context.append(text)

    for doc in docs:
        if doc.page_content in seen_context:
            continue
        seen_context.add(doc.page_content)
        context.append(doc.page_content)

    source_set = {source for source, _ in exact_matches}
    source_set.update(text_sources)
    source_set.update(
        str(doc.metadata["source"])
        for doc in docs
        if doc.metadata.get("source")
    )
    sources = sorted(source_set)
    return {"context": context, "sources": sources}


def answer_node(state: AgentState, config: RunnableConfig | None = None) -> dict:
    settings = get_settings()
    llm = build_chat_model(settings)
    messages = build_answer_messages(state)
    response = llm.invoke(messages, config=config)
    return {"messages": [response]}


def build_answer_messages(state: AgentState) -> list:
    context = "\n\n---\n\n".join(state.get("context", [])) or "没有检索到相关资料。"
    return [
        SystemMessage(content=f"{SYSTEM_PROMPT}\n\n知识库资料：\n{context}"),
        *state["messages"],
    ]
