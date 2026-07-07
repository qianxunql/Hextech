from pathlib import Path

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from aiproject.config import get_settings
from aiproject.llms import build_chat_model
from aiproject.scraper import load_champion_pages_from_index_html, load_hextech_pages_from_index_html, parse_page_text
from aiproject.state import AgentState
from aiproject.vectorstore import get_vectorstore


SYSTEM_PROMPT = (
    "你是“英雄联盟海克斯大乱斗助手”，专门基于知识库回答英雄联盟海克斯大乱斗相关问题。"
    "优先使用检索资料回答；如果资料不足，要明确说明不知道，不要编造。"
    "资料来源是 ARAM Hextech Wiki，不要把它称作英雄联盟官方数据。"
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


def _exact_hextech_context(question: str) -> list[tuple[str, str]]:
    try:
        pages = load_hextech_pages_from_index_html("海克斯强化列表 _ ARAM Hextech Wiki.html")
    except RuntimeError:
        return []

    question_lower = question.lower()
    matches: list[tuple[str, str]] = []
    for page in pages:
        aliases = [page.hextech_id, page.name]
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
                f"海克斯ID：{page.hextech_id}",
                f"中文名：{page.name}",
                f"评级：{page.tier}",
                f"目录描述：{page.description}",
                "",
                detail_text,
            ]
        )
        matches.append((page.url, text))

    return matches


def retrieve_node(state: AgentState) -> dict:
    question = state["messages"][-1].content
    exact_matches = _exact_champion_context(question)
    exact_matches.extend(_exact_hextech_context(question))
    if exact_matches:
        return {
            "context": [text for _, text in exact_matches],
            "sources": sorted({source for source, _ in exact_matches}),
        }

    vectorstore = get_vectorstore(get_settings())
    docs = vectorstore.similarity_search(question, k=5)
    context = [text for _, text in exact_matches]
    context.extend(doc.page_content for doc in docs)
    source_set = {source for source, _ in exact_matches}
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
    context = "\n\n---\n\n".join(state.get("context", [])) or "没有检索到相关资料。"
    messages = [
        SystemMessage(content=f"{SYSTEM_PROMPT}\n\n知识库资料：\n{context}"),
        *state["messages"],
    ]
    response = llm.invoke(messages, config=config)
    return {"messages": [response]}
