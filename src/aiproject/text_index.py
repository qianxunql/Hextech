from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re

from aiproject.scraper import load_champion_pages_from_index_html, load_hextech_pages_from_index_html, parse_page_text


_CJK_RE = re.compile(r"[\u4e00-\u9fff]{2,}")
_WORD_RE = re.compile(r"[A-Za-z0-9_]{2,}")
_STOPWORDS = {
    "什么",
    "怎么",
    "哪个",
    "哪些",
    "适合",
    "推荐",
    "海克斯",
    "强化",
    "英雄",
    "玩法",
    "大乱斗",
    "hextech",
    "aram",
}


@dataclass(frozen=True)
class TextDocument:
    content: str
    source: str
    title: str
    kind: str
    aliases: tuple[str, ...]


def _tokens(text: str) -> list[str]:
    values: list[str] = []
    lowered = text.lower()
    values.extend(match.group(0) for match in _WORD_RE.finditer(lowered))
    for match in _CJK_RE.finditer(text):
        word = match.group(0)
        values.append(word)
        if len(word) > 2:
            values.extend(word[index : index + 2] for index in range(len(word) - 1))
    return [token for token in values if token not in _STOPWORDS]


def _fields_from_text(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if "：" not in line:
            continue
        key, value = line.split("：", 1)
        fields[key.strip()] = value.strip()
    return fields


def _read_detail(path: Path, fallback: str) -> str:
    if not path.exists():
        return fallback
    html = path.read_text(encoding="utf-8", errors="replace")
    return parse_page_text(html)


@lru_cache(maxsize=1)
def load_text_documents() -> tuple[TextDocument, ...]:
    documents: list[TextDocument] = []

    try:
        champion_pages = load_champion_pages_from_index_html("data/html/champions_index.html")
    except RuntimeError:
        champion_pages = []

    for page in champion_pages:
        detail = _read_detail(Path("data/html/champions") / f"{page.name}.html", page.text)
        fields = _fields_from_text(page.text)
        champion_name = fields.get("英雄名称", page.name)
        title = fields.get("英雄称号", "")
        aliases = tuple(value for value in {page.name, champion_name, title} if value)
        content = "\n".join(
            part
            for part in [
                f"英雄页面：{champion_name}",
                f"URL 名：{page.name}",
                f"称号：{title}" if title else "",
                detail,
            ]
            if part
        )
        documents.append(
            TextDocument(
                content=content,
                source=page.url,
                title=champion_name,
                kind="champion",
                aliases=aliases,
            )
        )

    try:
        hextech_pages = load_hextech_pages_from_index_html("海克斯强化列表 _ ARAM Hextech Wiki.html")
    except RuntimeError:
        hextech_pages = []

    for page in hextech_pages:
        detail = _read_detail(Path("data/html/hextech") / f"{page.hextech_id}.html", page.text)
        aliases = tuple(value for value in {page.name, page.hextech_id} if value)
        content = "\n".join(
            part
            for part in [
                f"海克斯页面：{page.name}",
                f"评级：{page.tier}",
                f"目录描述：{page.description}",
                detail,
            ]
            if part
        )
        documents.append(
            TextDocument(
                content=content,
                source=page.url,
                title=page.name,
                kind="hextech",
                aliases=aliases,
            )
        )

    return tuple(documents)


def _score_document(question: str, question_tokens: list[str], document: TextDocument) -> int:
    haystack = f"{document.title}\n{' '.join(document.aliases)}\n{document.content}".lower()
    question_lower = question.lower()
    score = 0

    for alias in document.aliases:
        if alias and alias.lower() in question_lower:
            score += 80

    if document.kind == "hextech" and any(word in question for word in ("海克斯", "强化", "棱彩", "黄金", "白银")):
        score += 8
    if document.kind == "champion" and any(word in question for word in ("英雄", "出装", "玩法", "适合谁")):
        score += 8

    seen: set[str] = set()
    for token in question_tokens:
        if token in seen:
            continue
        seen.add(token)
        if token in haystack:
            score += 4 + min(haystack.count(token), 6)

    return score


def search_text_documents(question: str, k: int = 8) -> tuple[list[str], list[str]]:
    documents = load_text_documents()
    question_tokens = _tokens(question)
    scored = [
        (_score_document(question, question_tokens, document), document)
        for document in documents
    ]
    ranked = [item for item in sorted(scored, key=lambda item: item[0], reverse=True) if item[0] > 0]

    if not ranked:
        return [], []

    selected = [document for _, document in ranked[:k]]
    return [document.content for document in selected], sorted({document.source for document in selected})
