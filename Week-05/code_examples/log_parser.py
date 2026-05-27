#!/usr/bin/env python3
"""Extract lines containing a pattern from log files."""
import re
import sys


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <logfile> <pattern>")
        sys.exit(1)
    path, pattern = sys.argv[1], sys.argv[2]
    rx = re.compile(pattern)
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if rx.search(line):
                print(line.rstrip())


if __name__ == "__main__":
    main()
