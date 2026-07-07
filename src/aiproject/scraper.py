from __future__ import annotations

from dataclasses import dataclass
import html as html_lib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from time import sleep
from urllib.parse import urljoin, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from curl_cffi import requests as curl_requests
except ImportError:  # pragma: no cover - optional fallback
    curl_requests = None

BASE_URL = "https://apexlol.info"
CHAMPIONS_INDEX_URL = f"{BASE_URL}/zh/champions"
HEXTECH_INDEX_URL = f"{BASE_URL}/zh/hextech"


@dataclass(frozen=True)
class ChampionPage:
    name: str
    url: str
    text: str


@dataclass(frozen=True)
class HextechPage:
    hextech_id: str
    name: str
    tier: str
    url: str
    description: str
    text: str


class ChampionLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return

        attrs_map = dict(attrs)
        href = attrs_map.get("href")
        if not href:
            return

        path = urlparse(urljoin(BASE_URL, href)).path.strip("/")
        if path.startswith("zh/champions/") and path != "zh/champions":
            self.links.add(urljoin(BASE_URL, href))


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text and not self._skip_depth:
            self._chunks.append(text)

    @property
    def text(self) -> str:
        return "\n".join(self._chunks)


def fetch_html(url: str, timeout: int = 30) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Referer": BASE_URL,
    }
    cookie = os.getenv("APEXLOL_COOKIE")
    if cookie:
        headers["Cookie"] = cookie

    if curl_requests is not None:
        try:
            response = curl_requests.get(
                url,
                headers=headers,
                timeout=timeout,
                impersonate="chrome",
            )
            if response.status_code == 403:
                raise RuntimeError(
                    f"访问被站点拒绝：{url}。"
                    "当前 Cookie 可能已失效，或 Cloudflare 要求同一浏览器/IP 指纹。"
                )
            response.raise_for_status()
            response.encoding = response.encoding or "utf-8"
            return response.text
        except Exception as exc:
            if isinstance(exc, RuntimeError):
                raise
            raise RuntimeError(f"抓取失败：{url}，网络错误：{exc}") from exc

    request = Request(
        url,
        headers=headers,
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except HTTPError as exc:
        if exc.code == 403:
            raise RuntimeError(
                f"访问被站点拒绝：{url}。"
                "可以稍后重试，或改用浏览器导出的页面内容/允许访问的镜像数据源。"
            ) from exc
        raise RuntimeError(f"抓取失败：{url}，HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"抓取失败：{url}，网络错误：{exc.reason}") from exc


def discover_champion_urls(index_url: str = CHAMPIONS_INDEX_URL) -> list[str]:
    parser = ChampionLinkParser()
    parser.feed(fetch_html(index_url))
    urls = sorted(parser.links)
    if not urls:
        raise RuntimeError(f"没有从目录页发现英雄链接：{index_url}")
    return urls


def champion_url(name: str) -> str:
    return f"{CHAMPIONS_INDEX_URL}/{name.strip()}"


def hextech_url(hextech_id: str) -> str:
    return f"{HEXTECH_INDEX_URL}/{hextech_id.strip()}"


def parse_page_text(html: str) -> str:
    parser = TextParser()
    parser.feed(html)
    return parser.text


def scrape_champion_pages(
    champion_names: list[str] | None = None,
    delay_seconds: float = 0.5,
    limit: int | None = None,
) -> list[ChampionPage]:
    urls = [champion_url(name) for name in champion_names] if champion_names else discover_champion_urls()
    if limit is not None:
        urls = urls[:limit]

    pages: list[ChampionPage] = []
    for url in urls:
        html = fetch_html(url)
        text = parse_page_text(html)
        name = url.rstrip("/").split("/")[-1]
        pages.append(ChampionPage(name=name, url=url, text=text))
        sleep(delay_seconds)

    return pages


def load_champion_pages_from_html_dir(html_dir: str) -> list[ChampionPage]:
    root = Path(html_dir)
    if not root.exists():
        raise RuntimeError(f"HTML 目录不存在：{html_dir}")

    pages: list[ChampionPage] = []
    for path in sorted(root.glob("*.html")):
        html = path.read_text(encoding="utf-8", errors="replace")
        text = parse_page_text(html)
        pages.append(
            ChampionPage(
                name=path.stem,
                url=f"local://{path.name}",
                text=text,
            )
        )

    if not pages:
        raise RuntimeError(f"HTML 目录里没有 .html 文件：{html_dir}")

    return pages


def load_champion_pages_from_index_html(index_html: str) -> list[ChampionPage]:
    path = Path(index_html)
    if not path.exists():
        raise RuntimeError(f"目录页 HTML 不存在：{index_html}")

    html = path.read_text(encoding="utf-8", errors="replace")
    normalized = html.replace('\\"', '"')
    pattern = re.compile(
        r'\{"id":"[^"]+","name":"[^"]*","title":"[^"]*",'
        r'"roles":\[[^\]]*\],"image":"[^"]*","bestRating":"[^"]*",'
        r'"interactionCount":\d+\}'
    )

    pages: list[ChampionPage] = []
    seen: set[str] = set()
    for match in pattern.finditer(normalized):
        data = json.loads(match.group(0))
        champion_id = data["id"]
        if champion_id in seen:
            continue
        seen.add(champion_id)

        roles = "、".join(data.get("roles", [])) or "未知"
        url = champion_url(champion_id)
        text = "\n".join(
            [
                f"英雄ID：{champion_id}",
                f"中文称号：{data.get('name', '')}",
                f"英雄名称：{data.get('title', '')}",
                f"定位：{roles}",
                f"目录评级：{data.get('bestRating', '-')}",
                f"互动数量：{data.get('interactionCount', 0)}",
                f"详情页：{url}",
            ]
        )
        pages.append(ChampionPage(name=champion_id, url=url, text=text))

    if not pages:
        raise RuntimeError(f"没有从目录页 HTML 提取到英雄数据：{index_html}")

    return pages


def load_hextech_pages_from_index_html(index_html: str) -> list[HextechPage]:
    path = Path(index_html)
    if not path.exists():
        raise RuntimeError(f"海克斯目录页 HTML 不存在：{index_html}")

    html = path.read_text(encoding="utf-8", errors="replace")
    normalized = html.replace('\\"', '"')
    card_pattern = re.compile(
        r'<a class="[^"]*?" href="https://apexlol\.info/zh/hextech/(?P<id>\d+)"[^>]*>'
        r'.*?<span[^>]*>(?P<tier>[^<]+)</span>'
        r'<h3[^>]*>(?P<name>[^<]+)</h3>'
        r'<p[^>]*>(?P<description>.*?)</p>',
        re.S,
    )

    pages: list[HextechPage] = []
    seen: set[str] = set()
    for match in card_pattern.finditer(normalized):
        hextech_id = match.group("id")
        if hextech_id in seen:
            continue
        seen.add(hextech_id)

        name = html_lib.unescape(match.group("name")).strip()
        tier = html_lib.unescape(match.group("tier")).strip()
        description = html_lib.unescape(re.sub(r"<[^>]+>", "", match.group("description"))).strip()
        url = hextech_url(hextech_id)
        text = "\n".join(
            [
                f"海克斯ID：{hextech_id}",
                f"中文名：{name}",
                f"评级：{tier}",
                f"描述：{description}",
                f"详情页：{url}",
            ]
        )
        pages.append(
            HextechPage(
                hextech_id=hextech_id,
                name=name,
                tier=tier,
                url=url,
                description=description,
                text=text,
            )
        )

    if not pages:
        raise RuntimeError(f"没有从海克斯目录页 HTML 提取到数据：{index_html}")

    return pages


def load_hextech_pages_from_html_dir(index_html: str, html_dir: str) -> list[HextechPage]:
    catalog_pages = load_hextech_pages_from_index_html(index_html)
    catalog = {page.hextech_id: page for page in catalog_pages}
    root = Path(html_dir)
    if not root.exists():
        raise RuntimeError(f"海克斯 HTML 目录不存在：{html_dir}")

    pages: list[HextechPage] = []
    for path in sorted(root.glob("*.html")):
        catalog_page = catalog.get(path.stem)
        if catalog_page is None:
            continue

        html = path.read_text(encoding="utf-8", errors="replace")
        page_text = parse_page_text(html)
        text = "\n".join(
            [
                f"海克斯ID：{catalog_page.hextech_id}",
                f"中文名：{catalog_page.name}",
                f"评级：{catalog_page.tier}",
                f"目录描述：{catalog_page.description}",
                f"详情页：{catalog_page.url}",
                "",
                "详情正文：",
                page_text,
            ]
        )
        pages.append(
            HextechPage(
                hextech_id=catalog_page.hextech_id,
                name=catalog_page.name,
                tier=catalog_page.tier,
                url=catalog_page.url,
                description=catalog_page.description,
                text=text,
            )
        )

    if not pages:
        raise RuntimeError(f"海克斯 HTML 目录里没有可匹配目录的 .html 文件：{html_dir}")

    return pages


def download_champion_htmls_from_index(
    index_html: str,
    output_dir: str = "data/html/champions",
    delay_seconds: float = 0.5,
    limit: int | None = None,
) -> int:
    pages = load_champion_pages_from_index_html(index_html)
    if limit is not None:
        pages = pages[:limit]

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    count = 0
    for page in pages:
        target = root / f"{page.name}.html"
        if target.exists():
            print(f"skip existing {page.name} -> {target}")
            continue

        html = fetch_html(page.url)
        target.write_text(html, encoding="utf-8", errors="replace")
        count += 1
        print(f"[{count}/{len(pages)}] saved {page.name} -> {target}")
        sleep(delay_seconds)

    return count


def download_hextech_htmls_from_index(
    index_html: str,
    output_dir: str = "data/html/hextech",
    delay_seconds: float = 0.35,
    limit: int | None = None,
) -> int:
    pages = load_hextech_pages_from_index_html(index_html)
    if limit is not None:
        pages = pages[:limit]

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    count = 0
    for page in pages:
        target = root / f"{page.hextech_id}.html"
        if target.exists():
            print(f"skip existing {page.hextech_id} -> {target}")
            continue

        html = fetch_html(page.url)
        target.write_text(html, encoding="utf-8", errors="replace")
        count += 1
        print(f"[{count}/{len(pages)}] saved {page.hextech_id} {page.name} -> {target}")
        sleep(delay_seconds)

    return count
