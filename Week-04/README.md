# Week 4 — Cryptography, steganography & forensics

Last week you broke open web applications. This week you change posture entirely: instead of attacking running services, you analyse **artifacts**. A blob of ciphertext, a suspicious PNG, a packet capture from someone else's network, a hash dump, a repo full of "deleted" secrets. The categories you'll be working in — Crypto, Stego, Forensics — are the staple of every CTF beginner board and the daily bread of incident-response teams in industry.

By the end of the week you'll be able to recognise a classical cipher in 30 seconds, break a weak RSA modulus with three lines of Python, crack an MD5 hash with `hashcat`, find data hidden inside an image with `binwalk` and `zsteg`, read a PCAP in Wireshark, recover deleted secrets from Git history, and articulate why every one of those operations is legal only on artifacts you own or have written authorization to touch.

---

## Why this week matters

Three reasons:

1. **CTF coverage.** Almost every public CTF — picoCTF, HackTheBox, every CTFtime event — has Crypto / Stego / Forensics tracks. They're cheap to set up (no live infrastructure needed), they teach concrete skills, and they're how most people score their first hundred points.
2. **Real-world breach patterns.** When something goes wrong at a real company, the analysis loop looks exactly like Week 4. "Open this file. What is it? What's inside it? Who put it there? What happened next?" — every forensic engagement is a stack of those questions. Every secret-leak postmortem starts with `git log --all`.
3. **It builds the right reflexes for the rest of your career.** `file` before you trust an extension. `strings` before you trust an analysis tool. Hash before you trust a copy. Rotate first, scrub second when a secret leaks. These habits compound.

You'll re-use Week 1's CLI muscles (grep, find, awk, pipes), Week 2's recon mindset (iterate, pivot, verify), and Week 3's vulnerability instincts (think about misuse, not algorithms). Week 4 brings them together on artifact analysis.

---

## Learning objectives

By the end of this week, you should be able to:

- [ ] Distinguish encoding (Base64, hex, URL) from encryption, and chain-decode multi-layered encodings
- [ ] Recognise and break classical ciphers — Caesar/ROT, Vigenère, Atbash, substitution, transposition
- [ ] Explain what makes the one-time pad unbreakable, and why key reuse destroys that guarantee
- [ ] Describe symmetric vs asymmetric crypto and the role of AES, RSA, ECC, DH at a high level
- [ ] Identify why AES-ECB leaks structure, why AES-GCM is the modern default, and what "AEAD" means
- [ ] Spot CTF-grade RSA weaknesses (small `n`, small `e` without padding, shared primes) and exploit them
- [ ] Brute-force a single-byte XOR cipher and explain the multi-byte XOR attack
- [ ] Identify common hash algorithms by length and prefix, including modern password-hash schemes
- [ ] Use `hashid`, `hashcat`, and `john` to crack lab hashes with wordlists, rules, and masks
- [ ] Articulate why bcrypt/scrypt/Argon2 are slow on purpose and how that defeats GPU brute force
- [ ] Identify file types by magic byte and bypass extension-based assumptions
- [ ] Use `exiftool`, `strings`, `binwalk`, `foremost`, `zsteg`, and `steghide` to extract hidden data
- [ ] Read a PCAP with Wireshark / `tshark` and pull HTTP, DNS, and credentials from cleartext protocols
- [ ] Carve files out of disk images and document the chain-of-custody steps that make findings defensible
- [ ] Find leaked secrets in Git history, rewrite history safely, and explain why rotation must come first
- [ ] Run `trufflehog` / `gitleaks` on a repository and wire `pre-commit` to block future leaks
- [ ] Articulate the legal and ethical boundaries of hash-cracking, stego analysis, and secret-hunting

---

## Modules (read in order)

Each module builds on the previous one. Start with the conceptual crypto material, layer on attacker tooling, finish with the forensics + secret-handling discipline.

| # | Module | What you'll learn | Time estimate |
|---|--------|-------------------|---------------|
| 1 | [classical-crypto.md](classical-crypto.md) | Encodings vs encryption, Caesar/ROT-N, Vigenère with Kasiski + IoC, substitution, transposition, one-time pad, XOR teaser | 45 min |
| 2 | [modern-crypto.md](modern-crypto.md) | Symmetric vs asymmetric, AES modes (ECB/CBC/CTR/GCM), RSA with weak-instance attacks, ECC + DH overview, hashing vs encryption, openssl cheat sheet | 55 min |
| 3 | [hash-cracking.md](hash-cracking.md) | Hash family fingerprints, `hashid`, hashcat modes/attacks/rules/masks, `john`, rockyou, salts, why bcrypt/Argon2 exist | 50 min |
| 4 | [steganography.md](steganography.md) | File-magic table, exiftool / strings / binwalk / zsteg / steghide workflow, LSB encoding, audio spectrograms, polyglots, file carving | 40 min |
| 5 | [digital-forensics.md](digital-forensics.md) | Magic-byte table, foremost / bulk_extractor, log triage, PCAP analysis with Wireshark / tshark, disk imaging with dd/dcfldd, memory forensics overview, chain of custody | 55 min |
| 6 | [secrets-in-repos.md](secrets-in-repos.md) | Git data model, manual archaeology, trufflehog / gitleaks, removing secrets with `git filter-repo`, rotate-first incident response, pre-commit hygiene | 45 min |

**Total reading time:** ~4.5 – 5 hours (spread across Mon–Wed)

---

## Recommended workflow

```
Day 1 (Mon):  Modules 1–2 (classical + modern crypto)
              + work through Cryptohack "Introduction" + "General"
Day 2 (Tue):  Module 3 (hash-cracking)
              + install hashcat/john; run example_hashes for each mode
Day 3 (Wed):  Modules 4–5 (steganography + forensics)
              + install binwalk, zsteg, steghide, foremost, Wireshark
Day 4 (Thu):  Module 6 (secrets-in-repos) + assignments
              + set up gitleaks/pre-commit on your own repos
Day 5 (Fri):  Polish assignments, review CTF hints, fill in any gaps
Day 6–7:      Weekend CTF (10 challenges, 3–4 hours)
```

---

## External practice platforms

Do these in parallel with the reading — they reinforce exactly what each module covers.

| Platform | What to do | Link |
|----------|------------|------|
| CryptoHack | "Introduction to CryptoHack" + "General" + "Mathematics" + "RSA Starter" tracks | [cryptohack.org](https://cryptohack.org/) |
| OverTheWire | Krypton wargame (levels 0–6) — Caesar, Vigenère, OTP, substitution | [overthewire.org/wargames/krypton/](https://overthewire.org/wargames/krypton/) |
| picoCTF Gym | Cryptography category + Forensics category | [play.picoctf.org/practice](https://play.picoctf.org/practice) |
| TryHackMe | "Crack the hash", "Hashing - Crypto 101", "Encryption - Crypto 101" | [tryhackme.com](https://tryhackme.com/) |
| TryHackMe | "Wireshark 101", "Volatility", "Disk Analysis & Autopsy" | [tryhackme.com](https://tryhackme.com/) |
| TryHackMe | "c4ptur3-th3-fl4g" — broad encoding + stego practice | [tryhackme.com](https://tryhackme.com/) |
| HackTheBox | Crypto + Forensics challenge categories (start with "Very Easy" and "Easy") | [hackthebox.com](https://www.hackthebox.com/) |
| Cryptopals | Sets 1 and 2 — XOR / single-byte attacks / AES-ECB / CBC | [cryptopals.com](https://cryptopals.com/) |
| CyberDefenders | Forensics labs with real-world incident scenarios | [cyberdefenders.org](https://cyberdefenders.org/) |
| CTFlearn | Forensics + Crypto beginner-friendly puzzles with hints | [ctflearn.com](https://ctflearn.com/) |

---

## Tooling check

Confirm these are installed and working on your Kali / WSL / VM:

```bash
# Crypto + hash
sudo apt install -y hashid hash-identifier hashcat john openssl python3-cryptography
sudo gunzip /usr/share/wordlists/rockyou.txt.gz   # one-time

# Steganography
sudo apt install -y binwalk foremost steghide outguess exiftool
sudo gem install zsteg

# Forensics
sudo apt install -y wireshark tshark tcpdump bulk-extractor sleuthkit dcfldd sonic-visualiser audacity

# Secrets-in-repos
sudo apt install -y git-filter-repo pre-commit
go install github.com/trufflesecurity/trufflehog/v3@latest
go install github.com/gitleaks/gitleaks/v8@latest

# Optional but nice
sudo apt install -y seclists
```

If `hashcat` complains about devices in your VM, install `pocl-opencl-icd`. If `wireshark` won't capture, add yourself to the `wireshark` group with `sudo dpkg-reconfigure wireshark-common`.

---

## Assignments (practice — not scored)

Use these to practice crypto and forensics workflows before the weekend CTF. **Only CTF flags are scored.**

1. **Crypto write-up.** Pick three of the Week 4 crypto challenges (`caesar-shift`, `encoding-chain`, `vigenere-notes`, `xor-single-byte`, `weak-rsa-mini`) and write a one-page solution per challenge. Include: what you observed, what tool/technique you tried first, what worked, and a `bash`/`python3` snippet that reproduces the solve. Include the recovered flags.

2. **Hash-crack lab.** Generate three of your own MD5 / SHA-1 / SHA-256 hashes from words you pick (one from rockyou, one not, one with a number/symbol suffix), save them to `hashes.txt`, then write a single `hashcat` (or `john`) command line per hash that recovers each plaintext. Include the timings. *Only crack hashes you generated.*

3. **Forensics report on the lab artifacts.** Pick at least three of the Week 4 forensics/stego challenges (`hidden-png`, `metadata-leak`, `carved-note`, `pcap-cleartext`, `hash-identify`) and produce a single Markdown report walking through your analysis. Use the disciplined workflow from [digital-forensics.md](digital-forensics.md): `file` → metadata → strings → carving → specialised tool. Document each step.

4. **Self secret-scan.** Run `trufflehog --only-verified` on every public repo under your GitHub username and note whether you found anything (and rotated if so). Also install `pre-commit` with the `gitleaks` hook on your CSOT working repo so you can't accidentally commit secrets going forward.

---

## Weekend CTF

**Location:** [../../CTFs/week-04/](../../CTFs/week-04/)
**Challenges:** 10 — crypto, steganography, forensics, hash-cracking
**Duration:** 3–4 hours
**Format:** Jeopardy-style, individual
**Flag format:** `csot26{...}`

| Challenge | Category | Points | Skills tested |
|-----------|----------|--------|---------------|
| [caesar-shift](../../CTFs/week-04/caesar-shift/) | Crypto | 100 | ROT13 / Caesar shift — `tr` or CyberChef |
| [encoding-chain](../../CTFs/week-04/encoding-chain/) | Crypto | 150 | Recognise Base64 → hex chained encoding |
| [metadata-leak](../../CTFs/week-04/metadata-leak/) | Stego | 150 | Read metadata / EXIF comment |
| [hidden-png](../../CTFs/week-04/hidden-png/) | Stego | 200 | `file` + `strings`; recognise format mismatch |
| [hash-identify](../../CTFs/week-04/hash-identify/) | Forensics | 200 | `hashid` + `hashcat`/`john` with rockyou |
| [vigenere-notes](../../CTFs/week-04/vigenere-notes/) | Crypto | 200 | Vigenère decryption with given key |
| [xor-single-byte](../../CTFs/week-04/xor-single-byte/) | Crypto | 200 | Brute-force 256 keys, look for `csot26{` |
| [carved-note](../../CTFs/week-04/carved-note/) | Forensics | 250 | `strings`/`foremost`/`binwalk` carving |
| [pcap-cleartext](../../CTFs/week-04/pcap-cleartext/) | Forensics | 250 | Read HTTP traffic; `grep`/`tshark` |
| [weak-rsa-mini](../../CTFs/week-04/weak-rsa-mini/) | Crypto | 300 | Factor tiny `n`, recover `d`, decrypt `c` |

**Total available:** 2000 points

**Tips for success:**
- Read each challenge's `README.md` carefully — descriptions contain hints, and the `<details>` blocks contain explicit clues.
- Run `file` on every artifact before assuming the extension is honest.
- For anything that *looks* like encoded text, paste it into CyberChef's Magic operator first.
- For any hash challenge, `hashid -m hash.txt` gives you the right hashcat mode in one step.
- The flag format is always `csot26{...}` — `grep -r 'csot26{' .` on extracted directories ends many challenges.

---

## Key concepts to remember

| Concept | Why it matters this week |
|---------|--------------------------|
| Encoding vs encryption | If there's no key, it's encoding. `base64 -d` is not "decryption." |
| `file` over filename | Magic bytes don't lie; extensions do |
| ECB leaks structure | "Same plaintext block → same ciphertext block" — never use ECB |
| Key reuse | Two messages, one XOR key, you can recover both — same lesson from OTP to AES-CTR |
| Tiny RSA `n` | If `n` is under 2048 bits, factor it; under 256 bits is trivial |
| `hashid -m` | One command, get the hashcat mode number |
| Slow hashes on purpose | bcrypt/scrypt/Argon2 are slow so attackers can't brute force; that's the feature |
| LSB needs lossless | PNG/BMP/WAV preserve LSB; JPEG/MP3 destroy it |
| `binwalk -e` | One-shot extract of embedded files |
| Wireshark "Follow Stream" | Reassembles a TCP conversation as readable text in two clicks |
| Hash before, hash after | Forensic integrity = "the SHA didn't change while I was looking" |
| Rotate first, scrub second | A leaked secret stays compromised even after `git filter-repo` |
| `git log --all` | History is a DAG, not a list — "deleted" commits are still reachable |
| Authorization first | Same rule, every week: legal == lab + your stuff + written permission |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `hashcat` reports `No devices found` | `sudo apt install pocl-opencl-icd` for CPU OpenCL on Kali |
| Hashcat speeds in `kH/s` instead of `GH/s` | You're on CPU (likely a VM without GPU passthrough); expected for VM-based labs |
| `rockyou.txt` missing | `sudo gunzip /usr/share/wordlists/rockyou.txt.gz` (one-time) |
| `openssl enc` decryption gives "bad magic" | OpenSSL 3.x changed defaults; try with `-md md5 -pbkdf2` flags to match old behaviour |
| `binwalk` reports tons of false positives | Many compressed/random-looking files produce signature hits; trust `binwalk -e` output only when files extract successfully |
| `binwalk -e` extracts nothing | Tool wasn't sure of the format; try `foremost -i file` instead |
| Wireshark capture interfaces blank | `sudo dpkg-reconfigure wireshark-common`, add yourself to `wireshark` group, re-login |
| `zsteg` not found | `sudo apt install ruby-dev && sudo gem install zsteg` |
| `steghide` says "could not extract any data" | Wrong passphrase, or the file doesn't contain steghide data — try `outguess` or `zsteg` for PNG/BMP |
| `trufflehog` reports many "unverified" hits | Use `--only-verified` — verified-live credentials only |
| `git filter-repo` refuses to run | "Working dir not clean" — commit or stash; "fresh clone needed" — `git clone --mirror` for repos with reflogs |
| Force-push rejected after history rewrite | Repo has branch protection; coordinate with the team or temporarily unblock |
| `factordb` says `n` is "unknown" | RSA modulus is larger than the cached set — try `yafu factor` locally for moduli up to ~512 bits |
| CyberChef Magic operator misses something | Bump the depth setting; or chain the operations manually based on what you suspect |

---

## Advanced Reading

For those who want to go deeper this week:

### Books

- *Serious Cryptography* — Jean-Philippe Aumasson — modern crypto for practitioners
- *Applied Cryptography* — Bruce Schneier — reference (dense; skim by topic)
- *File System Forensic Analysis* — Brian Carrier — deep forensics (optional)

### Online courses / paths

- [Cryptohack](https://cryptohack.org/) — all tracks beyond RSA Starter
- [Cryptopals](https://cryptopals.com/) — sets 3–8 (block ciphers, padding oracles, CBC)
- [CyberDefenders](https://cyberdefenders.org/) — blue-team forensics labs

### Tools to explore

- [SageMath](https://www.sagemath.org/) — mathematical crypto attacks
- [z3](https://github.com/Z3Prover/z3) — SMT solver for constraint challenges
- [Volatility 3](https://github.com/volatilityfoundation/volatility3) — memory forensics (preview for IR)

### Challenge platforms

- [Mystery Twister](https://www.mysterytwister.org/) — crypto puzzles
- [Lattice Challenge](https://latticechallenge.org/) — advanced lattice crypto
- [CTFlearn — Forensics](https://ctflearn.com/)

### Videos / creators

- [LiveOverflow](https://www.youtube.com/c/LiveOverflow) — crypto and CTF math explained visually
- [Computerphile](https://www.youtube.com/user/Computerphile) — conceptual crypto primers

---

## What's next

Week 5 takes the forensics + crypto mindset and points it at exploitation: privilege escalation, reverse engineering, binary exploitation, post-exploitation, and incident response. The cryptographic primitives you saw here (hashes, JWTs, weak RSA) reappear as **attack surfaces** — most modern privesc paths involve a weak credential or a misused signature somewhere along the chain. The forensic discipline you built (artifact analysis, chain of custody) becomes the **blue-team mirror** of those same techniques.

**Next:** [Week 5 — Systems security, reverse engineering, binary exploitation & capstone](../Week-05/)
