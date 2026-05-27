# Networking fundamentals

Before you can scan, enumerate, or attack a system, you need a mental model of how computers actually talk to each other. This module is the conceptual glue under the rest of Week 2: when you run `nmap`, query DNS, or read a packet capture, you should understand **what layer you're poking at** and **what could go wrong there**.

You don't need to memorize RFCs. You do need to know which protocol does what, where it lives in the stack, and how attackers and defenders use that to their advantage.

---

## Why networking matters for security

Almost every interesting attack surface lives on a network. A web app is exposed because TCP port 443 is open. A misconfigured DNS server leaks subdomains because zone transfers weren't restricted. A leaked database is reachable because someone bound MongoDB to `0.0.0.0` instead of `127.0.0.1`.

If you can answer these four questions about any system, you've understood enough networking to start probing it safely:

1. **What addresses** does it have (IP, hostname, MAC)?
2. **What ports** are open and which **services** are behind them?
3. **What protocol** does each service speak (TCP, UDP, HTTP, DNS, …)?
4. **What boundary** sits in front of it (NAT, firewall, load balancer, CDN)?

The rest of Week 2 — DNS enumeration, port scanning, OSINT — is just systematic ways to answer those questions.

---

## The layered model (practical view)

Networking textbooks teach the 7-layer OSI model. In practice, the 4-layer TCP/IP model is what you'll think in. Here's the version that maps to actual tools:

| Layer | Examples | Tools you'll use | Where attacks live |
|-------|----------|------------------|--------------------|
| **Application** | HTTP, HTTPS, DNS, SSH, SMTP, FTP | `curl`, `dig`, `ssh`, Burp | Web vulns, auth bypass, protocol abuse |
| **Transport** | TCP, UDP | `nmap`, `nc`, `ss` | Port scans, SYN floods, session hijack |
| **Network** | IPv4, IPv6, ICMP, routing | `ping`, `traceroute`, `ip route` | Spoofing, routing tricks, scanning |
| **Link** | Ethernet, Wi-Fi, ARP, MAC | `arp`, `tcpdump`, `aircrack-ng` | ARP spoofing, MAC flooding, evil twin |

A useful mental rule: **higher layers ride on lower layers**. An HTTPS request (Application) is wrapped in TLS, sent over TCP (Transport), addressed with IP (Network), and pushed onto a physical wire or radio (Link). When something fails, work from the bottom up: is the host reachable (Link/Network)? Is the port open (Transport)? Is the protocol speaking correctly (Application)?

### How a single web request flows

```
You type:  https://example.com/login
   │
   ▼
[Application]  Browser builds HTTP request
   │
   ▼
[Application]  DNS lookup: example.com → 93.184.216.34
   │
   ▼
[Transport]    TCP 3-way handshake to 93.184.216.34:443
   │
   ▼
[Application]  TLS handshake (certificate exchange, key agreement)
   │
   ▼
[Application]  HTTP request sent inside encrypted TLS tunnel
   │
   ▼
[Network]      Packets routed hop-by-hop across the internet
   │
   ▼
[Link]         Each hop: Ethernet/Wi-Fi frames between routers
```

Every box above is something an attacker or defender can observe, modify, or block. Recon work is mostly figuring out which of these layers leaks information you can use.

---

## IP addresses

An IP address uniquely identifies a network interface. There are two versions you'll meet:

### IPv4

32-bit address written as four decimal numbers separated by dots:

```
192.168.1.10
└┬─┘└┬┘└┘└┘
 │   │ │ │
 └───┴─┴─┴── 4 octets, each 0–255 (8 bits)
```

There are about 4.3 billion possible IPv4 addresses — far too few for the modern internet, which is why we use **NAT** (see below) and IPv6.

### IPv6

128-bit address written as eight groups of four hex digits:

```
2001:0db8:85a3:0000:0000:8a2e:0370:7334
```

Consecutive zero groups can be collapsed with `::` (once per address):

```
2001:db8:85a3::8a2e:370:7334
```

### Public vs private (RFC 1918) ranges

Private ranges are reserved for internal networks and are **not routable** on the public internet. You'll see them everywhere in lab environments:

| Range | Size | Typical use |
|-------|------|-------------|
| `10.0.0.0/8` | ~16.7M addresses | Corporate networks, cloud VPCs |
| `172.16.0.0/12` | ~1M addresses | Docker default networks |
| `192.168.0.0/16` | ~65K addresses | Home routers, small LANs |
| `127.0.0.0/8` | Loopback | `127.0.0.1` = "this machine" |
| `169.254.0.0/16` | Link-local | Cloud metadata (`169.254.169.254`) |

### CIDR notation

`/24` is shorthand for the subnet mask. The number after the slash is how many bits are the **network** portion; the rest are **host** bits.

| CIDR | Mask | Hosts | Example |
|------|------|-------|---------|
| `/32` | 255.255.255.255 | 1 | A single host |
| `/30` | 255.255.255.252 | 2 usable | Point-to-point links |
| `/24` | 255.255.255.0 | 254 usable | Typical small LAN |
| `/16` | 255.255.0.0 | 65,534 usable | A `/16` like `10.0.0.0/16` |
| `/8` | 255.0.0.0 | 16.7M | Whole `10.0.0.0/8` block |

```bash
ip addr                  # Show interfaces and assigned IPs
ip -br addr              # Brief one-line-per-interface format
hostname -I              # Just the IP(s) of this host
```

### NAT — why your laptop's IP isn't really yours

Most home and corporate networks use **Network Address Translation (NAT)**: many internal devices share one public IP, with the router rewriting source addresses and ports on the way out.

```
Laptop  192.168.1.10:51234 ──► Router 203.0.113.5:51234 ──► Internet
                              (NAT table maps the connection back)
```

This means:
- Your **private** IP (`192.168.x.x`) is visible to your LAN only.
- Your **public** IP (whatever your ISP gave the router) is what the world sees.
- Inbound connections need explicit port forwarding to reach a device behind NAT.

For recon, this changes everything: you can't directly scan a friend's laptop on a different network without first traversing their router/firewall.

---

## Ports

A port is a 16-bit number (0–65535) identifying a specific service on a host. An IP gets you to the machine; the port gets you to the right program running on that machine.

```
93.184.216.34 : 443
└──────┬───────┘ └┬┘
   Which host    Which service (HTTPS)
```

### Three port ranges

| Range | Name | Used for |
|-------|------|----------|
| 0–1023 | **Well-known** | Standard services (need root to bind on Linux) |
| 1024–49151 | **Registered** | App-specific (Postgres 5432, Redis 6379) |
| 49152–65535 | **Ephemeral** | Temporary client-side source ports |

### Ports you must recognize on sight

These will appear constantly in scans and CTFs:

| Port | Protocol | Service | What it tells you |
|------|----------|---------|-------------------|
| 21 | TCP | FTP | Old file transfer, often anonymous-enabled |
| 22 | TCP | SSH | Remote shell; brute-force target |
| 23 | TCP | Telnet | Plaintext shell; almost always misconfig |
| 25 | TCP | SMTP | Mail server; user enumeration |
| 53 | TCP/UDP | DNS | Name resolution; zone transfers |
| 80 | TCP | HTTP | Web app — start here |
| 110 | TCP | POP3 | Legacy mail retrieval |
| 111 | TCP/UDP | RPC | Often leaks NFS info |
| 139 | TCP | NetBIOS | Windows file sharing |
| 143 | TCP | IMAP | Mail retrieval |
| 161 | UDP | SNMP | Often default community `public` |
| 389 | TCP | LDAP | Directory; auth info |
| 443 | TCP | HTTPS | Web app over TLS |
| 445 | TCP | SMB | Windows file sharing; EternalBlue era |
| 587 | TCP | SMTP submission | Authenticated mail send |
| 631 | TCP | IPP/CUPS | Print services |
| 993 | TCP | IMAPS | IMAP over TLS |
| 995 | TCP | POP3S | POP3 over TLS |
| 1433 | TCP | MSSQL | Microsoft SQL Server |
| 1521 | TCP | Oracle | Oracle DB |
| 2049 | TCP | NFS | Network file system |
| 3306 | TCP | MySQL | DB; often exposed by accident |
| 3389 | TCP | RDP | Windows remote desktop |
| 5432 | TCP | PostgreSQL | DB |
| 5900 | TCP | VNC | Graphical remote |
| 6379 | TCP | Redis | Cache; often no auth |
| 8000/8080 | TCP | HTTP-alt | Dev servers, proxies |
| 8443 | TCP | HTTPS-alt | TLS dev servers |
| 9001 | TCP | (CSOT lab) | Week 2 netcat challenge |
| 27017 | TCP | MongoDB | DB |

When you see one of these in an nmap result, you immediately know what enumeration to do next.

### Inspect ports on your own machine

```bash
ss -tulpn                 # Listening TCP and UDP ports + process names
# -t TCP   -u UDP   -l listening   -p process   -n numeric

ss -tn state established  # Currently active TCP connections
netstat -tulpn            # Older equivalent of `ss`
lsof -i :8080             # Which process owns port 8080?
```

---

## TCP vs UDP — the two big transport protocols

Everything you scan ultimately runs on TCP or UDP. Knowing the difference tells you what to expect from a scan.

| | TCP | UDP |
|---|-----|-----|
| Connection | Yes (3-way handshake) | No (fire-and-forget) |
| Reliability | Retransmits lost packets | Best-effort, may drop silently |
| Ordering | In-order delivery guaranteed | No ordering |
| Overhead | Higher (headers, ACKs) | Minimal |
| Use cases | HTTP, SSH, SMTP, databases | DNS, NTP, DHCP, QUIC, VoIP, gaming |
| Scanning | Easy: SYN/ACK reveals open | Hard: no response is ambiguous |

### The TCP 3-way handshake

Every TCP connection starts with three packets:

```
Client                          Server
  │ ─────── SYN (seq=x) ─────► │
  │ ◄─── SYN-ACK (seq=y, ack=x+1) │
  │ ─────── ACK (ack=y+1) ───► │
  │                            │
  ├──── connection established ──┤
```

This is the basis for most port-scanning techniques:

- **Full connect scan (`nmap -sT`)** — completes the handshake. Visible in logs.
- **SYN/stealth scan (`nmap -sS`)** — sends SYN, reads response, never sends final ACK. Half-open; requires root.
- **No response** — `filtered` (firewall likely dropping packets).
- **RST returned** — `closed` (host alive, nothing listening).
- **SYN-ACK returned** — `open`.

### UDP is fundamentally different

UDP doesn't have a handshake. A scanner sends a UDP packet to a port and waits. There are only three outcomes:

| Response | Meaning |
|----------|---------|
| Application reply | `open` |
| ICMP "port unreachable" | `closed` |
| Nothing | `open\|filtered` (can't tell) |

This is why UDP scans (`nmap -sU`) are slow and noisy: when nothing comes back, the scanner has to wait through a timeout before giving up.

---

## ICMP — the network's diagnostic channel

ICMP (Internet Control Message Protocol) is the protocol used by `ping` and `traceroute`. It's not "TCP/UDP without ports" — it's a separate Layer 3 protocol used for status messages.

| Message | Used by | Purpose |
|---------|---------|---------|
| Echo request / reply | `ping` | "Are you alive?" |
| Destination unreachable | Routers | "I can't deliver this" |
| Time exceeded | Routers | "TTL hit zero" — used by `traceroute` |
| Redirect | Routers | "Use this gateway instead" |

```bash
ping -c 3 8.8.8.8         # 3 echo requests
traceroute example.com    # Hops between you and the host (uses TTL trickery)
mtr example.com           # Interactive traceroute + live packet loss
```

Some networks block ICMP. A host that doesn't respond to `ping` isn't necessarily down — it might just be ignoring echo requests. `nmap -Pn` tells nmap to skip the ping check and assume the host is up.

---

## ARP — how machines find each other on a LAN

On a local network (same subnet), machines don't address each other by IP at the lowest level — they use **MAC addresses** (48-bit hardware identifiers). ARP (Address Resolution Protocol) maps IP → MAC.

```bash
ip neigh                  # Show ARP/neighbor table
arp -a                    # Legacy equivalent
```

A typical entry:

```
192.168.1.1 dev wlan0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
```

Why it matters: ARP has no authentication. Anyone on your LAN can claim to be the router (ARP spoofing) and silently intercept your traffic. This is why coffee-shop Wi-Fi is risky and why HTTPS matters.

---

## DNS — names, not numbers

Humans use `github.com`. Computers use `140.82.112.3`. DNS bridges the two. DNS gets a dedicated module — [dns-enumeration.md](dns-enumeration.md) — but the short version:

| Record type | Returns | Example |
|-------------|---------|---------|
| `A` | IPv4 address | `example.com → 93.184.216.34` |
| `AAAA` | IPv6 address | `example.com → 2606:2800:220::` |
| `CNAME` | Alias to another name | `www → example.com` |
| `MX` | Mail server hostnames | Used to send mail to a domain |
| `TXT` | Arbitrary text | SPF/DKIM/verification tokens — often **leaks info** |
| `NS` | Authoritative name servers | Reveals DNS provider |
| `SOA` | Zone metadata | Admin email, serial number |
| `PTR` | Reverse lookup (IP → name) | Often reveals provider/role |

```bash
dig example.com                    # A record (default)
dig MX example.com +short          # Just the values
dig TXT example.com                # TXT records (verification, secrets)
dig @8.8.8.8 example.com           # Query Google's DNS specifically
host example.com                   # Quick lookup
nslookup example.com               # Older interactive tool
```

DNS uses UDP/53 for most queries and TCP/53 for large responses (and zone transfers). Modern variants — **DoH** (DNS over HTTPS) and **DoT** (DNS over TLS) — encrypt the query.

---

## HTTP — what almost every recon ends up touching

HTTP is the protocol of the web, and it'll be Week 3's main focus, but recon work touches it constantly. You need a working understanding now.

### Anatomy of an HTTP request

```
GET /login HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0
Accept: text/html
Cookie: session=abc123
```

| Part | Meaning |
|------|---------|
| `GET` | Method — what action to perform |
| `/login` | Path — which resource |
| `HTTP/1.1` | Protocol version |
| `Host:` | Which virtual host (multiple sites on one IP) |
| `Cookie:` | Stored session data |

### Methods you'll see

| Method | Purpose | Idempotent? |
|--------|---------|-------------|
| `GET` | Read a resource | Yes |
| `POST` | Submit data, create | No |
| `PUT` | Replace a resource | Yes |
| `PATCH` | Partially update | No |
| `DELETE` | Remove a resource | Yes |
| `HEAD` | Like GET but no body | Yes |
| `OPTIONS` | Ask which methods are allowed | Yes |

### Status codes — the response language

| Range | Class | Common examples |
|-------|-------|-----------------|
| 1xx | Informational | `101` switching protocols (WebSockets) |
| 2xx | Success | `200` OK, `201` Created, `204` No Content |
| 3xx | Redirect | `301` permanent, `302` temporary, `304` not modified |
| 4xx | Client error | `400` bad request, `401` unauth, `403` forbidden, `404` not found, `429` rate limited |
| 5xx | Server error | `500` internal, `502` bad gateway, `503` unavailable |

**Recon trick:** a `403` on `/admin` is more interesting than a `404`. `403` says "I exist but you can't see me." `404` says "nothing here." Different responses to the same path leak structure.

### Useful HTTP recon commands

```bash
curl -I https://example.com        # HEAD request — just response headers
curl -v https://example.com        # Verbose: TLS handshake + headers + body
curl -L https://example.com        # Follow redirects
curl -A "Mozilla/5.0" ...          # Spoof user agent
curl -s -o /dev/null -w "%{http_code}\n" https://example.com   # Just the status
```

Response headers that reveal information:

```
Server: nginx/1.18.0 (Ubuntu)         ← exact version → vuln lookup
X-Powered-By: PHP/7.4.3               ← stack disclosure
Set-Cookie: PHPSESSID=...; HttpOnly   ← framework hint
X-Frame-Options: DENY                  ← clickjacking protection
Strict-Transport-Security: max-age=...  ← HSTS configured
```

Hardened sites strip these. Unhardened ones tell you exactly what they're running.

---

## Putting it together — what happens when you `nmap -sV target.com`

You'll do this in [network-scanning.md](network-scanning.md), but here's the layered story so it isn't magic:

1. **DNS lookup** — your machine resolves `target.com` to an IP (Application/Network).
2. **Host discovery** — nmap may send ICMP echo, ARP (if local), or a TCP probe to see if the host is up (Network/Transport).
3. **Port scan** — for each candidate port, nmap crafts a TCP SYN, sends it, and waits for SYN-ACK / RST / nothing (Transport).
4. **Service detection** — for open ports, nmap connects fully and reads the **banner** the service sends (Application). HTTP returns `Server:`, SSH announces `SSH-2.0-OpenSSH_8.9`, etc.
5. **Output** — nmap prints what it learned, optionally to XML/JSON for later parsing (see [recon-automation.md](recon-automation.md)).

Knowing where each step lives in the stack tells you why scans behave the way they do — and where each step can be blocked, slowed, or spoofed.

---

## Quick reference — commands from this module

```bash
# Identity / interfaces
ip addr            ip route           hostname -I

# Listening / connections
ss -tulpn          ss -tn state established        lsof -i :PORT

# Reachability
ping -c 3 host     traceroute host    mtr host

# Neighbors (LAN)
ip neigh           arp -a

# DNS
dig name           dig MX name +short    dig @resolver name    host name

# HTTP
curl -I url        curl -v url        curl -L -A "agent" url

# Captures (preview — Week 5)
sudo tcpdump -i any -nn host TARGET
```

---

## Reading and reference

- [Computer Networking: A Top-Down Approach (Kurose & Ross)](https://gaia.cs.umass.edu/kurose_ross/index.php) — the standard textbook; first two chapters cover most of this module.
- [Cloudflare Learning Center](https://www.cloudflare.com/learning/) — short, accurate explainers on TCP/IP, DNS, TLS.
- [HackerNoon — 10 things infosec needs about networking](https://hackernoon.com/10-things-infosec-professionals-need-to-know-about-networking-d159946efc93)
- [RFC 791 — IPv4](https://datatracker.ietf.org/doc/html/rfc791), [RFC 793 — TCP](https://datatracker.ietf.org/doc/html/rfc793), [RFC 1035 — DNS](https://datatracker.ietf.org/doc/html/rfc1035) — for when you want the source of truth.

---

## Next module

[network-scanning.md](network-scanning.md) — apply this model with `nmap`, `nc`, and friends to discover hosts and services in the Week 2 lab.
