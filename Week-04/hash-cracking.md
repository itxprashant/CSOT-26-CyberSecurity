# Hash identification & password cracking

Hashing is one-way: you compute it forward in microseconds, you can't go backwards. Except — when the inputs are short, predictable, or human-chosen, "you can't go backwards" turns into "you guess inputs and check them." This is **password cracking**, and it's the bridge between the maths of hash functions and the reality of how people pick passwords.

This module covers: how to recognise a hash, which cracker to reach for, how to pick the right wordlist and attack mode, what makes a password hash *hard* to crack on purpose, and where the legal and ethical lines are.

---

## Why this module matters

- **Every real breach you'll read about ended in cracked password hashes.** Adobe (2013), LinkedIn (2012), Ashley Madison (2015), Yahoo (2014 — 3 billion accounts) — the dumps got cracked, the credential-stuffers followed, and the cascade hit everyone who reused passwords. Knowing how that pipeline works is half of defending against it.
- **CTF challenges constantly hand you hashes.** A blob of 32 hex chars is either an MD5 hash, a hex-encoded message, or a fragment of a SHA. You need to tell at a glance.
- **It teaches you why modern password storage looks weird.** `$argon2id$v=19$m=65536,t=3,p=4$...` is not a corruption — it's a deliberate format designed to defeat the exact techniques in this module. Once you've run hashcat against MD5 for an hour and Argon2 for a week, you understand why.

---

## A word on ethics — read this before running any commands

Cracking hashes is a powerful capability with a narrow legal lane. Stay in it.

| Allowed | Not allowed |
|---------|-------------|
| Hashes from CSOT CTFs and any course-provided lab | Hashes from a breach dump you found online |
| Hashes you generated yourself for testing | Hashes from someone else's database, even a friend's |
| Authorized engagements with **written** scope | An IT Act conviction is an IT Act conviction |
| Bug-bounty programs that explicitly include credential testing | "Practising" against a real site's `/etc/shadow` |
| Auditing your own services and own accounts | Anything involving someone else's account without consent |

The IT Act §43 in India and the CFAA in the US both treat possession and use of breach dumps as criminal in many circumstances — even when the data is on a public mirror. Don't be the cautionary tale.

For everything in this module, **the targets are lab artifacts**. The Week 4 CTF challenge [../../CTFs/week-04/hash-identify/](../../CTFs/week-04/hash-identify/) is the only hash you should be cracking on your own machine while working through these examples.

---

## Hash families and their fingerprints

The first skill is **recognition**. Every hash family has a tell — length, character set, or a prefix.

### Plain hash algorithms

| Algorithm | Output bits | Hex length | Looks like | Status |
|-----------|-------------|------------|------------|--------|
| MD5 | 128 | 32 | `5f4dcc3b5aa765d61d8327deb882cf99` | Cryptographically broken; still seen everywhere |
| SHA-1 | 160 | 40 | `5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8` | Deprecated; collisions feasible |
| SHA-224 | 224 | 56 | 56 hex chars | Uncommon |
| SHA-256 | 256 | 64 | 64 hex chars | Current default |
| SHA-384 | 384 | 96 | 96 hex chars | Less common than 256 |
| SHA-512 | 512 | 128 | 128 hex chars | Used in /etc/shadow with salt |
| SHA-3 / Keccak | 224–512 | varies | Visually like SHA-2 — distinguish by context | Modern alternative |
| BLAKE2 / BLAKE3 | 256–512 | varies | Modern, fast | Tor, IPFS, age |
| RIPEMD-160 | 160 | 40 | Looks identical to SHA-1 by length | Bitcoin addresses |
| NTLM | 128 | 32 | Identical length to MD5 | Windows account hashes |

When you see "32 hex characters" that's MD5 *or* NTLM *or* a hex-encoded message. Context (`hashes.txt`? Windows dump? CyberChef output?) decides.

### Password hash schemes (KDFs) — the prefixed ones

These are deliberately slow and salted. The format encodes the parameters:

| Scheme | Prefix | Example |
|--------|--------|---------|
| **MD5 crypt** (legacy Unix) | `$1$` | `$1$abcd1234$VKbHBHRMV.zEa0XWoBOpA1` |
| **SHA-256 crypt** | `$5$` | `$5$rounds=5000$saltsalt$...` |
| **SHA-512 crypt** (modern /etc/shadow) | `$6$` | `$6$rounds=5000$abc...$WgUOIsAhg...` |
| **bcrypt** | `$2a$`, `$2b$`, `$2y$` | `$2b$12$WnaIqyZc...m0bP/ec7G3qVa` |
| **scrypt** | `$scrypt$` or library-specific | `$scrypt$ln=15,r=8,p=1$...` |
| **Argon2** (modern recommended) | `$argon2i$`, `$argon2d$`, `$argon2id$` | `$argon2id$v=19$m=65536,t=3,p=4$salt$hash` |
| **PBKDF2** | varies (often `pbkdf2_sha256$rounds$salt$hash` in Django) | `pbkdf2_sha256$600000$abc...$xyz...` |

### Application-specific formats

- `JDoe:$DCC2$10240#username#...` — Domain Cached Credentials (Windows).
- `0x0100abcd...` — MSSQL.
- `*A4B6157319038724E3560894F7F932C8886EBFCF` — MySQL 4.1+.

The [hashcat example_hashes wiki](https://hashcat.net/wiki/doku.php?id=example_hashes) is the canonical reference. Bookmark it.

---

## Identifying a hash — the tools

```bash
sudo apt install hashid hash-identifier

hashid '5f4dcc3b5aa765d61d8327deb882cf99'
# Analyzing '5f4dcc3b5aa765d61d8327deb882cf99'
# [+] MD2
# [+] MD5
# [+] MD4
# [+] Double MD5
# [+] LM
# [+] RIPEMD-128
# [+] Haval-128
# [+] Tiger-128
# [+] Skein-256(128)
# ...
```

`hashid` returns a *list* of candidates, ranked roughly by likelihood. For 32-hex hashes that includes MD5, NTLM, and a dozen others. The order is your starting point, not the answer.

```bash
echo 'f6b0049d361b170a450d05fe75acad7b' | hashid -m
# -m flag prints hashcat mode numbers — extremely useful
# [+] MD5 [Hashcat Mode: 0]
# [+] NTLM [Hashcat Mode: 1000]
# [+] ...
```

Alternative: CyberChef → `Operations → Analyse Hash` → paste. Same info, GUI.

### Week 4 challenge — [hash-identify](../../CTFs/week-04/hash-identify/)

The challenge ships `hash.txt`:

```
f6b0049d361b170a450d05fe75acad7b
```

32 hex chars, no prefix → MD5 candidate. The hint says "MD5, rockyou or crackstation," so we proceed assuming MD5. We crack it below.

---

## Cracker landscape

Two cracking engines dominate. Both are free, both are excellent. Pick by preference.

| Tool | Strengths | When to use it |
|------|-----------|----------------|
| [`hashcat`](https://hashcat.net/) | Fastest, GPU-accelerated, supports ~500 hash modes | Anything modern, anything you'll throw a wordlist at |
| [`john`](https://www.openwall.com/john/) (John the Ripper) | Smart defaults, multi-format detection, great for mixed dumps | Quick-and-dirty cracking, weird formats hashcat doesn't have |

You will end up using both. `john` is friendlier when you're throwing a dump at it and saying "figure it out." `hashcat` is what you reach for when you know the format and want the GPU to scream.

### Modes — the integer that says "this hash type"

Hashcat enumerates modes with `-m <number>`. The common ones:

| Mode | Hash |
|------|------|
| 0 | MD5 |
| 100 | SHA-1 |
| 1400 | SHA-256 |
| 1700 | SHA-512 |
| 1000 | NTLM |
| 1800 | sha512crypt `$6$` |
| 500 | md5crypt `$1$` |
| 3200 | bcrypt `$2*$` |
| 9300 | scrypt |
| 14000 | Argon2 (recent versions) |
| 22000 | WPA/WPA2 (Wi-Fi handshakes) |

Run `hashcat --example-hashes | less` to see one example per mode — instantly useful for confirming you've picked the right `-m`.

### Attack types

| `-a` | Name | What it does |
|------|------|--------------|
| 0 | Straight | Try each line of a wordlist |
| 1 | Combination | Concatenate words from two wordlists |
| 3 | Brute-force / Mask | Try every candidate matching a pattern (e.g. all 8-char lowercase) |
| 6 | Hybrid wordlist + mask | Each word + a brute-forced suffix |
| 7 | Hybrid mask + wordlist | Brute-forced prefix + each word |

Mask charsets:

| Symbol | Charset |
|--------|---------|
| `?l` | a-z |
| `?u` | A-Z |
| `?d` | 0-9 |
| `?s` | special chars |
| `?a` | all of the above |
| `?h` / `?H` | hex lower/upper |

So `?l?l?l?l?l?l?d?d` is "six lowercase letters then two digits" (`hello42`).

---

## Cracking the Week 4 hash — full walkthrough

The Week 4 CTF [hash-identify](../../CTFs/week-04/hash-identify/) gives us `f6b0049d361b170a450d05fe75acad7b`. Plan:

1. Confirm it's MD5.
2. Throw `rockyou.txt` at it with hashcat or john.
3. Read the result.

### With hashcat

```bash
echo 'f6b0049d361b170a450d05fe75acad7b' > hash.txt

hashcat -m 0 -a 0 hash.txt /usr/share/wordlists/rockyou.txt
```

`-m 0` → MD5, `-a 0` → straight (wordlist). Hashcat shows the hash followed by `:plaintext` once it cracks (the format is `<hash>:<cracked-plaintext>` on one line). You can re-display the result without rerunning:

```bash
hashcat -m 0 hash.txt --show
```

### With john the ripper

```bash
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
john --show --format=raw-md5 hash.txt
```

Result: the same cracked plaintext.

For the CTF the flag is the cracked plaintext wrapped in the standard format — read the challenge text for what exactly to submit.

### What was `rockyou.txt`?

`rockyou.txt` is the **most famous password wordlist on the internet**. It came from a 2009 breach of the RockYou social-game platform, which stored 32 million passwords in plaintext. The list (14 million unique entries after dedup) is sorted by frequency — the first lines are `123456`, `password`, `qwerty`. It ships with Kali at `/usr/share/wordlists/rockyou.txt.gz`. Decompress before use:

```bash
sudo gunzip /usr/share/wordlists/rockyou.txt.gz
wc -l /usr/share/wordlists/rockyou.txt
# 14344392
```

Most CTF hash challenges expect `rockyou.txt` to be the wordlist. If a hash doesn't crack with `rockyou.txt`, that's already a strong hint that it's salted, slow-by-design, or requires rules/mutations.

---

## Wordlists and rules

A wordlist is just lines. The art is **mutating** lines to cover human password patterns: `Password` → `Password1`, `P@ssw0rd`, `Password!`, `password2024`, etc.

### Useful default wordlists on Kali

```bash
ls /usr/share/wordlists/
# rockyou.txt.gz                fasttrack.txt
# dirb/                          metasploit/
# dirbuster/                     nmap.lst
# rockyou.txt                    seclists/  (after `apt install seclists`)
```

[SecLists](https://github.com/danielmiessler/SecLists) is the gold-standard collection — passwords, usernames, web fuzzing payloads, all in one repo. Install it once, reuse forever:

```bash
sudo apt install seclists
ls /usr/share/seclists/Passwords/
```

### Hashcat rules

A rule is a one-line transformation. Examples from `/usr/share/hashcat/rules/best64.rule`:

| Rule | Effect |
|------|--------|
| `:` | Do nothing (keep the word as-is) |
| `l` | Lowercase |
| `u` | Uppercase |
| `c` | Capitalize |
| `r` | Reverse |
| `d` | Duplicate (`abc` → `abcabc`) |
| `$1` | Append `1` |
| `^!` | Prepend `!` |
| `sa@` | Replace `a` with `@` |

Run with `-r`:

```bash
hashcat -m 0 -a 0 hash.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

`best64.rule` (64 transformations) covers most low-effort human mutations. `dive.rule` (~99,000 rules) covers vastly more at vastly higher cost.

### John's `--rules`

John ships with similar rulesets and a slightly different syntax. Quick start:

```bash
john --wordlist=rockyou.txt --rules=Single hash.txt
john --wordlist=rockyou.txt --rules=Wordlist hash.txt
```

---

## Brute force and masks

If a wordlist won't find it, you brute force. Brute force is **only** practical for very short passwords or very narrow character sets.

```bash
# All 4-digit PINs
hashcat -m 0 -a 3 hash.txt '?d?d?d?d'

# 6-character lowercase
hashcat -m 0 -a 3 hash.txt '?l?l?l?l?l?l'

# 8-character mixed but starts with a capital
hashcat -m 0 -a 3 hash.txt '?u?l?l?l?l?l?l?l'

# Hybrid: rockyou + 2-digit suffix
hashcat -m 0 -a 6 hash.txt rockyou.txt '?d?d'
```

### Keyspace and runtime

A useful back-of-envelope:

```
keyspace = (charset size) ^ length
runtime  = keyspace / rate
```

| Hash | GPU rate (RTX 3060, ballpark) | 8-char lowercase (26^8 ≈ 2×10¹¹) |
|------|-------------------------------|----------------------------------|
| MD5 | ~5 GH/s | ~40 seconds |
| SHA-256 | ~1.5 GH/s | ~2 minutes |
| NTLM | ~30 GH/s | ~7 seconds |
| bcrypt cost 12 | ~5 kH/s | ~1300 years |
| Argon2id (m=65536,t=3,p=4) | ~1 kH/s | ~6500 years |

Notice the gap. MD5 falls in seconds. Bcrypt at default cost is effectively uncrackable for 8-char random passwords. **This is the entire point of password hashes** — they're slow on purpose.

> **CTF tip.** If your hashcat run is showing speeds in the **kH/s** range (kilo-hashes per second) you're either on a CPU, in a VM without GPU passthrough, or attacking a deliberately slow KDF. Read the next section for the VM-specific caveat.

---

## Hashcat in a VM — the reality check

If you're running Kali inside VirtualBox / VMware / Hyper-V on a laptop, **hashcat does not have access to your GPU by default**. It falls back to CPU mode, which is 10–100x slower than native GPU.

Symptoms:

```
hashcat (v6.x.x) starting
* Device #1: CPU @ ...
* Device #2: not detected
```

Two paths:

| Option | Notes |
|--------|-------|
| Use hashcat on the **host** OS (Windows, macOS, native Linux) directly | Fastest. Install hashcat outside the VM. |
| Configure GPU passthrough (PCIe passthrough on Linux KVM, GPU paravirtualization on Hyper-V) | Possible but fiddly. Not worth the time for CTF-scale hashes. |
| Run on a cloud GPU (Lambda, Vast.ai, Colab) for big jobs | Overkill for course work; useful for serious cracking |

For CSOT's MD5 challenge, CPU mode is plenty. For anything bcrypt-scale you'd be measuring in days regardless.

```bash
hashcat -m 0 -a 0 hash.txt rockyou.txt -D 1
# -D 1 = force CPU device (silences warnings, doesn't change speed materially)
```

> **Gotcha.** `hashcat` requires the OpenCL runtime even on CPU. On a clean Kali install: `sudo apt install pocl-opencl-icd` if hashcat complains "no devices found."

---

## Salts and why they matter

A **salt** is a unique random value mixed into the hash, stored alongside it:

```
hash = H(password || salt)
```

Two passwords now produce different hashes even if the plaintext is identical. This kills two attack techniques at once:

| Attack | Why salt defeats it |
|--------|---------------------|
| **Rainbow table** lookup | Precomputed tables only work for unsalted hashes; salts make precomputation per-user |
| **Cracking one hash cracks N** | Without salt, every user with the same password shares a hash — crack once, unlock many |

Salts must be **per-user and random**. Reusing a single global salt brings rainbow tables back.

### Where salts live in modern formats

In `$2b$12$WnaIqyZc...m0bP/ec7G3qVa`:

- `$2b$` — algorithm (bcrypt v2b)
- `$12$` — cost factor (2¹² = 4096 rounds)
- The next 22 characters — base64-encoded 16-byte salt
- The rest — base64-encoded 23-byte hash output

Hashcat parses this automatically — give it the whole string.

---

## Rainbow tables — historical context

A rainbow table is a precomputed mapping from common hashes back to passwords. Pre-cloud-GPU era (early 2000s), they were the dominant attack against unsalted MD5 / SHA-1 / NTLM. Today, **GPUs crack faster than rainbow tables look up**, and salts neutralize them anyway. Mostly historical.

[CrackStation](https://crackstation.net/) is the modern descendant — a hosted lookup that has indexed ~190 GB of cracked hashes. Useful for instant lookups of *unsalted* hashes from public dumps. Do not paste private hashes into it.

---

## Online lookups vs offline cracking

| Service | What it does | Safe to use for |
|---------|--------------|-----------------|
| [CrackStation](https://crackstation.net/) | Looks up unsalted MD5/SHA-1/NTLM against indexed cracks | CTF hashes only; never private data |
| [HashKiller](https://hashkiller.io/) | Similar | CTF only |
| [hashes.com](https://hashes.com/) | Forum-based bulk cracking community | CTF only |
| [Hashcat Wiki — example_hashes](https://hashcat.net/wiki/doku.php?id=example_hashes) | Test hashes for every mode | Anything |

For the [hash-identify](../../CTFs/week-04/hash-identify/) challenge, CrackStation returns the plaintext in 200 ms — faster than your hashcat run. But the goal of the module is to know how to crack it yourself.

---

## Password hashes done right — for the defender side

When you store passwords in your own apps, use:

| Choice | Why |
|--------|-----|
| **Argon2id** | OWASP's current recommendation; memory-hard, GPU-resistant |
| **scrypt** | Older but still recommended; memory-hard |
| **bcrypt cost ≥ 12** | Battle-tested; not memory-hard but plenty slow |
| **PBKDF2-HMAC-SHA256 with ≥ 600,000 iterations** | When the platform forces it (FIPS, older libraries) |

Avoid:

| Don't | Why |
|-------|-----|
| Plain `sha256(password)` | Tens of GH/s on a GPU; cracked in minutes |
| `md5(password)` | Same, only worse |
| `sha256(password + global_salt)` | A single salt is no salt; rainbow tables apply per-user |
| `bcrypt cost ≤ 10` | Cheap on modern hardware |
| Implementing it yourself | Use a library: Argon2 via `argon2-cffi`, bcrypt via `bcrypt`, both via `passlib` |

```python
from argon2 import PasswordHasher

ph = PasswordHasher()
stored = ph.hash("correct horse battery staple")
ph.verify(stored, "correct horse battery staple")  # ok
ph.verify(stored, "wrong")                          # argon2.exceptions.VerifyMismatchError
```

If you remember nothing else: **a hash for fingerprinting (file checksums, content addressing) is fast on purpose; a hash for passwords is slow on purpose.** Same word, opposite goals.

---

## Identifying tricky hashes — flowchart

```
length in hex?
 ├── 32  → MD5? NTLM? hex-encoded message? — try hashid
 ├── 40  → SHA-1? RIPEMD-160? — try hashid
 ├── 64  → SHA-256? — almost always yes
 ├── 128 → SHA-512? — almost always yes
 └── other → it has a prefix
              └── $2[aby]$  → bcrypt   (-m 3200)
              └── $1$       → md5crypt (-m 500)
              └── $5$       → sha256crypt (-m 7400)
              └── $6$       → sha512crypt (-m 1800)
              └── $argon2*$ → argon2  (-m 14000)
              └── $scrypt$  → scrypt  (-m 9300)
              └── pbkdf2_*  → look up mode for the framework
```

If nothing matches, run `hashid -m` and pick the most likely.

---

## End-to-end CTF workflow

For any "here's a hash" challenge:

```bash
# 1. Inspect — what is it?
file hash.txt
cat hash.txt
hashid -m "$(cat hash.txt)"

# 2. Pick the hashcat mode (or john format) from the hashid output.

# 3. First try: wordlist alone.
hashcat -m <mode> -a 0 hash.txt /usr/share/wordlists/rockyou.txt

# 4. If that misses, add common rules.
hashcat -m <mode> -a 0 hash.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# 5. If still missing, try hybrid (wordlist + 2-digit suffix is very common).
hashcat -m <mode> -a 6 hash.txt rockyou.txt '?d?d'

# 6. If all of the above miss, it's either deliberately hard or salted with an
#    unknown salt format. Re-read the challenge prompt for hints.

# 7. View results any time:
hashcat -m <mode> hash.txt --show
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Token length exception` | Hash format is wrong for the mode; re-check `hashid` and the example hashes wiki |
| `No devices found` | Install `pocl-opencl-icd` (for CPU OpenCL) on Kali, or move off the VM |
| Speeds in `kH/s` not `GH/s` | CPU mode in VM — expected. Don't try to brute-force bcrypt this way. |
| Hashcat says `Cracked` but `--show` is empty | Specify the same mode (`-m N`) for `--show` |
| Wordlist not found | `sudo gunzip /usr/share/wordlists/rockyou.txt.gz` |
| `Self-test failed` on Kali | Install latest hashcat from upstream; the apt version may lag |
| `john` says "no password hashes loaded" | Wrong `--format=`; run `john --list=formats | grep -i md5` |

---

## Tooling summary

| Tool | Purpose |
|------|---------|
| `hashid`, `hash-identifier` | Identify hash family |
| `hashcat` | The cracker for hashes you know the type of |
| `john` (John the Ripper) | The cracker for hashes you don't, or for legacy formats |
| `mkpasswd` | Generate test hashes (`mkpasswd -m sha-512 password`) |
| `openssl passwd` | Same, in `openssl` form (`openssl passwd -6 password`) |
| [hashcat-rules](https://github.com/hashcat/hashcat/tree/master/rules) | Built-in rulesets ship with hashcat |
| [SecLists](https://github.com/danielmiessler/SecLists) | Wordlist mega-pack |
| [Pwned Passwords](https://haveibeenpwned.com/Passwords) | Look up if a password (or its SHA-1 prefix) is in known breaches |

---

## Further reading

- [Hashcat wiki — example_hashes](https://hashcat.net/wiki/doku.php?id=example_hashes) — one row per mode; bookmark.
- [OWASP — Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) — what to actually do server-side.
- [Argon2 RFC 9106](https://datatracker.ietf.org/doc/html/rfc9106) — the modern recommendation.
- [Troy Hunt — Have I Been Pwned blog](https://www.troyhunt.com/) — practical password-handling case studies.
- [Hashcat user manual](https://hashcat.net/wiki/doku.php?id=hashcat) — every flag explained.

---

## Next module

[steganography.md](steganography.md) — From "data is hidden by being unreadable" to "data is hidden by being invisible." Different attacker, different tools, same hunt.
