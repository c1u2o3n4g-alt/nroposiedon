import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
STATUSES = {"active", "suspended", "maintenance", "expired"}


def fail(message):
    raise RuntimeError(message)


def parse_time(value, field):
    if not value:
        fail(f"Missing {field}")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        fail(f"Invalid {field}: {exc}")


def main():
    path = PUBLIC / "control" / "runtime.json"
    with path.open("r", encoding="utf-8") as handle:
        runtime = json.load(handle)

    if runtime.get("schemaVersion") != 1:
        fail("Unsupported runtime schemaVersion")
    try:
        uuid.UUID(runtime.get("modId", ""))
    except ValueError:
        fail("Invalid runtime modId")
    if not runtime.get("companyName"):
        fail("Missing runtime companyName")
    if runtime.get("status") not in STATUSES:
        fail("Invalid runtime status")
    parse_time(runtime.get("expiresAt"), "expiresAt")
    parse_time(runtime.get("graceUntil"), "graceUntil")
    parse_time(runtime.get("updatedAt"), "updatedAt")
    if int(runtime.get("revision", 0)) <= 0:
        fail("Invalid runtime revision")
    print("WebGL control validation passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
