# DNS enumeration

DNS is one of the noisiest, most overlooked sources of intelligence on the internet. Subdomain names reveal internal tooling. TXT records leak verification tokens, third-party services, and sometimes secrets. Old zone-transfer misconfigurations dump entire DNS tables. CDNs hide origin IPs that historical records still expose.

This module covers how DNS works, how to query it precisely, and how to enumerate a domain without ever touching the target's actual web server.

---

## How DNS actually works

DNS is a distributed, hierarchical key/value store. Every lookup walks a tree from the root downward:

```
1. Your resolver asks the root servers:   "Where is .com?"
2. Root replies:                          "Ask the .com TLD servers."
3. Resolver asks .com:                    "Where is example.com?"
4. .com replies:                          "Ask ns1.example.com (the authoritative server)."
5. Resolver asks ns1.example.com:         "What's the A record for example.com?"
6. Authoritative server replies:          "93.184.216.34"
7. Resolver caches the answer and returns it to you.
```

Two important consequences:

- The **authoritative** server is the source of truth. Public resolvers (`8.8.8.8`, `1.1.1.1`) just cache and forward.
- DNS answers are **public by design**. Anything in the zone is fair game to query — no break-in required.

### Resolvers, recursion, and your own configuration

```bash
cat /etc/resolv.conf       # Which DNS servers does your machine use?
# nameserver 1.1.1.1
# nameserver 8.8.8.8

resolvectl status          # On systemd systems — fuller view
```

When you run `dig example.com`, your query goes to the resolver listed above. To bypass the cache and ask a specific server directly, use `@`:

```bash
dig @1.1.1.1 example.com
dig @ns1.example.com example.com    # Ask the authoritative server directly
```

---

## Record types you should recognize

DNS has dozens of record types. These ten cover ~99% of recon work:

| Record | Returns | Why it matters |
|--------|---------|----------------|
| `A` | IPv4 address | The basic name → IP mapping |
| `AAAA` | IPv6 address | Increasingly common |
| `CNAME` | Alias to another name | Reveals CDNs, SaaS providers |
| `MX` | Mail exchangers | Mail infrastructure (often Google Workspace, Microsoft 365) |
| `TXT` | Arbitrary text | SPF, DKIM, verification, **sometimes leaks** |
| `NS` | Authoritative name servers | Reveals DNS provider |
| `SOA` | Start of Authority | Admin contact, serial number |
| `PTR` | Reverse lookup (IP → name) | Often reveals hosting provider or role |
| `SRV` | Service location | SIP, XMPP, AD service discovery |
| `CAA` | Cert Authority Authorization | Which CAs can issue certs for the domain |

### Why `TXT` is the most interesting one

TXT records were designed for arbitrary text. In practice they hold:

| Pattern | Example | What it tells you |
|---------|---------|-------------------|
| SPF | `v=spf1 include:_spf.google.com ~all` | Google Workspace for email |
| DKIM | `v=DKIM1; k=rsa; p=...` | Mail signing key |
| DMARC | `v=DMARC1; p=reject; rua=mailto:...` | Mail security policy + admin email |
| Verification | `google-site-verification=...` | Owner uses Google Search Console |
| Verification | `MS=ms12345678` | Owner uses Microsoft 365 |
| Verification | `atlassian-domain-verification=...` | Owner uses Jira/Confluence |
| CTF / lab | `csot26{...}` | The whole reason we're here |

Every `include:` and verification string points to **another vendor the target uses**. That's a goldmine for understanding their stack — and where you can apply social-engineering pretexts (Week 2, [social-engineering-awareness.md](social-engineering-awareness.md)).

---

## The core tool: `dig`

`dig` (Domain Information Groper) is the standard DNS-debugging tool. Learn it well; you'll lean on it constantly.

### Syntax

```
dig [@server] [name] [type] [+options]
```

Order doesn't really matter; `dig` figures it out. Common forms:

```bash
dig example.com                          # A record (default), full output
dig example.com +short                   # Just the value(s)
dig example.com A +short                 # Explicit record type
dig example.com MX +short                # Mail servers
dig example.com TXT +short               # TXT records
dig example.com NS                       # Name servers (full output)
dig example.com ANY                      # Everything (often refused/limited)
dig @8.8.8.8 example.com                 # Query via Google DNS
dig -x 93.184.216.34 +short              # Reverse lookup
dig example.com +trace                   # Walk the delegation tree from root
dig example.com +short +noall +answer    # Custom output
```

### Reading dig output

```
; <<>> DiG 9.18.12 <<>> example.com
;; ANSWER SECTION:
example.com.       3589    IN    A      93.184.216.34
;; AUTHORITY SECTION:
example.com.       3589    IN    NS     a.iana-servers.net.
;; Query time: 24 msec
;; SERVER: 1.1.1.1#53(1.1.1.1)
```

| Section | What it contains |
|---------|------------------|
| `ANSWER` | The records you asked for |
| `AUTHORITY` | NS records of the authoritative servers for the zone |
| `ADDITIONAL` | "Helper" records (e.g., IPs of those NS servers) |
| `Query time` | Round trip — useful when cache vs. authoritative matters |

The `3589` is the **TTL** (time-to-live) — how many seconds resolvers may cache this answer. A very low TTL (60s) often means the domain is using a load balancer or failover.

### Other resolvers — `host`, `nslookup`

```bash
host example.com                  # Quick, terse
host -t MX example.com
host -t TXT example.com

nslookup example.com              # Interactive or one-shot
nslookup -type=MX example.com
```

`dig` is more powerful, but `host` is fast for scripting and `nslookup` ships everywhere (including Windows).

---

## WHOIS — registration data

WHOIS is the public registration database for domain names. It tells you who registered the domain, where, with whom, and when.

```bash
whois example.com
```

Useful fields you'll see (depending on registrar, redaction laws, and TLD):

| Field | What it reveals |
|-------|-----------------|
| Registrar | The company managing the registration |
| Creation Date | How old the domain is — new domains are phishing red flags |
| Updated Date | When records last changed |
| Expiry Date | When the registration ends |
| Name Servers | Confirms DNS provider |
| Registrant Org / Email | Who owns it (often redacted under GDPR) |
| Admin / Tech Contact | Sometimes still exposed; pretexting material |

GDPR and similar regulations have stripped most personal data from WHOIS in recent years. You'll still get registrar, dates, and name servers — which is plenty.

WHOIS for IP addresses works too and tells you the **AS** (autonomous system) the IP belongs to:

```bash
whois 93.184.216.34            # Which ISP/ASN owns this IP block?
```

---

## Subdomain discovery — passive (safe)

Subdomains expose internal tools and forgotten infrastructure. There are two ways to find them: **passive** (querying third-party data) and **active** (probing the target). Always start passive.

### Certificate transparency (CT) logs

Every TLS certificate issued by a public CA is logged publicly. If a subdomain ever had a cert, it's recorded forever.

- [crt.sh](https://crt.sh/) — search certificates by domain
- [Censys](https://search.censys.io/) — broader certificate + service search

```bash
# crt.sh has a JSON endpoint
curl -s "https://crt.sh/?q=%25.example.com&output=json" \
  | jq -r '.[].name_value' \
  | tr ',' '\n' | sort -u
```

This often turns up `dev.`, `staging.`, `internal.`, `vpn.`, `mail.`, `api.` — none of which are linked from the public website but all of which the target uses.

### Passive DNS aggregators

These services collect DNS queries from many vantage points and let you search the history of a domain:

- [SecurityTrails](https://securitytrails.com/) (free tier)
- [VirusTotal](https://www.virustotal.com/) — "Relations" tab
- [DNSdumpster](https://dnsdumpster.com/) — quick visual map
- [Shodan](https://www.shodan.io/) — search by DNS too

### Tools that combine sources

```bash
# subfinder (ProjectDiscovery) — fast, multi-source passive
subfinder -d example.com -silent

# amass (OWASP) — more thorough, slower
amass enum -passive -d example.com
```

Install:

```bash
# Subfinder (Go)
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Amass (Go) or via apt on Kali
sudo apt install amass
```

**These tools are passive by default** — they query third-party APIs, not the target. Stay passive unless you're explicitly authorized to be active.

---

## Subdomain discovery — active (authorization required)

When you do have authorization (your own lab, an explicit scope), active enumeration is more thorough.

### Wordlist-based DNS brute force

You ask the resolver about thousands of plausible names (`api.example.com`, `dev.example.com`, …) and record which ones resolve:

```bash
# gobuster
gobuster dns -d example.com -w /usr/share/wordlists/dnsmap.txt

# ffuf — flexible, fast
ffuf -u https://FUZZ.example.com -w subdomains.txt -mc 200

# dnsenum / dnsrecon
dnsenum example.com
dnsrecon -d example.com -t brt -D subdomains.txt
```

Wordlist sources: [SecLists](https://github.com/danielmiessler/SecLists) (`Discovery/DNS/`).

### Virtual-host (vhost) discovery

Many subdomains resolve to the **same IP** as the main site and are distinguished only by the `Host:` HTTP header. Wordlist scans against `FUZZ.target` won't catch these — they don't have DNS entries at all.

```bash
ffuf -u https://target/ -H "Host: FUZZ.target" -w subdomains.txt -fc 404
```

You're discovering which `Host:` headers the web server actually serves content for, regardless of DNS.

---

## Zone transfers — rare but devastating when they exist

A zone transfer (AXFR) is the mechanism authoritative DNS servers use to replicate the full zone file between primary and secondary. If misconfigured to allow anyone to request a transfer, the entire DNS map of the domain spills out.

```bash
# Find authoritative servers
dig NS example.com +short

# Attempt zone transfer against each
dig AXFR @ns1.example.com example.com
dig AXFR @ns2.example.com example.com
```

If it works, you get every A, MX, TXT, CNAME record in one response — basically a free subdomain dump plus internal hostnames.

This is well-known and almost always disabled today. But "almost" isn't "always" — always try it once when in scope. Tools like `dnsrecon -t axfr -d example.com` automate the attempt against every NS.

---

## Reverse DNS sweeps

If you know the target owns a contiguous IP block (from WHOIS / ASN lookup), reverse DNS often labels each IP with its role:

```bash
# Single reverse lookup
dig -x 93.184.216.34 +short

# Sweep a /24
for i in $(seq 1 254); do
  dig -x 192.0.2.$i +short | sed -n "s/.*/192.0.2.$i &/p"
done
```

You'll see names like `mail01.example.com`, `vpn.example.com`, `git-internal.example.com` — each one a target.

---

## DNS in modern privacy modes

The DNS landscape has shifted recently. You should know about it:

| Standard | Port | Meaning |
|----------|------|---------|
| Classic DNS | UDP/53, TCP/53 | Plaintext, observable by anyone on path |
| DoT (DNS-over-TLS) | TCP/853 | Encrypted to the resolver |
| DoH (DNS-over-HTTPS) | TCP/443 | Encrypted, indistinguishable from HTTPS traffic |
| DNSSEC | n/a | Adds cryptographic signatures so resolvers can verify answers |

For your queries to be private, the resolver you point at must support DoH/DoT (`1.1.1.1`, `8.8.8.8`, `9.9.9.9` all do). For the **target's** zone to be tamper-resistant, the *target* must publish DNSSEC signatures. Most still don't.

```bash
dig example.com +dnssec +short          # See signatures if present
dig example.com DS +short               # DS records in parent zone
```

---

## Building a domain dossier

A complete recon pass on a domain looks roughly like this:

```bash
DOMAIN=example.com
OUT="dns_${DOMAIN}_$(date +%F)"
mkdir -p "$OUT"

# 1. Authoritative servers and zone metadata
dig NS  "$DOMAIN" +short  >  "$OUT/ns.txt"
dig SOA "$DOMAIN" +short  >  "$OUT/soa.txt"

# 2. Common record types
for t in A AAAA MX TXT CAA; do
  dig "$t" "$DOMAIN" +short > "$OUT/$t.txt"
done

# 3. WHOIS
whois "$DOMAIN" > "$OUT/whois.txt"

# 4. Reverse lookup of A records
for ip in $(cat "$OUT/A.txt"); do
  echo "$ip $(dig -x "$ip" +short)"
done > "$OUT/ptr.txt"

# 5. Passive subdomains (no probing the target directly)
curl -s "https://crt.sh/?q=%25.$DOMAIN&output=json" \
  | jq -r '.[].name_value' | tr ',' '\n' | sort -u \
  > "$OUT/crt_subdomains.txt"

# 6. Zone transfer attempt (just in case)
for ns in $(cat "$OUT/ns.txt"); do
  dig AXFR "@$ns" "$DOMAIN" > "$OUT/axfr_$ns.txt" 2>&1
done

echo "Done. See $OUT/"
```

This is the kind of script we develop in [recon-automation.md](recon-automation.md).

---

## Lab — the Week 2 DNS challenge

The lab challenge [../../CTFs/week-02/dns-txt-flag/](../../CTFs/week-02/dns-txt-flag/) ships a synthetic zone file (`zone.txt`) instead of running a real authoritative server. The exercise is reading zone-file syntax and finding the TXT record that contains the flag.

Zone-file syntax cheat sheet (RFC 1035):

```
$ORIGIN example.com.            ; current zone
$TTL 3600                        ; default TTL
@       IN  SOA  ns1 admin (
                 2024010101  ; serial
                 3600        ; refresh
                 1800        ; retry
                 604800      ; expire
                 86400 )     ; minimum
@       IN  NS   ns1
@       IN  A    93.184.216.34
www     IN  CNAME @
mail    IN  A    93.184.216.35
@       IN  MX   10 mail
challenge IN TXT "csot26{example_flag_format}"
```

Notes that trip people up:

- `@` means "this zone's apex".
- Names without a trailing `.` are relative to `$ORIGIN`.
- TXT records are quoted strings.
- Serial number bumps on every change (`YYYYMMDDnn` convention).

---

## Ethics, scope, and rate limiting

DNS itself is public — you're not breaking anything by running `dig` against `example.com`. But:

- Repeated brute-force enumeration against someone else's authoritative server can look like a DoS. Stay in scope.
- Tools that query third-party APIs (crt.sh, SecurityTrails) have rate limits — respect them.
- WHOIS data, even when not redacted, is for technical contact. Don't email registered contacts unless that's your authorized purpose.
- In Indian law, unauthorized active enumeration of a domain you don't own can fall under Sec 43 of the IT Act.

---

## Further reading

- [DNS for Rocket Scientists](http://www.zytrax.com/books/dns/) — free, exhaustive online book.
- [Cloudflare — what is DNS?](https://www.cloudflare.com/learning/dns/what-is-dns/) — concise explainers.
- [HackTricks — Pentesting DNS](https://book.hacktricks.xyz/network-services-pentesting/pentesting-dns) — practical checklist.
- [SecLists — DNS wordlists](https://github.com/danielmiessler/SecLists/tree/master/Discovery/DNS) — when you go active.

---

## Next module

[osint-techniques.md](osint-techniques.md) — DNS is one slice of public information. OSINT widens the lens: search engines, social media, GitHub, metadata, archives.
