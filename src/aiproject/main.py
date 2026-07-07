import argparse

from langchain_core.messages import HumanMessage

from aiproject.config import settings_override
from aiproject.graph import graph
from aiproject.scraper import (
    download_champion_htmls_from_index,
    download_hextech_htmls_from_index,
    load_champion_pages_from_html_dir,
    load_champion_pages_from_index_html,
    load_hextech_pages_from_html_dir,
    scrape_champion_pages,
)
from aiproject.vectorstore import ingest_pages


def run(question: str, overrides: dict | None = None) -> str:
    with settings_override(**(overrides or {})):
        result = graph.invoke({"messages": [HumanMessage(content=question)]})
    answer = result["messages"][-1].content
    sources = result.get("sources", [])
    if sources:
        answer = f"{answer}\n\n资料来源：\n" + "\n".join(f"- {source}" for source in sources)
    return answer


def ingest(
    champions: list[str] | None = None,
    limit: int | None = None,
    html_dir: str | None = None,
    index_html: str | None = None,
) -> None:
    if index_html:
        pages = load_champion_pages_from_index_html(index_html)
    elif html_dir:
        pages = load_champion_pages_from_html_dir(html_dir)
    else:
        pages = scrape_champion_pages(champion_names=champions, limit=limit)

    if limit is not None:
        pages = pages[:limit]

    chunk_count = ingest_pages(pages)
    print(f"已抓取 {len(pages)} 个英雄页面，写入 {chunk_count} 个知识片段。")


def ingest_hextech(index_html: str, html_dir: str, limit: int | None = None) -> None:
    pages = load_hextech_pages_from_html_dir(index_html=index_html, html_dir=html_dir)

    if limit is not None:
        pages = pages[:limit]

    chunk_count = ingest_pages(pages)
    print(f"已导入 {len(pages)} 个海克斯详情页，写入 {chunk_count} 个知识片段。")


def download(index_html: str, output_dir: str, limit: int | None = None) -> None:
    count = download_champion_htmls_from_index(
        index_html=index_html,
        output_dir=output_dir,
        limit=limit,
    )
    print(f"已下载 {count} 个英雄详情页到 {output_dir}。")


def download_hextech(index_html: str, output_dir: str, limit: int | None = None) -> None:
    count = download_hextech_htmls_from_index(
        index_html=index_html,
        output_dir=output_dir,
        limit=limit,
    )
    print(f"已下载 {count} 个海克斯详情页到 {output_dir}。")


def main() -> None:
    parser = argparse.ArgumentParser(description="英雄联盟海克斯大乱斗助手")
    subparsers = parser.add_subparsers(dest="command")

    ingest_parser = subparsers.add_parser("ingest", help="抓取英雄页面并写入本地知识库")
    ingest_parser.add_argument("--champion", action="append", dest="champions", help="只抓取指定英雄 URL 名，可重复传入")
    ingest_parser.add_argument("--limit", type=int, help="限制抓取数量，调试时很有用")
    ingest_parser.add_argument("--index-html", help="从浏览器另存为的英雄目录页 HTML 导入")
    ingest_parser.add_argument("--html-dir", help="从浏览器另存为的本地 HTML 目录导入")

    ingest_hextech_parser = subparsers.add_parser("ingest-hextech", help="把本地海克斯详情页写入知识库")
    ingest_hextech_parser.add_argument(
        "--index-html",
        default="海克斯强化列表 _ ARAM Hextech Wiki.html",
        help="海克斯目录页 HTML",
    )
    ingest_hextech_parser.add_argument("--html-dir", default="data/html/hextech", help="本地海克斯详情页 HTML 目录")
    ingest_hextech_parser.add_argument("--limit", type=int, help="限制导入数量，调试时很有用")

    ask_parser = subparsers.add_parser("ask", help="基于知识库提问")
    ask_parser.add_argument("question", help="要问助手的问题")

    download_parser = subparsers.add_parser("download", help="从英雄目录页批量下载英雄详情页 HTML")
    download_parser.add_argument("--index-html", default="data/html/champions_index.html", help="英雄目录页 HTML")
    download_parser.add_argument("--output-dir", default="data/html/champions", help="保存英雄详情页 HTML 的目录")
    download_parser.add_argument("--limit", type=int, help="限制下载数量，调试时很有用")

    download_hextech_parser = subparsers.add_parser("download-hextech", help="从海克斯目录页批量下载详情页 HTML")
    download_hextech_parser.add_argument(
        "--index-html",
        default="海克斯强化列表 _ ARAM Hextech Wiki.html",
        help="海克斯目录页 HTML",
    )
    download_hextech_parser.add_argument("--output-dir", default="data/html/hextech", help="保存海克斯详情页 HTML 的目录")
    download_hextech_parser.add_argument("--limit", type=int, help="限制下载数量，调试时很有用")

    parser.add_argument("legacy_question", nargs="?", help="兼容旧用法：直接传问题")
    args = parser.parse_args()

    if args.command == "ingest":
        ingest(
            champions=args.champions,
            limit=args.limit,
            html_dir=args.html_dir,
            index_html=args.index_html,
        )
        return

    if args.command == "ingest-hextech":
        ingest_hextech(
            index_html=args.index_html,
            html_dir=args.html_dir,
            limit=args.limit,
        )
        return

    if args.command == "ask":
        print(run(args.question))
        return

    if args.command == "download":
        download(
            index_html=args.index_html,
            output_dir=args.output_dir,
            limit=args.limit,
        )
        return

    if args.command == "download-hextech":
        download_hextech(
            index_html=args.index_html,
            output_dir=args.output_dir,
            limit=args.limit,
        )
        return

    if args.legacy_question:
        print(run(args.legacy_question))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
