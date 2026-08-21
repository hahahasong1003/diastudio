#!/usr/bin/env python3
"""Stop 훅 — 예약만 되고 확정되지 않은 변주값이 남았는지 확인한다.

예약만 쌓이고 확정되지 않으면 대장이 원고와 어긋나고,
어긋난 대장은 없느니만 못하다.

settings.json의 Stop에 건다.
"""

import json
import os
import sys

LEDGER = os.environ.get("BOOK_LEDGER", "ledger.json")


def main():
    if not os.path.exists(LEDGER):
        return 0
    try:
        with open(LEDGER, encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, OSError):
        return 0

    pending = [(field, e) for field, entries in (data.get("entries") or {}).items()
               for e in entries if e.get("state") == "reserved"]
    if not pending:
        return 0

    sys.stderr.write(
        f"변주 대장에 예약만 되고 확정되지 않은 값이 {len(pending)}건 남았다.\n"
        "원고에 실제로 쓴 값을 확정하거나, 버린 값은 해제한다.\n"
        "  python3 <suite>/series-variation-ledger/scripts/variation_ledger.py commit --chapter N\n"
        "  python3 <suite>/series-variation-ledger/scripts/variation_ledger.py release --chapter N\n\n")
    for field, e in pending[:10]:
        sys.stderr.write(f"  {e.get('chapter')}장  {field}  {e.get('value')}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
