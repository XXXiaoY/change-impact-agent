"""
Change Impact Analysis Agent - Main entry point.

Usage:
    python -m src.main --diff path/to/diff.patch --repo path/to/repo
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Change Impact Analysis Agent")
    parser.add_argument("--diff", required=True, help="Path to unified diff / patch file")
    parser.add_argument("--repo", default="./demo_repo", help="Path to the repository to analyze")
    args = parser.parse_args()

    # Read diff
    try:
        with open(args.diff, "r") as f:
            diff_text = f.read()
    except FileNotFoundError:
        print(f"Error: diff file not found: {args.diff}")
        sys.exit(1)

    print(f"Analyzing diff: {args.diff}")
    print(f"Repository: {args.repo}")
    print("---")

    # TODO: Initialize RAG engine
    # TODO: Run LangGraph workflow
    # TODO: Print report

    print("Agent workflow not yet implemented. Skeleton is ready.")


if __name__ == "__main__":
    main()
