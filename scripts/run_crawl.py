import argparse

import scripts.fetch_detail as fetch_detail
import list_crawler
import parse_html


def main():
    parser = argparse.ArgumentParser(description="CLI crawl dữ liệu luật")
    parser.add_argument("command", choices=["list", "detail", "parse", "all"])

    args = parser.parse_args()

    if args.command == "list":
        list_crawler.main()
        print("List xong")
    elif args.command == "detail":
        fetch_detail.main()
        print("Fetch xong")
    elif args.command == "parse":
        parse_html.main()
        print("Parse xong")
    elif args.command == "all":
        list_crawler.main()
        fetch_detail.main()
        parse_html.main()
        print("Hoàn thành")


if __name__ == "__main__":
    main()
