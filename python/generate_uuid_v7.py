#!/usr/bin/env python3

import argparse
import secrets
import sys
import time
import uuid

# ANSI escape codes
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def generate_uuid7() -> uuid.UUID:
    """
    Generate a UUID version 7 identifier according to RFC 9562.

    Layout:
      - 48 bits: Unix timestamp in milliseconds
      - 4 bits: version 7
      - 12 bits: random data
      - 2 bits: RFC 4122 variant
      - 62 bits: random data
    """
    timestamp_ms = int(time.time() * 1000) & ((1 << 48) - 1)

    random_a = secrets.randbits(12)
    random_b = secrets.randbits(62)

    uuid_int = (
        (timestamp_ms << 80)
        | (0x7 << 76)
        | (random_a << 64)
        | (0x2 << 62)
        | random_b
    )

    return uuid.UUID(int=uuid_int)


def print_message(message: str, color: str, use_color: bool) -> None:
    if use_color:
        print(f"{color}{message}{RESET}")
    else:
        print(message)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate UUID version 7 identifiers.",
        epilog="Example: ./uuid7gen.py -n 5",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "-n",
        "--number",
        type=int,
        default=1,
        help="Number of UUIDv7 identifiers to generate. Default: 1",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output.",
    )

    parser.add_argument(
        "--plain",
        action="store_true",
        help="Print only UUIDs, without extra messages.",
    )

    args = parser.parse_args()

    count = args.number
    use_color = not args.no_color

    if count < 1:
        print_message("Error: The number of UUIDs must be at least 1.", RED, use_color)
        sys.exit(1)

    if not args.plain:
        print_message(
            f"\nGenerating {count} UUIDv7 identifier{'s' if count > 1 else ''}:\n",
            GREEN,
            use_color,
        )

    for _ in range(count):
        print(generate_uuid7())

    if not args.plain:
        print_message(
            f"\nDone. {count} UUIDv7 identifier{'s' if count > 1 else ''} generated.\n",
            GREEN,
            use_color,
        )


if __name__ == "__main__":
    main()