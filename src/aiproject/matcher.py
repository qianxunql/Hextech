from __future__ import annotations

from dataclasses import dataclass
import re

from rapidfuzz import fuzz, process


_NOISE_RE = re.compile(r"[\s\W_]+", re.UNICODE)


@dataclass(frozen=True)
class MatchResult:
    id: str
    name: str
    tier: str
    description: str
    score: float
    source_text: str


def normalize_name(value: str) -> str:
    return _NOISE_RE.sub("", value).lower()


def compact_alias(value: str) -> str:
    compact = normalize_name(value)
    for token in ("你的", "他们", "它们", "这个", "那个", "之", "的", "出"):
        compact = compact.replace(token, "")
    if len(compact) >= 3:
        return f"{compact[0]}{compact[-1]}"
    return compact


def match_hextech_names(
    raw_text: str,
    catalog: list[dict[str, str]],
    *,
    limit: int = 4,
    threshold: float = 78.0,
) -> list[MatchResult]:
    candidates = [item for item in catalog if item.get("name")]
    if not raw_text.strip() or not candidates:
        return []

    normalized_text = normalize_name(raw_text)
    choice_to_item: dict[str, dict[str, str]] = {}
    for item in candidates:
        name = item["name"]
        choice_to_item[name] = item
        alias = compact_alias(name)
        if len(alias) >= 2:
            choice_to_item.setdefault(alias, item)
    results: dict[str, MatchResult] = {}

    for item in candidates:
        name = item["name"]
        normalized_name = normalize_name(name)
        if normalized_name and normalized_name in normalized_text:
            results[item["id"]] = MatchResult(
                id=item["id"],
                name=name,
                tier=item.get("tier", ""),
                description=item.get("description", ""),
                score=100.0,
                source_text=name,
            )

    text_parts = [
        part.strip()
        for part in re.split(r"[\r\n,，。:：;；|/\\]+", raw_text)
        if len(normalize_name(part)) >= 2
    ]
    if not text_parts:
        text_parts = [raw_text]

    choices = list(choice_to_item.keys())
    for part in text_parts:
        normalized_part = normalize_name(part)
        for name, score, _ in process.extract(normalized_part, choices, scorer=fuzz.WRatio, limit=3):
            if score < threshold:
                continue
            item = choice_to_item[name]
            current = results.get(item["id"])
            if current is None or score > current.score:
                results[item["id"]] = MatchResult(
                    id=item["id"],
                    name=item["name"],
                    tier=item.get("tier", ""),
                    description=item.get("description", ""),
                    score=float(score),
                    source_text=part,
                )

    return sorted(results.values(), key=lambda item: item.score, reverse=True)[:limit]


def build_hextech_choice_question(champion: str, matches: list[MatchResult]) -> str:
    champion_part = champion.strip() or "当前英雄未知"
    choices = "、".join(match.name for match in matches)
    if not choices:
        choices = "未能可靠识别，请根据截图 OCR 文本判断"
    return (
        f"当前英雄：{champion_part}\n"
        f"当前可选海克斯强化：{choices}\n"
        "请基于知识库给出本轮最优选择排序，并简洁说明每个选择适合原因、收益条件和需要避开的情况。"
    )
