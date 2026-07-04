"""Simple load-test harness for the reconciliation engine."""

import random
import sys
from typing import List

from reconciliation_engine import evaluate_transaction


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    seen = set()
    for index in range(count):
        event = {
            "TransID": f"LOAD-{index}",
            "TransAmount": str(100 + random.randint(0, 10)),
            "MSISDN": f"2547000000{index % 10}",
            "TransTime": "20240601120000",
            "BusinessShortCode": "12345",
        }
        internal_record = {
            "internal_ref": f"ORD-{index}",
            "amount": 100.0 + (index % 5),
            "phone_number": f"2547000000{index % 10}",
            "timestamp": "2024-06-01T12:00:00Z",
            "status": "pending",
        }
        evaluate_transaction(event, [internal_record], seen, window_minutes=15)
        seen.add(event["TransID"])
    print(f"Processed {count} events")


if __name__ == "__main__":
    main()
