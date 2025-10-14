#!/usr/bin/env python3
"""Wait for MongoDB to become available."""

import sys
import time
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
TIMEOUT_MS = 2000
RETRIES = 10


def main() -> int:
    for attempt in range(1, RETRIES + 1):
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=TIMEOUT_MS)
            client.server_info()
            print("✅ MongoDB reachable")
            return 0
        except Exception as exc:
            if attempt == RETRIES:
                print(f"❌ MongoDB not reachable: {exc}")
                return 1
            time.sleep(1)
    return 1


if __name__ == "__main__":
    sys.exit(main())
