#!/usr/bin/env python3
"""Bulk query utility for ProcessedTransaction records.

Usage:
  python scripts/admin_query.py trans_id1 trans_id2 ...
  python scripts/admin_query.py --file ids.txt

This script queries the local DB using `EventStore.get_processed()` so it does
not require the webserver or admin token.
"""
import argparse
import json
import sys
from pesaguard_backend_pipeline.event_store import EventStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trans_ids", nargs="*", help="One or more transaction IDs to query")
    parser.add_argument("--file", help="File with one trans_id per line")
    parser.add_argument("--db", help="Optional DATABASE_URL to use for EventStore")
    args = parser.parse_args()

    ids = list(args.trans_ids or [])
    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            ids.extend([line.strip() for line in fh if line.strip()])

    if not ids:
        print("No trans_ids supplied", file=sys.stderr)
        sys.exit(2)

    es = EventStore(database_url=args.db) if args.db else EventStore()

    out = {}
    for tid in ids:
        out[tid] = es.get_processed(tid)

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
