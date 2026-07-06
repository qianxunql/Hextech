import argparse

from langchain_core.messages import HumanMessage

from aiproject.graph import graph
from aiproject.scraper import (
    load_champion_pages_from_html_dir,
    load_champion_pages_from_index_html,
    scrape_champion_pages,
)
from aiproject.vectorstore import ingest_pages


def run(question: str) -> str:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="英雄联盟海克斯大乱斗助手")
    subparsers = parser.add_subparsers(dest="command")

    ingest_parser = subparsers.add_parser("ingest", help="抓取英雄页面并写入本地知识库")
    ingest_parser.add_argument("--champion", action="append", dest="champions", help="只抓取指定英雄 URL 名，可重复传入")
    ingest_parser.add_argument("--limit", type=int, help="限制抓取数量，调试时很有用")
    ingest_parser.add_argument("--index-html", help="从浏览器另存为的英雄目录页 HTML 导入")
    ingest_parser.add_argument("--html-dir", help="从浏览器另存为的本地 HTML 目录导入")

    ask_parser = subparsers.add_parser("ask", help="基于知识库提问")
    ask_parser.add_argument("question", help="要问助手的问题")

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

    if args.command == "ask":
        print(run(args.question))
        return

    if args.legacy_question:
        print(run(args.legacy_question))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
