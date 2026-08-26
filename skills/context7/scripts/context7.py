import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://context7.com/api/v2"


def fetch(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


def search_library(library: str, query: str):
    url = (
        f"{API}/libs/search?"
        f"libraryName={urllib.parse.quote(library)}&"
        f"query={urllib.parse.quote(query)}"
    )
    data = fetch(url).decode("utf-8")
    return json.loads(data)


def fetch_context(library_id: str, query: str, response_type: str = "txt"):
    url = (
        f"{API}/context?"
        f"libraryId={urllib.parse.quote(library_id)}&"
        f"query={urllib.parse.quote(query)}&"
        f"type={urllib.parse.quote(response_type)}"
    )
    return fetch(url).decode("utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Query Context7 library documentation."
    )
    parser.add_argument("library", help="Library name to search for")
    parser.add_argument("query", help="Topic to query")
    parser.add_argument(
        "--type",
        default="txt",
        choices=["txt", "json"],
        help="Response format for the context endpoint",
    )
    args = parser.parse_args(argv)

    try:
        search = search_library(args.library, args.query)
    except urllib.error.URLError as exc:
        print(f"Context7 search request failed: {exc}", file=sys.stderr)
        return 1

    results = search.get("results") or []
    if not results:
        print(f"No Context7 library found for '{args.library}'.", file=sys.stderr)
        return 1

    library_id = results[0].get("id")
    if not library_id:
        print("Search result missing library id.", file=sys.stderr)
        return 1

    try:
        context = fetch_context(library_id, args.query, args.type)
    except urllib.error.URLError as exc:
        print(f"Context7 context request failed: {exc}", file=sys.stderr)
        return 1

    print(context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
