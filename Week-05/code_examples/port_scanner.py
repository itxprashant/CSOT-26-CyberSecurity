#!/usr/bin/env python3
"""Simple TCP port scanner for authorized lab targets only."""
import socket
import sys


def scan(host: str, port: int, timeout: float = 0.5) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def parse_ports(spec: str) -> list[int]:
    ports = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            ports.extend(range(int(a), int(b) + 1))
        else:
            ports.append(int(part))
    return ports


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <host> <ports>")
        print(f"Example: {sys.argv[0]} 127.0.0.1 22,80,443")
        sys.exit(1)
    host = sys.argv[1]
    ports = parse_ports(sys.argv[2])
    for p in ports:
        if scan(host, p):
            print(f"{p}/tcp open")


if __name__ == "__main__":
    main()
