# Network scanning

Once you know *which network and host* a target lives on, the next question is **what's running on it**. Network scanning answers that. This module covers host discovery, port scanning with `nmap`, service interrogation with `nc`, and how to read the results without fooling yourself.

> **Authorization is non-negotiable.** Only scan hosts that fall into one of these buckets:
> - Your own VMs and Docker containers (Week 2 lab counts).
> - Targets on platforms that explicitly authorize scanning while you're on their VPN (TryHackMe, HackTheBox, PortSwigger Web Security Academy).
> - Systems with **written** permission from the owner.
>
> Scanning random internet IPs, your hostel network, or campus infrastructure is illegal under the IT Act (Sections 43, 66) and similar laws elsewhere — even if you don't actually break in.

---

## What scanning actually does

A "scan" is just **structured probing**: you send carefully chosen packets and infer what's on the other end from what comes back (or doesn't). Three layers, three questions:

1. **Host discovery** — is the machine alive?
2. **Port scanning** — which TCP/UDP ports are accepting connections?
3. **Service detection** — what software, and which version, is behind each open port?

Each step narrows the surface. By the end you should have a table like:

| Host | Port | Proto | State | Service | Version | Notes |
|------|------|-------|-------|---------|---------|-------|
| 192.168.56.100 | 22 | TCP | open | ssh | OpenSSH 8.9p1 | Newish — unlikely default creds |
| 192.168.56.100 | 80 | TCP | open | http | nginx 1.18 | Visit, look for `/admin`, `/robots.txt` |
| 192.168.56.100 | 3306 | TCP | open | mysql | MariaDB 10.5 | Don't brute; test for default/empty pwd |

That table drives the rest of the engagement.

---

## Host discovery

Before you scan every port on a machine, confirm the machine actually exists. There are several ways, each with different stealth and reliability trade-offs.

### `ping` — the dumbest, easiest check

```bash
ping -c 2 192.168.56.100      # Send 2 ICMP echo requests
```

Pros: trivially simple, gives you round-trip time.
Cons: many firewalls drop ICMP. A non-responding host might still be up.

### nmap ping sweep

To check a whole subnet at once:

```bash
nmap -sn 192.168.56.0/24      # -sn = "no port scan", just host discovery
```

`-sn` is much smarter than plain `ping`: on the same LAN it actually uses ARP (which is reliable and fast). On remote networks it sends ICMP echo, ICMP timestamp, TCP SYN to port 443, and TCP ACK to port 80, then declares the host up if **any** of those get a response.

### Skip discovery entirely

If you know the host is up (CTF lab, you just spun up the container), tell nmap to stop guessing:

```bash
nmap -Pn target               # -Pn = treat host as alive, skip discovery
```

Use this when ICMP is blocked or when discovery probes are wasting time on a target you know exists.

---

## Port scanning with nmap

nmap is the swiss army knife of network scanning. Spend the time to learn its flags — you'll use it for years.

### The simplest scan

```bash
nmap target
```

By default this is a TCP SYN scan (if you're root) or TCP connect scan (if not), against nmap's top 1000 ports. Good first move on a CTF box; not exhaustive.

### Choosing what to scan

| Flag | Effect |
|------|--------|
| `-p 80,443,8080` | Specific ports |
| `-p 1-1000` | Range |
| `-p-` | **All** 65535 TCP ports (slow but thorough) |
| `--top-ports 100` | nmap's 100 most common |
| `-F` | "Fast" — top 100 ports |
| `-sU -p 53,161,500` | UDP scan of specific ports (UDP is slow; never `-p-`) |

**Realistic workflow:** start with `nmap -sV -sC target` for a quick read, then run `nmap -p- target` in another tab to catch anything hiding on a weird port.

### Scan techniques

You usually don't need to think about these, but knowing them helps you interpret results:

| Flag | Name | How it works | When to use |
|------|------|--------------|-------------|
| `-sS` | SYN/stealth | Sends SYN, reads response, never finishes handshake | Default when root; fastest, least logged |
| `-sT` | TCP connect | Full 3-way handshake (uses OS connect()) | When you're not root |
| `-sU` | UDP | Sends UDP probe; waits for reply or ICMP unreachable | Find DNS/SNMP/NTP services |
| `-sA` | ACK | Sends ACK; detects firewall rules | Mapping firewalls |
| `-sn` | Ping sweep only | No port scan | Discovery only |
| `-sV` | Version detection | Probes open ports for service banners | Almost always include |
| `-O` | OS detection | TCP/IP fingerprinting | Targeted attacks |
| `-A` | Aggressive | `-sV -O -sC --traceroute` combined | When stealth doesn't matter |

### NSE — the scripting engine

`-sC` runs the **default** set of NSE (Nmap Scripting Engine) scripts on open ports. NSE is a library of ~600 community scripts that do detailed probing — banner grabs, default-credential checks, vuln detection, enumeration.

```bash
nmap -sC target                                # Default scripts
nmap --script=http-title,http-headers target   # Specific scripts
nmap --script=vuln target                      # Run the entire "vuln" category
nmap --script "default and safe" target        # Boolean combinations
ls /usr/share/nmap/scripts/ | grep ssh         # Find SSH-related scripts
```

A few high-value scripts to know:

| Script | What it does |
|--------|--------------|
| `http-title` | Grabs `<title>` from HTTP responses |
| `http-headers` | Dumps response headers |
| `http-enum` | Brute-force common paths (`/admin`, `/wp-login.php`) |
| `ssh-hostkey` | Prints the host's SSH keys + algorithms |
| `ssl-cert` | TLS certificate details |
| `smb-os-discovery` | Windows version via SMB |
| `dns-brute` | Guess common subdomains |
| `vuln` (category) | All vuln-detection scripts |

### Speed and stealth

nmap is loud by default. You can dial timing:

| Template | Name | Use case |
|----------|------|----------|
| `-T0` | Paranoid | IDS evasion, very slow (hours) |
| `-T1` | Sneaky | IDS evasion |
| `-T2` | Polite | Avoids loading the network |
| `-T3` | **Default** | Reasonable |
| `-T4` | Aggressive | Lab and CTF networks |
| `-T5` | Insane | Fast but may miss results |

For our docker-compose lab, `-T4` is fine. For TryHackMe over VPN, default `-T3` is more reliable.

### Output formats — never leave the terminal without them

If you only print to your screen, you'll lose the result the first time you accidentally scroll. Always save:

```bash
nmap -sV -sC -oN scan.txt target          # Normal (human-readable)
nmap -sV -sC -oX scan.xml target          # XML (machine-parseable)
nmap -sV -sC -oG scan.gnmap target        # Greppable (one-line-per-host)
nmap -sV -sC -oA scan target              # All three: scan.{nmap,xml,gnmap}
```

You'll use the XML output in [recon-automation.md](recon-automation.md) to build reports automatically.

---

## A complete worked example

Here's a realistic enumeration sequence against a Week 2 lab target:

```bash
# 1. Confirm the host is up (works on local Docker network)
nmap -sn 127.0.0.1

# 2. Quick read: top 1000 ports, with version and default scripts
nmap -sV -sC -oN quick.txt 127.0.0.1

# 3. Full port sweep in parallel (different terminal)
nmap -p- -T4 -oN full.txt 127.0.0.1

# 4. For each interesting port found, deeper interrogation
nmap -p 8080 --script=http-enum,http-headers,http-title -oN web.txt 127.0.0.1

# 5. UDP top-100 (much slower)
sudo nmap -sU --top-ports 100 -oN udp.txt 127.0.0.1
```

### Interpreting an nmap report

```
PORT      STATE         SERVICE   VERSION
22/tcp    open          ssh       OpenSSH 8.9p1 Ubuntu 3ubuntu0.1
80/tcp    open          http      nginx 1.18.0
139/tcp   filtered      netbios-ssn
443/tcp   closed        https
3306/tcp  open          mysql     MariaDB 10.5.15
```

| State | What it means | Next step |
|-------|---------------|-----------|
| `open` | Service is accepting connections | Enumerate the service |
| `closed` | Host is up but nothing is listening on that port | Move on |
| `filtered` | A firewall is blocking probes | Try different scan type or accept it's blocked |
| `open\|filtered` | Couldn't determine (common on UDP) | Re-probe with `-sV` |
| `unfiltered` | Reachable but state unknown (rare, used with `-sA`) | Combine with other scan |

A `filtered` result doesn't mean "closed forever" — it means a firewall ate the probe. The service might be reachable from a different source IP or with a different scan technique.

---

## Netcat — the swiss army knife of TCP

`nc` (netcat) is a low-level tool that connects TCP/UDP sockets together. Where nmap is a microscope, nc is a pair of pliers. You'll use it constantly.

### Reading service banners

Many services announce themselves on connect. Just `nc` to the port:

```bash
nc target 22
# SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1   ← banner

nc target 25
# 220 mail.example.com ESMTP Postfix         ← SMTP greeting
```

### Talking HTTP by hand

```bash
nc target 80
GET / HTTP/1.1
Host: target
(blank line — press Enter twice)
```

You'll see the raw HTTP response. Indispensable when you're troubleshooting and need to know exactly what the server returned.

### Listen / connect

```bash
nc -lvnp 4444             # Listen on port 4444, verbose, no DNS, persistent
nc target 4444            # Connect to a listener and chat

# Simple port check
nc -zv target 80          # -z = "no I/O", just probe; prints open/closed
nc -zv target 1-1024 2>&1 | grep succeeded
```

### File transfer (no SSH needed)

```bash
# Receiver
nc -lvnp 4444 > received.bin

# Sender
nc -w 5 receiver-ip 4444 < send.bin
```

### Two important variants

There are several `nc` implementations and they differ slightly:

| Variant | Notes |
|---------|-------|
| `nc` (BSD/OpenBSD) — usual default on Kali | `-l -v -n -p` style flags |
| `nc.traditional` (Hobbit's original) | Same flags but `-e` exists by default |
| `ncat` (nmap project) | Adds TLS, multi-client, scripting (`--exec`, `--ssl`) |

If a command doesn't work, check `which nc` and read `man nc`.

---

## Practical recon recipes

### "Give me a one-pager on this host"

```bash
nmap -sV -sC -oA host_$(date +%F) target
```

### "What's exposed on my own machine?"

```bash
sudo ss -tulpn                       # Listening ports
sudo nmap -sV -sC 127.0.0.1          # External view of your own machine
```

### "Find every web server in this subnet"

```bash
nmap -p 80,443,8080,8443 --open -oG - 192.168.56.0/24 | grep open
```

### "Probe a single port quickly"

```bash
nc -zv target 9001 && echo OPEN || echo CLOSED
```

### "Dump banners for a list of ports"

```bash
for port in 22 25 80 110 143; do
  echo "=== $port ==="
  timeout 2 nc -nv target "$port" </dev/null 2>&1 | head -3
done
```

---

## Common gotchas

| Symptom | Likely cause |
|---------|--------------|
| Nmap says host is down but you can SSH to it | ICMP is blocked — use `-Pn` |
| Scan takes forever | You enabled `-p-` and `-sV` together; split into two passes |
| Ports show as filtered everywhere | A firewall is dropping probes — try from inside the network, or use `-sT` |
| No banner from `nc` | Service may need input first (HTTP needs a request) |
| Version detection wrong | Banner was spoofed or stripped — verify with NSE scripts |
| Different scans give different answers | Some scans hit cache/rate-limit; re-run with different timing |

---

## Connecting to the Week 2 lab

The lab is a small docker-compose stack with two services:

| Service | Port | What it is |
|---------|------|------------|
| `nc-service` | `127.0.0.1:9001` | Plain TCP — challenge for the `nc` workflow |
| `http-banner` | `127.0.0.1:8080` | nginx serving a synthetic banner page |

Start it:

```bash
cd CTFs/week-02/_infra
sudo docker compose up -d
```

Then practice everything you just read:

```bash
# Discover
nmap -sn 127.0.0.1

# Scan ports
nmap -sV -sC -p 8080,9001 -oN lab.txt 127.0.0.1

# Banner-grab the netcat service
echo "HELLO_CSOT" | nc 127.0.0.1 9001     # See ../../CTFs/week-02/netcat-handshake/

# Banner-grab the HTTP service
curl -sI http://127.0.0.1:8080            # See ../../CTFs/week-02/banner-guess/
```

Stop:

```bash
sudo docker compose down
```

The corresponding CTF challenges:

- [../../CTFs/week-02/banner-guess/](../../CTFs/week-02/banner-guess/) — match the HTTP response banner to its service.
- [../../CTFs/week-02/netcat-handshake/](../../CTFs/week-02/netcat-handshake/) — exchange the correct greeting.
- [../../CTFs/week-02/scan-report/](../../CTFs/week-02/scan-report/) — find the flag hidden in nmap output comments.
- [../../CTFs/week-02/port-logic/](../../CTFs/week-02/port-logic/) — port-number riddle, tests recall of the well-known ports table.

---

## External practice

| Platform | What to do |
|----------|------------|
| TryHackMe | "Nmap" room — guided walk-through |
| TryHackMe | "Introductory Networking" room |
| TryHackMe | "Network Services" / "Network Services 2" |
| HackTheBox | Starting Point machines (Tier 0 → Tier 1) — every box starts with nmap |
| Bandit (overthewire) | Practice `nc` interactively |

---

## Further reading

- [Official nmap book](https://nmap.org/book/) — free, exhaustive, by the author.
- [`man nmap`](https://nmap.org/book/man.html) — bookmark this.
- [HackTricks — Pentesting methodology](https://book.hacktricks.xyz/generic-methodologies-and-resources/pentesting-methodology) — what to do *after* a scan.
- [SANS Internet Storm Center](https://isc.sans.edu/) — see real scanning patterns observed in the wild.

---

## Next module

[dns-enumeration.md](dns-enumeration.md) — DNS is its own world of recon. The next module covers `dig`, subdomain discovery, WHOIS, and zone transfers.
