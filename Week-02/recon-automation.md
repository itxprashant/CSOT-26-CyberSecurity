# Recon automation

By the end of this week you have a pile of useful commands: `nmap`, `dig`, `whois`, `curl`, `nc`, `ffuf`, and friends. Running them one at a time on a single host is fine for learning. The moment you face a real engagement — even a CTF box list of five targets — running them by hand becomes a slow, error-prone slog where you lose findings in your terminal scrollback.

Automation fixes three problems at once: **speed** (parallel commands), **completeness** (you can't forget a step that's in a script), and **reproducibility** (the same target produces the same artifact, every time).

This module covers the patterns: how to script bash and Python recon pipelines, parse structured tool output, organize artifacts, and stay on the right side of "automated but ethical."

---

## What good recon automation looks like

A useful workflow is small, layered, and writes everything to disk:

```
input  : target (IP / domain / CIDR)
        ↓
stage 1: discovery     → who's alive
        ↓
stage 2: enumeration   → which ports / services / records
        ↓
stage 3: fingerprinting → versions, banners, titles
        ↓
stage 4: reporting     → human-readable summary + machine-readable evidence
```

Each stage **reads from disk and writes to disk**. That way:

- A failure in one stage doesn't lose the previous stages' work.
- You can rerun a single stage with different flags.
- You can diff today's results against yesterday's to spot changes.

A useful directory layout per run:

```
recon_example.com_2025-05-27/
├── 00-meta.txt            target, time, command line, operator
├── 01-dns/
│   ├── ns.txt   soa.txt   a.txt   txt.txt   mx.txt
│   ├── whois.txt
│   └── subdomains.txt
├── 02-nmap/
│   ├── quick.nmap   quick.xml   quick.gnmap
│   ├── full.nmap    full.xml
│   └── udp.nmap
├── 03-http/
│   ├── 8080-headers.txt   8080-index.html
│   └── 8080-screenshot.png
├── 04-banners/
│   └── 9001.txt
└── report.md              the actual write-up
```

You'll be glad you did this the first time you need to revisit a target six weeks later.

---

## Bash patterns — the building blocks

Bash is the right choice for "stitch tools together." Use it until your logic gets complicated enough that a real language helps.

### A first script — discovery + scan + DNS

```bash
#!/usr/bin/env bash
# recon.sh — minimal multi-stage recon pipeline
# Usage: ./recon.sh <target>

set -euo pipefail                      # fail fast on errors / unset vars / pipe failures

TARGET="${1:?Usage: $0 <target>}"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
OUT="recon_${TARGET}_${STAMP}"

mkdir -p "$OUT"/{dns,nmap,http}

# --- 00 meta ---
cat > "$OUT/00-meta.txt" <<EOF
target:    $TARGET
operator:  $(whoami)@$(hostname)
started:   $(date -Iseconds)
cmdline:   $0 $*
EOF

# --- 01 DNS ---
echo "[+] DNS"
for t in A AAAA NS MX TXT CAA SOA; do
  dig "$t" "$TARGET" +short > "$OUT/dns/$t.txt" || true
done
whois "$TARGET" > "$OUT/dns/whois.txt" 2>&1 || true

# --- 02 Nmap quick + full ---
echo "[+] Nmap quick (top 1000)"
nmap -sV -sC -T4 -oA "$OUT/nmap/quick" "$TARGET" >/dev/null

echo "[+] Nmap full (-p-)"
nmap -p- -T4 -oA "$OUT/nmap/full" "$TARGET" >/dev/null

# --- 03 HTTP banner per discovered web port ---
echo "[+] HTTP banners"
grep -oE '^[0-9]+/tcp.*open.*http' "$OUT/nmap/quick.nmap" \
  | awk '{print $1}' | cut -d/ -f1 \
  | while read -r port; do
      curl -sI "http://$TARGET:$port/" \
        > "$OUT/http/$port-headers.txt" || true
  done

echo "[+] Done. Artifacts in $OUT/"
```

Two patterns worth copying:

1. **`set -euo pipefail`** at the top of every script you write. It turns silent failures into loud ones.
2. **One target per output directory, timestamped.** Never overwrite previous runs.

### Iterating over a target list

```bash
#!/usr/bin/env bash
while IFS= read -r target; do
  [[ -z "$target" || "$target" =~ ^# ]] && continue   # skip blanks/comments
  echo "=== $target ==="
  ./recon.sh "$target"
done < targets.txt
```

Combined with GNU `parallel` when you trust the targets and want concurrency:

```bash
parallel -j 4 ./recon.sh :::: targets.txt
```

### Trapping interruptions cleanly

```bash
cleanup() { echo "[!] interrupted, partial output in $OUT"; }
trap cleanup INT TERM
```

So Ctrl-C still leaves you a directory you can resume from.

---

## Parsing nmap output

`nmap` has three text formats. Pick the one that fits the consumer:

| Format | Best for |
|--------|----------|
| `-oN file.nmap` | Humans reading the file directly |
| `-oG file.gnmap` | One line per host — easy to `grep` / `awk` |
| `-oX file.xml` | Programs — robust structure, what you should use in Python |

### Quick grep on `-oG`

```bash
nmap -p- --open -oG - target | awk '/Ports:/ {print $2, $0}'
```

Or extract `host:port` pairs ready for the next stage:

```bash
awk '/Ports:/ {
  ip=$2;
  for (i=4; i<=NF; i++) if ($i ~ /\//) {
    split($i, a, "/");
    if (a[2] == "open") print ip ":" a[1]
  }
}' nmap.gnmap
```

### Parsing `-oX` in Python

Robust, structured, what you want for any report:

```python
#!/usr/bin/env python3
"""parse-nmap.py — extract open ports + services from nmap XML."""

import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    sys.exit("Usage: parse-nmap.py <nmap.xml>")

tree = ET.parse(sys.argv[1])
for host in tree.findall("host"):
    addr = host.find("address").get("addr")
    for port in host.findall(".//port"):
        state = port.find("state").get("state")
        if state != "open":
            continue
        portid = port.get("portid")
        proto = port.get("protocol")
        svc = port.find("service")
        name = svc.get("name", "?") if svc is not None else "?"
        product = svc.get("product", "") if svc is not None else ""
        version = svc.get("version", "") if svc is not None else ""
        print(f"{addr}\t{portid}/{proto}\t{name}\t{product} {version}".strip())
```

Run:

```bash
python3 parse-nmap.py recon_example.com_*/nmap/quick.xml
# 10.10.10.5  22/tcp  ssh   OpenSSH 8.9p1
# 10.10.10.5  80/tcp  http  nginx 1.18.0
```

---

## Parsing JSON tool output with `jq`

Many modern recon tools (subfinder, httpx, projectdiscovery's whole suite, custom scanners) emit JSON. `jq` is to JSON what `awk` is to columns — learn the basics once, use forever.

The Week 2 lab challenge [../../CTFs/week-02/parse-scan-json/](../../CTFs/week-02/parse-scan-json/) ships `scan.json` for practice. Its schema is:

```json
{
  "hosts": [
    {
      "ip": "10.10.10.5",
      "ports": [
        {"port": 22, "state": "open"},
        {"port": 80, "state": "open", "flag": "csot26{json_parsing_wins}"}
      ]
    }
  ]
}
```

Useful queries:

```bash
# All hosts
jq '.hosts[].ip' scan.json

# Open ports as ip:port pairs
jq -r '.hosts[] | .ip as $ip | .ports[] | select(.state=="open") | "\($ip):\(.port)"' scan.json

# Any port that carries a `flag` field
jq -r '.. | objects | select(has("flag")) | .flag' scan.json

# Filter and pretty-print
jq '.hosts[] | {ip: .ip, open_ports: [.ports[] | select(.state=="open") | .port]}' scan.json
```

The same patterns work for subfinder, httpx, nuclei, dnsx, and so on — they all emit one JSON object per line (NDJSON), and `jq` handles that with `--slurp`/`-c` flags as needed.

### Pythonic equivalent

```python
import json, pathlib
data = json.loads(pathlib.Path("scan.json").read_text())
for host in data["hosts"]:
    for port in host["ports"]:
        if port["state"] == "open":
            print(host["ip"], port["port"], port.get("flag", ""))
```

---

## Python patterns — when bash starts to hurt

Switch to Python when you need any of:

- Conditional logic more involved than "if/else".
- Concurrency you can reason about (`asyncio`, `concurrent.futures`).
- Structured data flowing between stages.
- Producing real reports (Markdown / HTML).

### Subprocess wrappers

```python
import subprocess
import shlex
from pathlib import Path

def run(cmd: str, cwd: Path | None = None, timeout: int = 60) -> str:
    """Run a shell command; capture stdout; raise on failure."""
    result = subprocess.run(
        shlex.split(cmd),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,                  # we want to inspect non-zero exits
    )
    if result.returncode != 0:
        print(f"[!] {cmd!r} exit={result.returncode} stderr={result.stderr[:200]}")
    return result.stdout
```

Avoid `shell=True`. It opens shell-injection risks the moment your input comes from anywhere untrusted (a file, a webhook, a user). `shlex.split` keeps you safe.

### Concurrent host scans

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def scan(host: str) -> tuple[str, str]:
    xml = run(f"nmap -sV -sC -oX - {host}", timeout=300)
    return host, xml

hosts = Path("targets.txt").read_text().splitlines()
with ThreadPoolExecutor(max_workers=4) as pool:
    futs = {pool.submit(scan, h): h for h in hosts}
    for fut in as_completed(futs):
        host, xml = fut.result()
        Path(f"out/{host}.xml").write_text(xml)
        print(f"[+] {host} done")
```

Four parallel scans, results saved per host, no scrollback chaos.

### Markdown report generation

```python
def render_report(parsed: list[dict], out: Path) -> None:
    lines = ["# Recon report\n"]
    for host in parsed:
        lines.append(f"## {host['ip']}\n")
        lines.append("| Port | Service | Version |")
        lines.append("|------|---------|---------|")
        for p in host["ports"]:
            lines.append(f"| {p['port']}/{p['proto']} | {p['name']} | {p['version']} |")
        lines.append("")
    out.write_text("\n".join(lines))
```

A two-page Markdown report — converted to PDF with `pandoc` — is what most real recon engagements deliver to clients.

---

## Idempotence, caching, and resumability

The single best habit when scripting recon: **make every stage cheap to rerun**.

- Always check whether the output file already exists before re-running an expensive command.
- Use timestamps in directory names so re-runs go somewhere new.
- For long pipelines, use `make` or `just` so unchanged stages aren't repeated.

A minimal `Makefile`:

```makefile
TARGET ?=

dns: dns/A.txt
dns/A.txt:
	@mkdir -p dns
	dig A  $(TARGET) +short > dns/A.txt
	dig MX $(TARGET) +short > dns/MX.txt
	dig TXT $(TARGET) +short > dns/TXT.txt

scan: scan/quick.xml
scan/quick.xml: dns
	@mkdir -p scan
	nmap -sV -sC -oA scan/quick $(TARGET)

report: scan
	@python3 ../parse-nmap.py scan/quick.xml > report.md

.PHONY: dns scan report
```

Run: `make TARGET=example.com report`. Make figures out what's stale and re-runs only that.

---

## Rate limiting and being a good network citizen

Automation amplifies whatever you do. A bad script hits a target 1000× harder than typing the same commands by hand.

- **Default to slow.** Start with low concurrency (`-T3`, `--max-rate 100`, `-j 4`) and only ramp up after confirming the target tolerates it.
- **Rate-limit third-party APIs.** crt.sh, Shodan, SecurityTrails all have request budgets. Hammer them and you get banned.
- **Set a meaningful User-Agent** when making HTTP requests:

  ```python
  headers = {"User-Agent": "csot-recon/1.0 (educational)"}
  ```

  This makes it easy for an admin to tell you to stop, which is friendlier than silent rate-limiting.
- **Respect `robots.txt`** when scraping. Tools like `gau` and `waybackurls` do this; custom code should too.
- **Watch retries.** A loop that retries on failure can hammer a flaky service into oblivion. Use exponential backoff.

---

## Ethics, again

This may sound repetitive — the rules are repetitive because they matter.

| Allowed | Not allowed |
|---------|-------------|
| Scripting recon against your own VMs / Docker labs | Scripting recon against your hostel, campus, or any non-consenting network |
| TryHackMe / HTB targets while on their VPN | Any TryHackMe-style scanning of internet hosts that weren't given to you |
| Passive OSINT (third-party APIs only) | Active enumeration of a domain you don't own |
| Self-OSINT — auditing your own footprint | Profiling a real classmate "as a joke" |
| Bug bounty scanning **only** within program scope | Scanning anything off-scope, even adjacent infra |

The IT Act §43 and §66 treat automated unauthorized scanning the same as manual unauthorized scanning. "It was a script" is not a defense.

---

## Putting it all together — the Week 2 assignment workflow

Use the lab in `../../CTFs/week-02/_infra/` as your authorized target and the patterns above to produce a one-page recon report:

```bash
# 1. Start the lab
cd CTFs/week-02/_infra
sudo docker compose up -d

# 2. Run your pipeline against 127.0.0.1 (everything binds to loopback)
cd ../../..
./recon.sh 127.0.0.1                      # the script from this module

# 3. Use parse-nmap.py to produce a Markdown summary
python3 parse-nmap.py recon_127.0.0.1_*/nmap/quick.xml > report.md

# 4. Solve at least one CTF challenge per stage:
#    - banner-guess     (uses the HTTP banner you captured)
#    - netcat-handshake (uses the TCP banner)
#    - scan-report      (parses an nmap text file)
#    - parse-scan-json  (parses JSON output)
```

Deliverables for the assignment:

1. The recon script(s) you wrote (`bash` and/or Python).
2. The output directory it produced (artifact tree).
3. A short Markdown report listing open ports, services, versions, and notes.
4. The flags from the four CTF challenges mentioned above.

---

## Further reading

- [ProjectDiscovery's suite](https://github.com/projectdiscovery) — `subfinder`, `httpx`, `nuclei`, `dnsx`. Read their READMEs; the JSON they emit is your input.
- [`nmap` book — output options](https://nmap.org/book/man-output.html) — official docs on `-oX`/`-oG`/`-oN`.
- [`jq` manual](https://stedolan.github.io/jq/manual/) — the only reference you'll need.
- [Pure Bash Bible](https://github.com/dylanaraps/pure-bash-bible) — string/array tricks without external commands.
- [HackTricks — Pentesting methodology](https://book.hacktricks.xyz/generic-methodologies-and-resources/pentesting-methodology) — checklist your scripts can encode.
- [GNU `parallel` tutorial](https://www.gnu.org/software/parallel/parallel_tutorial.html) — when you really do need 16 scans at once.

---

## Next week

[Week 3 — Web security](../Week-03/) — we move from "what's on the network" to "what's broken inside the web app." The recon artifacts you produced this week become the *input* to web-app enumeration: subdomains and HTTP ports turn into URLs to fuzz.
