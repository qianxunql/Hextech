from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from collections import Counter
import math
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


@dataclass(frozen=True)
class TextIndex:
    documents: tuple[TextDocument, ...]
    term_frequencies: tuple[Counter[str], ...]
    document_frequencies: dict[str, int]
    document_lengths: tuple[int, ...]
    average_document_length: float


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


@lru_cache(maxsize=1)
def load_text_index() -> TextIndex:
    documents = load_text_documents()
    term_frequencies: list[Counter[str]] = []
    document_frequencies: dict[str, int] = {}
    document_lengths: list[int] = []

    for document in documents:
        indexed_text = "\n".join([document.title, " ".join(document.aliases), document.content])
        frequencies = Counter(_tokens(indexed_text))
        term_frequencies.append(frequencies)
        document_lengths.append(sum(frequencies.values()))
        for token in frequencies:
            document_frequencies[token] = document_frequencies.get(token, 0) + 1

    average_document_length = sum(document_lengths) / len(document_lengths) if document_lengths else 0.0
    return TextIndex(
        documents=documents,
        term_frequencies=tuple(term_frequencies),
        document_frequencies=document_frequencies,
        document_lengths=tuple(document_lengths),
        average_document_length=average_document_length,
    )


def _bm25_score(
    question_tokens: list[str],
    frequencies: Counter[str],
    document_frequency: dict[str, int],
    document_count: int,
    document_length: int,
    average_document_length: float,
) -> float:
    if not question_tokens or document_count <= 0 or document_length <= 0 or average_document_length <= 0:
        return 0.0

    k1 = 1.45
    b = 0.72
    score = 0.0
    for token in set(question_tokens):
        tf = frequencies.get(token, 0)
        if tf <= 0:
            continue
        df = document_frequency.get(token, 0)
        idf = math.log(1 + (document_count - df + 0.5) / (df + 0.5))
        denominator = tf + k1 * (1 - b + b * document_length / average_document_length)
        score += idf * (tf * (k1 + 1) / denominator)
    return score


def _score_document(
    question: str,
    question_tokens: list[str],
    document: TextDocument,
    index: TextIndex,
    document_index: int,
) -> float:
    question_lower = question.lower()
    score = _bm25_score(
        question_tokens=question_tokens,
        frequencies=index.term_frequencies[document_index],
        document_frequency=index.document_frequencies,
        document_count=len(index.documents),
        document_length=index.document_lengths[document_index],
        average_document_length=index.average_document_length,
    )

    for alias in document.aliases:
        if alias and alias.lower() in question_lower:
            score += 12.0

    if document.kind == "hextech" and any(word in question for word in ("海克斯", "强化", "棱彩", "黄金", "白银")):
        score += 1.2
    if document.kind == "champion" and any(word in question for word in ("英雄", "出装", "玩法", "适合谁")):
        score += 1.2

    return score


def search_text_documents(question: str, k: int = 8) -> tuple[list[str], list[str]]:
    index = load_text_index()
    question_tokens = _tokens(question)
    scored = [
        (_score_document(question, question_tokens, document, index, document_index), document)
        for document_index, document in enumerate(index.documents)
    ]
    ranked = [item for item in sorted(scored, key=lambda item: item[0], reverse=True) if item[0] > 0]

    if not ranked:
        return [], []

    selected = [document for _, document in ranked[:k]]
    return [document.content for document in selected], sorted({document.source for document in selected})
