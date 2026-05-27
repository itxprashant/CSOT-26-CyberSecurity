# Modern cryptography

Classical crypto teaches you the words: key, plaintext, ciphertext, attack model, brute force. Modern crypto is what actually protects your bank login, your Signal messages, the TLS handshake to GitHub. It rests on **hard math problems** (factoring, discrete logarithms, lattice problems) and on **bit-level operations** done at speeds that make brute force absurd.

You don't need to invent crypto. You need to recognize the building blocks, know which combinations are safe vs broken, and understand how each piece breaks when misused — because CTFs hand you the broken versions deliberately. By the end of this module you should be able to look at a CTF challenge and say "OK, that's AES in ECB mode, here's the leak" or "small `e`, no padding, try the cube-root attack."

---

## Why this module matters

Three reasons:

1. **You will see all of this in real code.** Every backend you build calls `cryptography.fernet` or `openssl` or `crypto.subtle`. Misusing any of them silently breaks security. The most expensive crypto bugs in the wild — Heartbleed, Cloudbleed, ROCA, every nonce-reuse in TLS implementations — are misuse, not algorithm breaks.
2. **CTF cryptography is mostly misuse.** Challenges almost never give you raw AES to break — that's an open research problem. Instead they hand you AES-ECB on a known-plaintext, RSA with a tiny modulus, XOR with a reused pad. You're meant to spot the misuse.
3. **It builds the right vocabulary for the rest of the course.** Week 5 (exploitation) leans on signatures and HMACs. The forensics module talks about file hashes. Knowing what `SHA-256` vs `HMAC-SHA-256` vs `bcrypt` means saves you from chasing the wrong attack.

---

## The big picture — three families

Modern crypto splits cleanly into three families based on **how many parties hold the secret**.

| Family | Who has the secret | Speed | Typical use |
|--------|---------------------|-------|-------------|
| **Symmetric (secret-key)** | Both sides share the same key | Very fast (GB/s) | Bulk data encryption: TLS records, disk, files |
| **Asymmetric (public-key)** | One side has private key; the world has the public key | Slow (KB/s) | Key exchange, digital signatures, identity |
| **Hashing (no key, one-way)** | No secret | Very fast | Integrity, fingerprints, password storage (with a KDF) |

Almost every real protocol uses all three: asymmetric to agree on a session key, symmetric to encrypt the actual data, hashing to verify integrity. TLS, SSH, Signal, WireGuard — same pattern every time.

We cover symmetric first because the concepts are smaller.

---

## Symmetric encryption

The same key encrypts and decrypts. Two sub-types:

| Type | Operates on | Notable algorithms |
|------|-------------|--------------------|
| **Block cipher** | Fixed-size blocks (16 bytes for AES) | AES, 3DES (legacy), Blowfish (legacy) |
| **Stream cipher** | One byte/bit at a time, using a keystream | ChaCha20, RC4 (broken), Salsa20 |

Block ciphers are the modern default — but a block cipher alone only knows how to encrypt one block. To encrypt more than 16 bytes, you need a **mode of operation** that chains blocks together. The mode matters more than the cipher.

### AES — the workhorse

**AES (Advanced Encryption Standard)** has been the standard since 2001. Key sizes: 128, 192, 256 bits. There's no practical attack on AES itself — the misuse is always in the mode or the key handling.

```bash
openssl enc -aes-256-cbc -salt -in plain.txt -out cipher.bin -pbkdf2
openssl enc -d -aes-256-cbc -in cipher.bin -out plain.txt -pbkdf2
```

`openssl` prompts for a password and derives the key with PBKDF2 (a slow KDF — covered in [hash-cracking.md](hash-cracking.md)).

### Modes of operation — pick carefully

| Mode | Full name | Properties | When to use |
|------|-----------|------------|-------------|
| **ECB** | Electronic Codebook | Each block encrypted independently. **Identical plaintext blocks → identical ciphertext blocks.** Leaks structure. | Never. |
| **CBC** | Cipher Block Chaining | Each block XORed with previous ciphertext before encryption. Needs IV. Vulnerable to padding-oracle attacks if you also expose padding errors. | Legacy. Avoid in new code. |
| **CTR** | Counter | Turns block cipher into stream cipher by encrypting a counter. **Nonce reuse breaks everything.** | When you must, and you can guarantee unique nonces. |
| **GCM** | Galois/Counter Mode | CTR + an authentication tag. **Authenticated encryption.** Detects tampering. | Default modern choice. |

### Why ECB is dangerous — the Linux penguin

The textbook demonstration: take a BMP image of the Linux mascot Tux, encrypt the pixel data with AES-ECB. The result is still recognizably Tux. Why? Because identical 16-byte plaintext blocks (large flat-colour regions) encrypt to identical 16-byte ciphertext blocks. The shape leaks even though every block is "encrypted."

ASCII version of the same idea:

```
Plaintext:           AES-ECB ciphertext:
##########            ●●●●●●●●●●
##########            ●●●●●●●●●●        same plaintext block →
####  ####            ●●●●  ●●●●        same ciphertext block →
##########            ●●●●●●●●●●        the outline of the image
##########            ●●●●●●●●●●        is preserved
```

You can find the actual Tux image with a quick web search ("ECB penguin"). Once seen, never forgotten.

> **CTF tip.** If you see ciphertext where the *same chunk repeats* at regular 16-byte boundaries, the mode is ECB. Encryption by 16-byte blocks of repeating data is a giveaway. Try a chosen-plaintext attack: submit known data through the encryption oracle, line up your input against the output, and you can usually decrypt one byte at a time. This is the classic "ECB byte-at-a-time" attack covered in [Cryptopals set 2](https://cryptopals.com/sets/2).

### CTR mode and nonce reuse

CTR mode encrypts `counter` and XORs the result with the plaintext to produce ciphertext. The counter is built from a **nonce + counter index** — the nonce must be unique per message.

If you use the same nonce twice with the same key:

```
C1 = M1 ⊕ AES_K(nonce || 0)
C2 = M2 ⊕ AES_K(nonce || 0)
C1 ⊕ C2 = M1 ⊕ M2          (the keystream cancels — same disaster as OTP key reuse)
```

This is the same XOR-key-reuse failure from [classical-crypto.md](classical-crypto.md), scaled up. The cipher is "modern," the mistake is ancient.

### Authenticated encryption (AEAD) — what to actually use

For new code, the only sane default is an **AEAD** mode like AES-GCM or ChaCha20-Poly1305. AEAD gives you:

- **Confidentiality** (encryption).
- **Integrity + authenticity** (a tag that fails if the ciphertext is modified).

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = AESGCM.generate_key(bit_length=256)
aes = AESGCM(key)
nonce = os.urandom(12)               # unique per message
ct = aes.encrypt(nonce, b"hello", associated_data=b"v1")
pt = aes.decrypt(nonce, ct, associated_data=b"v1")
```

If anyone flips a single bit of `ct`, `decrypt` raises an exception. That's the property you want.

### ChaCha20

ChaCha20-Poly1305 is the modern stream-cipher AEAD. Used in TLS 1.3, WireGuard, Signal. Operates on 64-byte blocks of a state, no S-boxes (constant-time in software), faster than AES on CPUs without AES-NI (mobile, ARM).

You don't usually choose between AES-GCM and ChaCha20-Poly1305 — the protocol picks one. Both are safe.

---

## XOR — the smallest stream cipher

XOR a single byte against your message and you have the world's worst stream cipher. CTFs love it.

The hex blob in [../../CTFs/week-04/xor-single-byte/](../../CTFs/week-04/xor-single-byte/) is exactly this. Strategy:

1. There are only 256 possible keys.
2. Brute force all of them.
3. Pick the result that looks like English (or starts with `csot26{`).

Solution:

```python
ciphertext = bytes.fromhex("21312d367074393a2d301d203b3627352b31273f")
for key in range(256):
    pt = bytes(b ^ key for b in ciphertext)
    if pt.startswith(b"csot26{"):
        print(f"key=0x{key:02x}", pt.decode())
```

Output:

```
key=0x42 csot26{xor_bytewise}
```

> **CTF tip.** For a slightly harder version with a multi-byte repeating XOR key, the trick is to: (1) guess the key length (look for repeated patterns at distance N), (2) treat each byte position modulo N as a single-byte XOR, (3) frequency-analyze each subgroup. This is "Vigenère's revenge" — same technique you learned for Vigenère, applied to bytes instead of letters.

### Why even repeating XOR fails

Real stream ciphers like ChaCha20 generate a keystream that is **indistinguishable from random** for any practical attacker. Repeating XOR generates a keystream that is *visibly* periodic. Frequency in the plaintext (ASCII text has heavy bias towards bytes 0x20–0x7E) bleeds through the periodicity and reveals the key.

The lesson — **never roll your own stream cipher**.

---

## Asymmetric encryption

Two keys: a **public key** anyone can have, and a **private key** you guard. Anything encrypted with the public key only the private key can decrypt; anything signed with the private key anyone can verify with the public key.

This solves the *key distribution* problem: you can publish your public key on Twitter, and a stranger can encrypt a message that only you can read.

| Algorithm | Hard problem | Typical use |
|-----------|--------------|-------------|
| **RSA** | Factoring large semiprimes | Encryption, signing, key transport |
| **DH / DHE** | Discrete log mod prime | Key agreement |
| **ECDH** | Discrete log on elliptic curve | Key agreement (modern TLS) |
| **ECDSA / Ed25519** | Discrete log on elliptic curve | Signing |

### RSA — the canonical asymmetric algorithm

The setup:

1. Pick two large random primes `p` and `q`.
2. Compute `n = p * q` (the **modulus**).
3. Compute `φ(n) = (p-1)(q-1)`.
4. Pick a public exponent `e` (commonly 65537).
5. Compute `d` such that `e * d ≡ 1 (mod φ(n))`.

Public key: `(n, e)`. Private key: `(n, d)`. Or all of `(p, q, d)`.

To encrypt a message `m`:

```
c = m^e mod n
```

To decrypt:

```
m = c^d mod n
```

The security rests on this fact: given only `n` and `e`, recovering `d` requires factoring `n = p * q`. For `n` of 2048 bits with random primes, that's the hardest known computational problem.

### RSA in practice — `openssl`

```bash
openssl genrsa -out priv.pem 2048
openssl rsa -in priv.pem -pubout -out pub.pem

openssl rsautl -encrypt -inkey pub.pem -pubin -in msg.txt -out msg.enc
openssl rsautl -decrypt -inkey priv.pem -in msg.enc -out msg.txt
```

In real systems RSA encrypts a **session key**, not data — it's far too slow for bulk traffic.

### When RSA breaks (CTF flavours)

| Mistake | Why it breaks | Tooling |
|---------|---------------|---------|
| `n` is small (under ~256 bits) | Factor with general-purpose tools | [factordb.com](http://factordb.com/), `yafu`, SageMath |
| `n` reused across messages with different `e` | Common-modulus attack | Bezout's identity |
| `e = 3` and no padding | Cube-root attack when `m^3 < n` | `gmpy2.iroot(c, 3)` |
| Two `n`s share a prime | `gcd(n1, n2)` reveals it instantly | `math.gcd` |
| `m` is small relative to `n` | Brute force or coppersmith | sage |
| `p` and `q` are too close | Fermat factorization | Python loop |

CSOT [../../CTFs/week-04/weak-rsa-mini/](../../CTFs/week-04/weak-rsa-mini/) is the smallest of these. The public key is:

```json
{"n": 3233, "e": 17, "c": 2509}
```

`n = 3233` is tiny — trial division finds the factors instantly:

```python
n, e, c = 3233, 17, 2509
for p in range(2, 100):
    if n % p == 0:
        q = n // p
        break
print(p, q)
# 53 61

phi = (p - 1) * (q - 1)
d = pow(e, -1, phi)
m = pow(c, d, n)
print(m, bytes.fromhex(hex(m)[2:]))
```

If the resulting `m` decodes to ASCII, you're holding the flag. For larger `n`, throw it at `factordb` (it has cached factorizations of every CTF modulus ever published) or run `yafu factor`.

### Diffie-Hellman key exchange — the concept

Two people agree on a shared key over a public channel without ever sending the key:

```
Alice picks a, sends A = g^a mod p
Bob   picks b, sends B = g^b mod p
Alice computes  s = B^a mod p
Bob   computes  s = A^b mod p
                    └── same value: g^(ab) mod p
```

An eavesdropper sees `g`, `p`, `A`, `B`, but recovering `a` from `g^a mod p` is the **discrete logarithm problem** — hard for large `p`. Modern variants use elliptic curves instead of `mod p` — same idea, smaller keys, faster.

DH is how TLS, SSH, Signal, and WireGuard agree on session keys. You'll rarely break DH in a CTF — challenges focus on RSA.

### Elliptic-curve cryptography (briefly)

ECC uses points on an elliptic curve instead of integers mod p. The benefit: a 256-bit ECC key gives roughly the same security as a 3072-bit RSA key — smaller, faster, less battery.

Algorithms you'll see named: **X25519** (key exchange), **Ed25519** (signing), **ECDSA P-256** (TLS / JWT). Treat them as drop-in replacements for DH and RSA-signing respectively. The math is harder; CTF-level attacks on ECC are rare and almost always involve some implementation quirk (bad randomness in nonces, leaked private-key bit, etc.).

---

## Digital signatures

Signatures answer "did this exact data come from the owner of this private key?" — they prove **integrity** and **authenticity** of a message.

```
Sign:   sig = sign(private_key, hash(message))
Verify: verify(public_key, hash(message), sig) → true/false
```

The signer hashes the message first because public-key ops are expensive — you sign a small hash, not the whole document. This is why signature schemes always specify a hash function (e.g. ECDSA-SHA256, Ed25519, RSA-PSS-SHA512).

Practical example with `openssl`:

```bash
echo "release v1.0" > msg.txt

openssl dgst -sha256 -sign priv.pem -out msg.sig msg.txt
openssl dgst -sha256 -verify pub.pem -signature msg.sig msg.txt
# Verified OK
```

You see this in software supply chains: signed `.deb` packages, code-signing certificates, container image signatures (Sigstore), JWTs.

### Where signatures break in CTFs

- **Algorithm-confusion JWTs** — server accepts `alg: none`, or treats an HMAC signature with the public key as legitimate.
- **Deterministic ECDSA with bad randomness** — if two signatures use the same `k`, the private key falls out instantly. This is how the PlayStation 3 firmware key was extracted (2010).
- **Length-extension on raw hashes** — using `SHA-256(secret || data)` for authentication lets attackers append. The fix is HMAC.

---

## Hash functions (vs encryption)

A **cryptographic hash** is a one-way function: takes any input, produces a fixed-size output, and you can't recover the input from the output. **There is no key.**

| Property | What it means |
|----------|---------------|
| Deterministic | Same input → same output, always |
| Fast to compute | Hashing GB/s |
| Pre-image resistant | Given `h`, hard to find any `m` with `H(m) = h` |
| Second pre-image resistant | Given `m`, hard to find `m' ≠ m` with `H(m') = H(m)` |
| Collision resistant | Hard to find any two `m1 ≠ m2` with `H(m1) = H(m2)` |

| Algorithm | Output | Status |
|-----------|--------|--------|
| MD5 | 128 bits / 32 hex | Broken (collisions in seconds); fine as a non-cryptographic checksum |
| SHA-1 | 160 bits / 40 hex | Broken (collisions feasible); deprecated |
| SHA-256 | 256 bits / 64 hex | Current default |
| SHA-3 / Keccak | 256–512 bits | Drop-in successor; based on different construction |
| BLAKE2 / BLAKE3 | 256–512 bits | Faster than SHA-2, equally secure |

```bash
echo -n 'hello' | sha256sum
# 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824 -

# Hash a file
sha256sum ubuntu-22.04.iso
```

### Hashing vs encryption — the line in one sentence

**Encryption is reversible with a key; hashing is not reversible at all.** If someone says "I encrypted the password with SHA-256," correct them — they hashed it, and that's not the same.

We cover password hashing (bcrypt, scrypt, Argon2, PBKDF2) in detail in [hash-cracking.md](hash-cracking.md). For now: regular hashes are too fast for storing passwords because they let attackers brute-force billions per second.

---

## Hybrid systems — how real protocols compose these

TLS, SSH, Signal, WireGuard, age, GPG — all of them follow the same recipe:

```
1. asymmetric (slow)    → agree on a fresh symmetric key for this session
2. symmetric AEAD (fast) → encrypt the actual payload with that key
3. hash / HMAC          → verify integrity / derive subkeys / fingerprint identities
```

TLS 1.3 specifically:

- **ECDHE** (ephemeral X25519 or P-256) agrees on the session secret.
- **HKDF-SHA384** derives traffic keys from that secret.
- **AES-256-GCM** or **ChaCha20-Poly1305** encrypts the records.
- **ECDSA** or **RSA-PSS** signatures verify the server certificate.

You don't need to memorize this. You need to recognize the *pattern*: any time someone needs to send a lot of data securely, you'll see asymmetric → symmetric → MAC.

---

## Encodings vs encryption — recap with examples

Same distinction as last module, restated because students keep tripping on it:

| Looks like | Is | What gives it away |
|------------|-----|--------------------|
| `SGVsbG8=` | Base64 encoding | `=` padding, multiple of 4 length |
| `c29tZXRoaW5n` | Base64 encoding | mixed case + digits + maybe `+/` |
| `48656c6c6f` | Hex encoding | only `0-9a-f`, even length |
| `e3b0c44298fc1c14...` | SHA-256 hash | exactly 64 hex chars, no message structure visible |
| `5d41402abc4b2a76b9719d911017c592` | MD5 hash | exactly 32 hex chars |
| `$2b$12$WnaIqyZc...` | bcrypt hash (encrypted form) | `$2b$` prefix |
| `gAAAAABf3...` | Fernet token | `gAAAAA` prefix |
| `-----BEGIN RSA PRIVATE KEY-----` | PEM-encoded key | armor header |
| Random-looking bytes | could be AES ciphertext, could be random | needs context to tell |

The encoding-chain CTF challenge is exactly the first two rows nested: outer Base64, inner hex. Recognize the shapes.

---

## Practical: openssl cheat sheet

```bash
# Symmetric (AES-256-CBC, password-derived key with PBKDF2)
openssl enc -aes-256-cbc -pbkdf2 -salt -in in.txt -out out.bin
openssl enc -d -aes-256-cbc -pbkdf2 -in out.bin -out in.txt

# RSA key pair
openssl genrsa -out priv.pem 2048
openssl rsa -in priv.pem -pubout -out pub.pem
openssl rsa -in priv.pem -text -noout            # inspect numerical params

# Hash a file
openssl dgst -sha256 file.bin
sha256sum file.bin                                # same thing, different binary

# Sign and verify
openssl dgst -sha256 -sign priv.pem -out sig.bin file.bin
openssl dgst -sha256 -verify pub.pem -signature sig.bin file.bin

# Look at a cert
openssl x509 -in cert.pem -text -noout
openssl s_client -connect example.com:443 -showcerts < /dev/null
```

> **Gotcha.** `openssl` on Kali 2024 ships OpenSSL 3.x, which removed some legacy ciphers and changed default options. Old CTF write-ups using `openssl enc` without `-pbkdf2` may produce different output than what you get today — add `-md md5 -pbkdf2` flags only if the challenge says it used the old default.

---

## Tooling table

| Need | Tool |
|------|------|
| Inspect/encode/decode anything quickly | [CyberChef](https://gchq.github.io/CyberChef/) |
| Real RSA/AES/openssl ops on the command line | `openssl` |
| Cracking small RSA | [factordb.com](http://factordb.com/), `yafu`, `sage` |
| Heavy cryptanalysis (lattice, coppersmith, ECC) | [SageMath](https://www.sagemath.org/) |
| Cryptography library in Python | [`cryptography`](https://cryptography.io/) (high level), `pycryptodome` (low level) |
| Hash identification | `hashid`, `hash-identifier` (covered next module) |
| End-to-end practice | [CryptoHack](https://cryptohack.org/) |

Implementing crypto yourself in production is almost always wrong. Use libraries. The [`cryptography`](https://cryptography.io/) Python library has a "hazmat" submodule named that way deliberately — to scare you into using the high-level recipes (`Fernet`, `AESGCM`) instead.

---

## CSOT CTF cross-reference

| Challenge | What it teaches |
|-----------|-----------------|
| [encoding-chain](../../CTFs/week-04/encoding-chain/) | Base64 → hex chain; recognise layered encodings |
| [xor-single-byte](../../CTFs/week-04/xor-single-byte/) | Brute force the smallest XOR cipher |
| [weak-rsa-mini](../../CTFs/week-04/weak-rsa-mini/) | Factor a tiny `n`, recover `d`, decrypt `c` |
| [vigenere-notes](../../CTFs/week-04/vigenere-notes/) | Polyalphabetic substitution (covered last module, but recurs here as XOR's classical cousin) |

These four together walk you from "encoding" through "stream cipher" to "asymmetric." Solving them in order gives a clean mental gradient.

---

## Practice progression

- **CryptoHack** — `General → Encoding`, `General → XOR`, `Mathematics`, `RSA → Starter`. Hands-down the best modern-crypto trainer.
- **picoCTF Cryptography** — gym challenges labeled "easy" and "medium" cover this module's content.
- **Cryptopals Sets 1 and 2** — set 1 is XOR / frequency; set 2 is AES-ECB / CBC misuse. The classic.
- **CSOT Week 4 CTF** — solve all four crypto challenges (caesar-shift, encoding-chain, vigenere-notes, xor-single-byte, weak-rsa-mini).

---

## Further reading

- [Cryptography Engineering — Ferguson, Schneier, Kohno](https://www.schneier.com/books/cryptography-engineering/) — the right book to read once. Builds intuition.
- [A Graduate Course in Applied Cryptography — Boneh, Shoup](http://toc.cryptobook.us/) — free, dense, definitive.
- [Cryptopals Challenges](https://cryptopals.com/) — every modern crypto bug as a puzzle.
- [Real-World Crypto blog posts on the cryptography.io site](https://cryptography.io/) — short articles on common misuse.
- [Cryptohack Wiki](https://github.com/cryptohack/wiki) — write-ups and references mapped to their challenges.

---

## Next module

[hash-cracking.md](hash-cracking.md) — Hashing was the third family; here we look at it as an attacker. Identify a hash, pick the right cracker, throw the right wordlist at it.
