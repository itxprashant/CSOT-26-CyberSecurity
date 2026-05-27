# Digital forensics fundamentals

Forensics is the discipline of recovering, preserving, and analysing digital evidence. In a CTF it shows up as "here's a disk image, find the flag." In real life it shows up as "the breach happened sometime last week, find out what they took and how they got in." The toolkit is the same; the stakes differ.

This module covers the forensics workflow you'll use for the Week 4 CTF and the foundation you'll build on if you ever do real incident response: file carving, magic-byte analysis, log triage, packet capture inspection, memory and disk imaging, and the chain-of-custody habits that make findings legally defensible.

---

## Why this module matters

- **The Week 4 CTF leans heavily on forensics.** Half the challenges are "open this artifact, find the flag in it." Recognising the right tool for each kind of artifact wins time.
- **Forensics is half of incident response.** When something goes wrong in production, "what happened?" is answered by reading logs, packet captures, and disk artifacts. The skills you build here directly transfer.
- **It's where security work meets law.** A pentest report is internal. A forensics report is evidence — sometimes for HR, sometimes for a court. Handling it correctly matters.

---

## The forensics mindset

Three habits separate forensics from "just poking at files":

1. **Touch the original as little as possible.** Work on copies. Hash everything before and after. If you have to modify the original, document why.
2. **Document as you go.** Every command, every observation, every file you opened — note it. Future-you (and the auditor) will need the trail.
3. **Hypothesise, then verify.** Don't start typing tools. Form a theory ("the attacker uploaded a web shell"), then look for evidence that confirms or refutes it.

In a CTF you can be sloppier — there's a flag, you find it, you move on. But the muscle memory of "hash → copy → analyse" is what makes you employable.

---

## The evidence pyramid — what's in your typical artifact set

```
                       /\        Cloud / SaaS logs (Okta, GitHub, M365)
                      /  \
                     /----\      Network captures (PCAP, NetFlow, logs)
                    /      \
                   /--------\    Disk images (full disk, file system)
                  /          \
                 /------------\  Memory dumps (RAM acquisition)
                /              \
               /----------------\ Live system state (running processes, sockets)
```

Higher up = more durable, slower to change. Lower down = ephemeral but richest. In a real incident you collect from the most volatile to the most durable — RAM first because it disappears on reboot, then disk, then network/cloud logs which are usually already shipped to a SIEM.

---

## File-magic and signatures (carry-over from stego)

Forensics starts the same way stego does: identify what the file actually is.

| Format | Magic (hex) | Magic (ASCII) | Notes |
|--------|-------------|---------------|-------|
| PNG | `89 50 4E 47 0D 0A 1A 0A` | `.PNG....` | Lossless raster |
| JPEG | `FF D8 FF` | (binary) | Multiple variants (`E0`/`E1`/`DB`) |
| GIF | `47 49 46 38 [79\|37] 61` | `GIF89a` / `GIF87a` | Palette + animation |
| BMP | `42 4D` | `BM` | Uncompressed image |
| PDF | `25 50 44 46` | `%PDF` | Can embed JS / files |
| ZIP / DOCX / APK / JAR | `50 4B 03 04` | `PK..` | Same magic, format inside differs |
| RAR (v1.5+) | `52 61 72 21 1A 07 00` | `Rar!...` | |
| 7-Zip | `37 7A BC AF 27 1C` | `7z....` | |
| GZIP | `1F 8B` | (binary) | Often `.tar.gz` |
| TAR | (no magic; check `ustar` at offset 257) | | |
| ELF (Linux) | `7F 45 4C 46` | `.ELF` | |
| PE (Windows .exe/.dll) | `4D 5A` | `MZ` | |
| Mach-O (macOS) | `CF FA ED FE` / `FE ED FA CF` | (binary) | |
| Sqlite | `53 51 4C 69 74 65 20 66 6F 72 6D 61 74 20 33 00` | `SQLite format 3.` | |
| PCAP | `D4 C3 B2 A1` (LE) or `A1 B2 C3 D4` (BE) | (binary) | |
| PCAPNG | `0A 0D 0D 0A` | | Modern Wireshark default |
| MBR / boot sector | last 2 bytes `55 AA` at offset 510 | | |

```bash
file /tmp/unknown_artifact
xxd /tmp/unknown_artifact | head -2
```

If `file` says `data`, you're looking at something without a recognised header — could be raw data, could be encrypted, could be a custom format. Time to inspect the bytes yourself.

---

## File carving

**Carving** = pulling recognisable files out of a larger blob (disk image, memory dump, raw network capture) without relying on filesystem metadata. Works because every format starts with a known magic.

| Tool | Strengths |
|------|-----------|
| `foremost` | Classic; configurable signatures in `/etc/foremost.conf` |
| `scalpel` | Foremost fork, similar usage |
| `bulk_extractor` | Extracts emails, URLs, credit-card numbers, hashes, etc. |
| `photorec` | Part of `testdisk`; aggressive image/document recovery |
| `binwalk` | Best when the embedded files are signed by known magics |
| `strings` + manual carving | When the format isn't in any tool's signature DB |

### `foremost`

```bash
sudo apt install foremost

foremost -i disk.img -o carved/
# Processing: disk.img
# |*|

ls carved/
# audit.txt   jpg/   pdf/   png/   zip/   wav/
cat carved/audit.txt
# foremost version 1.5.7
# Foremost started at ...
# Input: disk.img
# Output: carved
# ...
# Finish: ...
# 17 FILES EXTRACTED
```

`carved/audit.txt` is exactly the kind of evidence trail you want — file, byte offset, length, output filename.

### `bulk_extractor`

Different mindset: instead of carving files, it pulls out **strings of interest**:

```bash
sudo apt install bulk-extractor
bulk_extractor -o bulk_out disk.img
ls bulk_out/
# email.txt       url.txt        ccn.txt        hex.txt      ...

grep csot26 bulk_out/*.txt
```

Useful when the flag isn't a whole file but a string buried in slack space.

### Week 4 CTF — `carved-note`

The artifact at [../../CTFs/week-04/carved-note/disk/blob.bin](../../CTFs/week-04/carved-note/disk/blob.bin) is small enough that `strings` solves it immediately:

```bash
strings ../../CTFs/week-04/carved-note/disk/blob.bin
# junk junk csot26{carved_from_garbage} more junk
```

On a larger blob you would reach for `foremost` or `binwalk -e`. For a 48-byte file, `strings` is the right hammer.

---

## Log analysis

Logs are the single most-read forensic artifact. Almost every breach is detected — eventually — because something in a log file was unusual.

### Common log types

| Log | Path / source | Useful for |
|-----|---------------|------------|
| `auth.log` / `secure` | `/var/log/auth.log` | SSH logins, sudo, PAM failures |
| `syslog` / `messages` | `/var/log/syslog` | Kernel, daemons, generic system |
| `nginx`/`apache` access | `/var/log/nginx/access.log` | Every HTTP request hitting the server |
| `nginx`/`apache` error | `/var/log/nginx/error.log` | 5xx, config errors, scanner noise |
| `audit.log` | `/var/log/audit/` | auditd, syscall-level events |
| `journalctl` | systemd journal | Modern unified replacement for many syslog feeds |
| Windows Event Log | `.evtx` files | Security, Application, System events |

### Triage commands

```bash
# Failed SSH logins by IP
grep "Failed password" /var/log/auth.log \
  | awk '{print $11}' | sort | uniq -c | sort -rn | head

# 5xx requests from a specific path
awk '$9 ~ /^5/ && $7 ~ /\/admin/' /var/log/nginx/access.log

# Requests from a single IP, sorted by time
awk '$1 == "203.0.113.5"' /var/log/nginx/access.log

# All sudo invocations
grep sudo /var/log/auth.log | grep COMMAND

# journalctl
journalctl -u sshd --since "1 hour ago"
journalctl --since "2024-05-25 00:00" --until "2024-05-25 23:59"
```

### Apache/Nginx combined-log fields

```
198.51.100.7 - - [25/May/2024:10:15:32 +0530] "GET /admin HTTP/1.1" 403 287 "-" "curl/8.4"
│              │  │  │                          │              │   │   │   │
│              │  │  │                          │              │   │   │   └── User-Agent
│              │  │  │                          │              │   │   └── Referer
│              │  │  │                          │              │   └── Bytes sent
│              │  │  │                          │              └── HTTP status
│              │  │  │                          └── Request line ($7 = path)
│              │  │  └── Time (in [brackets])
│              │  └── Auth user
│              └── Identd
└── Client IP ($1)
```

The `$7 == path` and `$9 == status` columns are what you grep most.

### Week 4 CTF — `pcap-cleartext`

The challenge ships [../../CTFs/week-04/pcap-cleartext/traffic.txt](../../CTFs/week-04/pcap-cleartext/traffic.txt) — a text capture of one HTTP request. The hint says `grep -i flag traffic.txt`:

```bash
grep -i flag ../../CTFs/week-04/pcap-cleartext/traffic.txt
# X-Flag: csot26{wireshark_would_love_this}
```

In a real PCAP you'd use Wireshark or `tshark` — covered below.

---

## PCAP analysis

A **PCAP** (or **PCAPNG**) is a packet capture: every byte that crossed the wire, saved to disk. The killer tools:

| Tool | Purpose |
|------|---------|
| **Wireshark** | GUI; the canonical packet analyser |
| **tshark** | Command-line Wireshark — same engine, same filters |
| **tcpdump** | Capture and read; lighter weight |
| **NetworkMiner** | Auto-extracts files, sessions, credentials from a PCAP |

### Capturing

```bash
sudo tcpdump -i eth0 -w capture.pcap                 # capture everything
sudo tcpdump -i eth0 -w capture.pcap port 80          # only HTTP
sudo tcpdump -i any -w capture.pcap host 10.0.0.5     # only one host
```

> **Forensics tip.** On Wireshark in Kali, capture requires either root or membership in `wireshark` group. Add yourself with `sudo dpkg-reconfigure wireshark-common` then re-login. Otherwise capture interfaces are blank.

### Display filters in Wireshark / tshark

Wireshark has two filter languages:

| Filter | Where | Syntax | Example |
|--------|-------|--------|---------|
| Capture filter | tcpdump-style | BPF | `tcp port 80 and host 1.2.3.4` |
| Display filter | Wireshark GUI / `tshark -Y` | dotted | `tcp.port == 80 && ip.addr == 1.2.3.4` |

The most useful display filters:

| Filter | What it shows |
|--------|----------------|
| `http` | HTTP request/response packets |
| `http.request` | HTTP requests only |
| `http.response.code == 200` | Successful responses |
| `dns` | DNS queries and responses |
| `tcp.port == 22` | SSH traffic |
| `ip.addr == 10.0.0.5` | Anything to or from 10.0.0.5 |
| `tcp.stream eq 0` | All packets in TCP stream 0 |
| `frame contains "csot26"` | Frames with the literal string |
| `ftp.request.command == "USER"` | FTP authentication |
| `tcp.flags.syn == 1 && tcp.flags.ack == 0` | SYN-only (scan signals) |

### Follow stream

In Wireshark: right-click any packet → `Follow → TCP/UDP/HTTP Stream`. Wireshark reassembles the entire conversation as readable text. This is how you read cleartext credentials, exfiltrated files, or in-band commands in two clicks.

### `tshark` for scripting

```bash
# List all HTTP request URIs
tshark -r capture.pcap -Y http.request -T fields -e http.host -e http.request.uri

# Pull all DNS queries
tshark -r capture.pcap -Y dns -T fields -e dns.qry.name | sort -u

# Find anything that contains 'csot26'
tshark -r capture.pcap -Y 'frame contains "csot26"' -T fields -e frame.number -e ip.src -e ip.dst

# Extract HTTP objects (download files transferred over HTTP)
tshark -r capture.pcap --export-objects http,/tmp/http_objects
```

The HTTP-object export is gold — if an attacker uploaded a web shell or downloaded a payload, you find it as a file in the output directory.

### Cleartext protocols to watch for

| Protocol | What leaks |
|----------|------------|
| HTTP (no TLS) | URL paths, headers, request bodies, cookies, sometimes credentials |
| FTP | Username, password, file listings, all file contents |
| Telnet | Everything typed and displayed |
| SMTP / IMAP / POP3 (no STARTTLS) | Email contents, AUTH PLAIN credentials |
| SNMP v1/v2c | Community string == password |
| DNS | Every domain queried |
| NTLM (Windows) | Challenge-response, often crackable offline |
| LDAP (no TLS) | Bind credentials in plaintext |

If you find these in a capture from a "secure" environment, you've found a finding.

---

## Memory forensics (overview)

A RAM dump captures *the running state* of a machine: process list, open sockets, decrypted data, injected DLLs, malicious code that exists only in memory.

### Acquisition

| OS | Tool |
|----|------|
| Linux | `LiME` (kernel module), `avml` (Microsoft), `dd` of `/dev/mem` (limited on modern kernels) |
| Windows | `winpmem`, `DumpIt`, `Magnet RAM Capture` |
| macOS | `osxpmem` (older), commercial tools |

### Analysis with Volatility 3

```bash
pip install volatility3

vol -f memory.raw windows.info
vol -f memory.raw windows.pslist
vol -f memory.raw windows.netscan
vol -f memory.raw windows.cmdline
vol -f memory.raw windows.malfind
vol -f memory.raw windows.dumpfiles --pid 1234
```

For Linux dumps you need a matching **symbol table** (kernel version-specific). Volatility 3 ships some; for others you build one with `dwarf2json`.

Memory forensics is a deep topic — we mention it for awareness. The Week 4 CTF doesn't require memory analysis. For practice when you're ready: [Magnet Forensics CTF samples](https://www.magnetforensics.com/resources/magnet-virtual-summit-2024-ctf/) and the SANS FOR526 course material.

---

## Disk imaging and integrity hashing

You **never** analyse a suspect disk in-place. You image it first, hash both copies, then work on the copy. If anything you do modifies the copy, the hash mismatch with the original proves the analysis didn't tamper with evidence.

### `dd` — the original

```bash
sudo dd if=/dev/sdb of=/tmp/usb.img bs=4M status=progress conv=noerror,sync
```

| Flag | Meaning |
|------|---------|
| `if=` | input file (the device) |
| `of=` | output file (the image) |
| `bs=4M` | block size — bigger is faster on modern disks |
| `conv=noerror,sync` | keep going past read errors; pad bad blocks with zeros |
| `status=progress` | print progress to stderr (modern coreutils) |

### `dcfldd` — `dd` for forensics

`dcfldd` is `dd` with built-in hashing, progress reporting, and split output. Better choice for serious acquisition.

```bash
sudo apt install dcfldd
sudo dcfldd if=/dev/sdb of=usb.img hash=sha256 hashlog=usb.sha256 \
            bs=4M conv=noerror,sync status=on
```

### Hashing for integrity

```bash
sha256sum usb.img > usb.sha256
sha256sum -c usb.sha256
# usb.img: OK
```

If anyone (you, the case officer, the court) re-runs the hash later and gets the same digest, the image hasn't been altered. That's chain of custody in math form.

### Mounting an image read-only

```bash
sudo mkdir /mnt/case
sudo mount -o ro,loop usb.img /mnt/case
ls /mnt/case/
sudo umount /mnt/case
```

For images with partition tables, attach as a loop device with offsets:

```bash
sudo losetup -P /dev/loop10 usb.img
sudo mount -o ro /dev/loop10p1 /mnt/case
```

The `-o ro` (read-only) is critical. Skip it and your analysis can change filesystem mount timestamps — instant evidence contamination.

---

## Timeline analysis

A **timeline** is "every event with a timestamp, sorted." Built from filesystem metadata (`atime`/`mtime`/`ctime`), log entries, browser history, registry hives, Plaso super-timelines.

### Quick filesystem timeline with `find`

```bash
find /mnt/case -printf '%T+ %p\n' 2>/dev/null | sort
# 2024-05-25+09:42:11 /mnt/case/etc/passwd
# 2024-05-25+10:13:08 /mnt/case/tmp/payload.sh
# ...
```

### Plaso / log2timeline (industrial-strength)

```bash
log2timeline.py --storage-file case.plaso /mnt/case
psort.py -o l2tcsv -w case.csv case.plaso
```

Open `case.csv` in any spreadsheet, sort by time, look at the moments around your incident time. Plaso parses dozens of artifact types — registry, MFT, event logs, browser history, prefetch.

---

## Chain of custody — what to document

This is what separates a usable forensic report from a "trust me bro":

| Field | What to record |
|-------|----------------|
| Item ID | Unique label for this evidence (e.g. `CASE-001-DISK-01`) |
| Source | Where it came from (hostname, location, who handed it to you) |
| Collected by | Name + role |
| Collected at | Date, time, timezone |
| Hash | SHA-256 of the acquired image (and tool used) |
| Tool used | `dcfldd 1.7.x` |
| Storage | Where the original now lives (sealed bag, encrypted drive, etc.) |
| Each handoff | Date, from whom, to whom, signed |

For CTFs the bar is much lower — you can just keep a `notes.md` of what you did. But the habit of "every action is logged" carries through to professional work.

---

## Forensics tool table (quick reference)

| Tool | Purpose |
|------|---------|
| `file` | Identify file type |
| `xxd` / `hexdump` / `bvi` | Hex inspection |
| `strings` | Printable text from binaries |
| `binwalk` | Embedded file detection |
| `foremost`, `scalpel`, `photorec` | File carving |
| `bulk_extractor` | String-of-interest extraction |
| `tcpdump`, `tshark`, Wireshark | Packet capture and analysis |
| `NetworkMiner` | Automated PCAP file/credential extraction |
| `volatility3` | Memory forensics |
| `dd`, `dcfldd`, `ewfacquire` | Disk imaging |
| `sleuthkit` (`fls`, `tsk_recover`, `mmls`) | Filesystem-level analysis |
| `Autopsy` | GUI on top of sleuthkit |
| `log2timeline` / `plaso` | Super-timelines |
| `regripper` | Windows registry parsing |
| `chainsaw`, `evtx_dump` | Windows event log triage |
| `exiftool` | Document metadata |
| `pdfid`, `pdf-parser`, `peepdf` | PDF analysis |
| `jadx`, `apktool` | APK reverse engineering |

A working Kali install has most of these out of the box. For the ones it doesn't (`chainsaw`, `dcfldd` sometimes), `apt install` covers it.

---

## Ethics and legality of forensic work

Even more than other modules, forensics intersects with law:

- **In a CTF or lab** — image away. The artifacts are yours.
- **At work, on assets you own** — fine, but follow your company's IR playbook so the evidence is admissible internally.
- **On someone else's device or network** — needs explicit, written authorization. Plugging an unfamiliar USB into your analysis machine is a security risk *and* a legal risk if you didn't have permission to acquire it.
- **Cross-border** — data sovereignty laws (GDPR, DPDP Act) regulate what you can image and move across jurisdictions. For multinational incidents, get counsel involved early.

> **Forensics tip.** Always work on a copy. Always hash before and after. Always log what you did. If you can't answer "what tool produced this evidence and when" you don't have evidence — you have a guess.

---

## CSOT CTF cross-reference

| Challenge | Technique | Tool of choice |
|-----------|-----------|----------------|
| [pcap-cleartext](../../CTFs/week-04/pcap-cleartext/) | Find a flag in HTTP request text | `grep`, `tshark`, Wireshark |
| [carved-note](../../CTFs/week-04/carved-note/) | Recover a flag from a raw blob | `strings`, `foremost`, `binwalk` |
| [metadata-leak](../../CTFs/week-04/metadata-leak/) | Read metadata from an image / artifact | `exiftool` |
| [hash-identify](../../CTFs/week-04/hash-identify/) | Identify and crack a hash | `hashid` + `hashcat` (covered in [hash-cracking.md](hash-cracking.md)) |

Each one rehearses a specific muscle. After solving all four, the broad forensics workflow (`file` → metadata → strings → carving → specialised tool) will feel automatic.

---

## End-to-end workflow — "you get a disk image"

When you're handed `case.img` cold, here's the ordered pass:

```bash
# 0. Hash the image for integrity
sha256sum case.img > case.sha256

# 1. Identify
file case.img
mmls case.img                                   # partition table from sleuthkit

# 2. Mount partitions read-only
sudo losetup -P /dev/loop10 case.img
sudo mkdir /mnt/case
sudo mount -o ro /dev/loop10p1 /mnt/case

# 3. Quick artefacts
fls -r -m / /dev/loop10p1 > body.txt           # body file for timeline
mactime -b body.txt > timeline.txt
ls /mnt/case/{etc/passwd,etc/shadow,home,var/log} 2>/dev/null

# 4. Targeted searches
grep -rE 'csot26\{|password|api[_-]?key' /mnt/case 2>/dev/null
strings /mnt/case/var/log/* | grep -i csot26

# 5. Carve deleted data
foremost -i case.img -o carved/
bulk_extractor -o bulk_out case.img

# 6. Network artefacts if any
tshark -r /mnt/case/path/to/capture.pcap -Y 'frame contains "csot26"'

# 7. Tear down
sudo umount /mnt/case
sudo losetup -d /dev/loop10
sha256sum case.img                              # confirm matches case.sha256
```

That sequence handles 80% of disk-image CTFs. For the others, you'll know what's missing because steps 2 / 4 / 5 will turn up something weird that drives the next investigation.

---

## Practice progression

- **CSOT Week 4 CTF** — [pcap-cleartext](../../CTFs/week-04/pcap-cleartext/), [carved-note](../../CTFs/week-04/carved-note/), [metadata-leak](../../CTFs/week-04/metadata-leak/), [hash-identify](../../CTFs/week-04/hash-identify/).
- **picoCTF Forensics gym** — many challenges in the spirit of this module.
- **TryHackMe** — *Volatility*, *Disk Analysis & Autopsy*, *Network Miner*, *Wireshark 101*.
- **HackTheBox — Forensics** category.
- **SANS DFIR public CTFs** — Magnet Virtual Summit, DFRWS challenges (free).
- **CyberDefenders.org** — labs with real-world incident scenarios.

---

## Further reading

- [SANS DFIR Cheatsheets](https://www.sans.org/posters/?focus-area=digital-forensics) — single-page references for Windows artifacts, memory, network.
- [Wireshark User's Guide](https://www.wireshark.org/docs/wsug_html_chunked/) — official, thorough.
- [Volatility 3 docs](https://volatility3.readthedocs.io/) — plugin reference.
- [Sleuthkit / Autopsy book](https://sleuthkit.org/autopsy/docs/user-docs/) — disk-level forensics.
- [Hacking Exposed Computer Forensics](https://www.amazon.com/Hacking-Exposed-Computer-Forensics-Second/dp/0071626778) — classic reference.
- [The Honeynet Project — Forensic Challenges](https://www.honeynet.org/challenges/) — long-running public puzzles with full write-ups.

---

## Next module

[secrets-in-repos.md](secrets-in-repos.md) — Forensics applied to a specific, modern artifact: the Git repository. The same hunt for "what was deleted but is still recoverable" applies — only the filesystem is a DAG of commits.
