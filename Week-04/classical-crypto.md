# Classical cryptography & encoding

Before modern crypto turned into a wall of acronyms (AES-GCM, ECDSA, X25519), people hid messages with pencil-and-paper tricks: shift the alphabet, swap one letter for another, scramble the order. Those tricks survived because they're **everywhere in CTFs**. They are the easiest 100-point challenges on every beginner board, and they appear in real-world data leaks more often than you'd expect — anytime a developer says "just obfuscate it a bit," they reinvent a classical cipher.

This module covers the classical ciphers and encodings you will see week after week: how each one works, how to recognize it, how to break it, and where it shows up in the Week 4 CTF.

---

## Why this module matters

Classical crypto is the on-ramp for everything else. Every concept in modern crypto — key, plaintext, ciphertext, frequency analysis, brute force, known-plaintext attack — was invented and named on a classical cipher. If you understand why Caesar is broken by trying 25 shifts, you understand why a 56-bit DES key is broken by trying 2^56 keys. The math gets bigger; the idea is the same.

Practical reasons too:

- **CTF triage.** When a challenge dumps a string of letters in front of you, the first 60 seconds are spent recognizing *what kind* of thing it is. Is it Base64? Hex? ROT-something? A monoalphabetic substitution? Without a mental catalogue, you'll waste hours.
- **Defense.** "Encoded" is not "encrypted." Devs ship Base64 thinking they hid the password. They didn't. You need to be able to spot this on code reviews.
- **Onboarding to real crypto.** Once you've broken a Vigenère by repeating-key analysis, the leap to "why XOR with a repeating pad is unsafe" is a single step. We make that step in [modern-crypto.md](modern-crypto.md).

---

## Encoding vs encryption — the most important distinction

This is the slide every "intro to crypto" course skips, then gets re-taught every interview cycle:

| | Encoding | Encryption |
|---|----------|------------|
| **Goal** | Make data safe to transport (ASCII-clean, URL-safe, line-safe) | Make data unreadable without a key |
| **Key needed?** | No | Yes |
| **Reversible by anyone?** | Yes (the algorithm is the whole secret) | Only with the key |
| **Examples** | Base64, Base32, Base58, hex, URL encoding, ROT13 | AES, ChaCha20, RSA, Vigenère |
| **CTF role** | Always present, often chained 2–3 deep | The main event |
| **Mistake** | Calling it "encryption" because it looks scrambled | Trusting it because the algorithm name sounds modern |

If you only remember one rule: **if there's no key, it's encoding.** Anyone with `base64 -d` can reverse it.

ROT13 sits in a strange middle ground — it has a fixed "key" (shift 13), so it's technically a cipher, but since the key is built into the name and everyone knows it, in practice it's an encoding.

---

## Common encodings — the warm-up

You will encounter these constantly. Memorize the look.

### Base64

Alphabet: `A–Z`, `a–z`, `0–9`, `+`, `/`. Length is a multiple of 4 (padded with `=`).

```bash
echo -n 'Hello' | base64
# SGVsbG8=

echo 'SGVsbG8=' | base64 -d
# Hello
```

**Tell:** trailing `=` or `==`, mix of upper/lower/digits, length divisible by 4.

### Base32

Alphabet: `A–Z`, `2–7`. Looks like Base64 with no lowercase and no digits below 2.

```bash
echo -n 'Hello' | base32
# JBSWY3DPEB======
```

**Tell:** uppercase + digits 2–7 only, often lots of `=` padding.

### Base58

Used by Bitcoin and IPFS. Alphabet skips ambiguous characters (`0`, `O`, `I`, `l`). Variable length, no padding.

```bash
pip install base58
python3 -c "import base58; print(base58.b58decode('JxF12TrwUP45BMd').decode())"
# Hello World
```

### Hex (Base16)

Each byte → two hex digits. Length is always even.

```bash
echo -n 'Hello' | xxd -p
# 48656c6c6f

echo '48656c6c6f' | xxd -r -p
# Hello
```

**Tell:** only `0-9a-fA-F`, even length, often blocks of 32/40/64 (which is also how MD5/SHA-1/SHA-256 look — be careful, it could be a hash).

### URL encoding (percent-encoding)

```text
Hello World!  →  Hello%20World%21
```

```python
from urllib.parse import quote, unquote
quote("flag=csot26{x}")     # 'flag%3Dcsot26%7Bx%7D'
unquote("%2Fetc%2Fpasswd")  # '/etc/passwd'
```

**Tell:** lots of `%` followed by two hex digits.

### CyberChef — the universal Swiss army knife

[CyberChef](https://gchq.github.io/CyberChef/) (GCHQ, open source) is the single most useful tool in this entire week. Drag operations into a recipe, the output updates live. Its **Magic** operation auto-detects common encodings and chains them.

For the Week 4 [encoding-chain](../../CTFs/week-04/encoding-chain/) challenge, drop `payload.txt` into CyberChef and pick `From Base64 → From Hex`. The Magic operation finds it in one click.

Manually:

```bash
cat ../../CTFs/week-04/encoding-chain/payload.txt | base64 -d | xxd -r -p
# csot26{layers_of_encoding}
```

That's the whole challenge: recognize the outer Base64, recognize that the inner blob is hex, peel both layers.

---

## Caesar / ROT-N — the simplest shift cipher

Caesar shifts every letter by a fixed amount. ROT-N is just Caesar with shift N. ROT13 specifically shifts by 13 — and because the alphabet has 26 letters, ROT13(ROT13(x)) = x, so it's self-inverse.

```
Plaintext:    HELLO
Shift +3:     KHOOR     (Caesar's actual shift)
Shift +13:    URYYB     (ROT13)
Shift +25:    GDKKN     (= shift -1)
```

### Doing it in one line

```bash
echo 'URYYB' | tr 'A-Za-z' 'N-ZA-Mn-za-m'       # ROT13
echo 'KHOOR' | tr 'A-Za-z' 'X-ZA-Wx-za-w'       # ROT-3 (shift back by 3)
```

`tr` does straight character translation. For an arbitrary shift, Python is easier:

```python
def rotn(s, n):
    out = []
    for ch in s:
        if 'A' <= ch <= 'Z':
            out.append(chr((ord(ch) - ord('A') + n) % 26 + ord('A')))
        elif 'a' <= ch <= 'z':
            out.append(chr((ord(ch) - ord('a') + n) % 26 + ord('a')))
        else:
            out.append(ch)
    return ''.join(out)

print(rotn("pfbg26{fvzcyr_pnrfne_fuvsg}", 13))
# csot26{simple_caesar_shift}
```

### Breaking Caesar by brute force

There are only 25 non-trivial shifts. Try all of them and read.

```bash
for i in $(seq 1 25); do
  echo "shift=$i: $(echo 'pfbg26{fvzcyr_pnrfne_fuvsg}' | python3 -c "
import sys; n=$i
s=sys.stdin.read().strip()
print(''.join(chr((ord(c)-ord('a')+n)%26+ord('a')) if c.islower() else
              chr((ord(c)-ord('A')+n)%26+ord('A')) if c.isupper() else c for c in s))
")"
done
```

You'll see one line that reads `csot26{simple_caesar_shift}` and the other 24 that look like alphabet soup. That's [../../CTFs/week-04/caesar-shift/](../../CTFs/week-04/caesar-shift/) solved.

### Breaking Caesar by frequency

Brute force works because the keyspace is tiny. For longer texts, frequency analysis is more elegant: the most common letter in English is `E` (~12.7%), then `T`, `A`, `O`, `I`, `N`. Whichever letter dominates the ciphertext is likely the shifted version of `E`.

```python
from collections import Counter

ct = "WKLV LV D ORQJHU FDHVDU FLSKHU H[DPSOH WR ZRUN ZLWK"
freq = Counter(ch.upper() for ch in ct if ch.isalpha())
top = freq.most_common(1)[0][0]
shift = (ord(top) - ord('E')) % 26
print("Likely shift:", shift)
```

Most common letter here is `H`, which is 3 ahead of `E`, so shift is 3. Apply `-3` to recover *This is a longer caesar cipher example...*.

> **CTF tip.** ROT13 is so common it's worth a one-second sanity check on any all-letters string. Pipe it through `tr` and skim. Even better — paste into CyberChef, click Magic.

---

## ROT13 vs ROT47

ROT13 only rotates letters. **ROT47** rotates the full printable ASCII range (`!` through `~`), so it touches punctuation and digits too. If a flag has been ROT47'd, the curly braces become `T` and `}` becomes `=`, which is a giveaway.

```bash
echo 'pdf=26{rot47_eats_braces}' | tr '!-~' 'P-~!-O'
# Not the right shift here — illustrative only
```

> **Gotcha.** Don't confuse ROT13 with the flag format. `pfbg26{...}` is ROT13 of `csot26{...}`. If a challenge string contains `26{` you're already done.

---

## Atbash

Atbash maps `A↔Z`, `B↔Y`, … — a fixed reflection. It's a special case of substitution and self-inverse (apply twice, get original).

```bash
echo 'XSOT26' | tr 'A-Z' 'Z-A'
# CHLG—wait, that's wrong because Atbash reverses the alphabet
echo 'XSOT26' | tr 'A-Za-z' 'Z-Az-a'
# CHLG26
```

You'll see Atbash in maybe 1-in-50 CTFs, but it's cheap to try.

---

## Substitution ciphers and frequency analysis

A **monoalphabetic substitution** picks a fixed but arbitrary permutation of the alphabet — each plaintext letter maps to one ciphertext letter. There are `26!` possible keys (≈ 4 × 10²⁶), so brute force is hopeless. Frequency analysis isn't.

### English letter frequencies

| Letter | Frequency |
|--------|-----------|
| E | 12.7% |
| T | 9.1% |
| A | 8.2% |
| O | 7.5% |
| I | 7.0% |
| N | 6.7% |
| S | 6.3% |
| H | 6.1% |
| R | 6.0% |

Also useful:

- Most common bigrams: `TH`, `HE`, `IN`, `ER`, `AN`.
- Most common trigrams: `THE`, `AND`, `ING`.
- A two-letter word is usually `of`, `to`, `in`, `is`, `it`.
- A three-letter word starting with the most-common-final letter is probably `the`.

### Workflow

1. Count letter frequencies in the ciphertext.
2. Guess the most common ciphertext letter → `E`, next → `T`, etc.
3. Look for short words and `'s` suffixes for fast wins.
4. Iterate.

### Solvers

When you don't want to do this by hand:

- [quipqiup.com](https://www.quipqiup.com/) — automated monoalphabetic solver.
- [dCode substitution solver](https://www.dcode.fr/monoalphabetic-substitution).
- CyberChef has a manual substitution recipe; useful for tweaking after an automated guess.

---

## Vigenère — the famous polyalphabetic cipher

Vigenère uses a **keyword**. Each plaintext letter is shifted by the next letter of the key, with the key repeating across the message.

```
Plaintext:  HELLOWORLD
Key:        CSOTCSOTCS         (repeat "CSOT")
Ciphertext: JWZESOCKNV
```

The shift for each position is the letter of the key (`A=0`, `B=1`, … `Z=25`). So `H + C = J`, `E + S = W`, and so on.

Vigenère resisted casual attack for 300 years because **frequency analysis fails directly** — `E` in the plaintext becomes different ciphertext letters depending on which key letter aligns with it.

### The Kasiski technique

In 1863, Friedrich Kasiski noticed that **repeated plaintext substrings produce repeated ciphertext substrings** whenever the same key letters happen to align with them. The distance between repeated ciphertext blocks is a multiple of the key length.

```
Ciphertext:  XYZAB...XYZ........XYZAB
             ^^^      ^^^       ^^^
             ↑        ↑         ↑
             repeated triplets, distance 8 and 16 → key length divides gcd(8,16)=8
```

So:

1. Scan for repeated substrings of length 3–5.
2. Record the distances between them.
3. Take the GCD of those distances — that's your candidate key length.

### Friedman / Index of Coincidence

The **Index of Coincidence (IoC)** is the probability that two random letters from a text are equal. For English plaintext, IoC ≈ 0.066. For uniform random letters, IoC ≈ 0.038.

If you split the Vigenère ciphertext into `N` columns (one per key position), each column is a Caesar cipher of English text. So the column-wise IoC should jump back up to ~0.066 at the correct key length. Try `N = 2, 3, 4, …, 12` and pick the value where the average column IoC is closest to 0.066.

### Once you know the key length, recover the key

Each column is a Caesar shift. Frequency-analyze each column independently (look for `E`-shaped peaks), recover one key letter per column, concatenate. That's the keyword.

### Vigenère in practice — Week 4 CTF

[../../CTFs/week-04/vigenere-notes/](../../CTFs/week-04/vigenere-notes/) gives you `ekcm26{xauxpwfx_hjwxpvg}` and tells you the key is 4 letters: `CSOT`.

```python
def vigenere_decrypt(ct, key):
    out = []
    j = 0
    for ch in ct:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            shift = ord(key[j % len(key)].lower()) - ord('a')
            out.append(chr((ord(ch) - base - shift) % 26 + base))
            j += 1
        else:
            out.append(ch)
    return ''.join(out)

print(vigenere_decrypt("ekcm26{xauxpwfx_hjwxpvg}", "csot"))
# csot26{vigenere_friends}
```

> **CTF tip.** When you have *no* hint about the key, paste the text into [dCode's Vigenère solver](https://www.dcode.fr/vigenere-cipher) with "automatic decryption" — it does Kasiski + IoC for you. CyberChef's `Vigenère Decode` only works if you already know the key.

---

## Transposition ciphers — rearrange, don't substitute

Transposition keeps the original letters and reorders them. Frequency analysis on the ciphertext gives the same distribution as English — which is itself a tell.

### Rail fence

Write the plaintext on `N` "rails" zigzagging up and down, then read each row left-to-right.

```
Plaintext: HELLOWORLD,  rails = 3

H . . . O . . . R . .
. E . L . W . R . D .
. . L . . . O . . . .

Ciphertext: HOR ELWRD LO  →  HORELWRDLO
```

Decryption: reconstruct the zigzag pattern based on rail count and message length, then place each ciphertext letter in order.

### Columnar transposition

Write plaintext into a grid row-by-row under a keyword. Read out columns in the order given by the alphabetical position of each keyword letter.

```
Key:         C O D E
Plaintext:   ATTACKAT
             DAWNXXXX

Read columns in C,O,D,E alphabetical order → C(1) D(2) E(3) O(4):
Column under C: A,D  → AD
Column under D: T,A  → TA   (third in keyword, but second alphabetically)
...
```

Both rail fence and columnar appear in beginner CTFs. Solvers exist; manual decryption is mostly an exercise in patience.

---

## One-time pad — the only provably unbreakable cipher

A **one-time pad (OTP)** XORs the plaintext with a random key *of the same length as the message*. If the key is truly random, used only once, and kept secret, then **the ciphertext gives an attacker zero information** about the plaintext. This is Claude Shannon's information-theoretic security from 1949.

```
Plaintext:  H E L L O          (01001000 01000101 01001100 01001100 01001111)
Key:        K M X P A          (01001011 01001101 01011000 01010000 01000001)
Ciphertext: 00000011 00001000 00010100 00011100 00001110
```

Decryption is the same XOR.

### Why OTP is impractical

You need a key as long as your message, and you can never reuse it. For two parties exchanging gigabytes, you need to first exchange gigabytes of key material *securely*. If you could do that, you wouldn't need encryption.

### Why key reuse is catastrophic

If you encrypt two messages `M1` and `M2` with the same key `K`:

```
C1 = M1 ⊕ K
C2 = M2 ⊕ K
C1 ⊕ C2 = M1 ⊕ M2     (the key cancels out)
```

`M1 ⊕ M2` is **English XOR English**, which has enough redundancy to recover both messages by sliding a guessed crib (`" the "`, `" and "`) along it. This is the "many-time pad" attack and it has appeared in production systems (most famously Microsoft's PPTP and the Venona project that broke Soviet OTP key reuse).

The same idea — **never reuse keystream** — is the foundation of every modern stream cipher rule. We come back to this in [modern-crypto.md](modern-crypto.md) when we look at AES-CTR nonce reuse.

### XOR as a teaser for the next module

A **single-byte XOR** is the smallest possible "stream cipher": one byte of key repeating forever. It's trivially broken (256 keys to try, frequency analysis picks the right one immediately). [../../CTFs/week-04/xor-single-byte/](../../CTFs/week-04/xor-single-byte/) is exactly this — `xxd -r -p` the hex, XOR every byte with each value 0–255, look for the one that yields `csot26{`. We cover the attack in detail in the next module.

---

## Tool table — what to reach for

| Tool | Use it for |
|------|------------|
| [CyberChef](https://gchq.github.io/CyberChef/) | Anything encoded; Magic auto-detection; chained recipes |
| `base64`, `xxd`, `tr`, `rev` | One-shot decodes from the shell |
| `python3` | Custom rotations, XOR, ad-hoc analysis |
| [dCode](https://www.dcode.fr/) | Automatic Vigenère, substitution, rail-fence solvers |
| [quipqiup.com](https://www.quipqiup.com/) | Monoalphabetic substitution by frequency |
| [factordb.com](http://factordb.com/) | Foreshadowing for RSA — covered next module |
| `hashid` | Distinguish a hex hash from a hex-encoded message |

---

## Recognition checklist — what is this string?

When a challenge dumps a blob at you, walk this in order. Most strings fall out in under a minute.

1. **`file <thing>`** — if it's a file, what does the magic byte say?
2. **Length and alphabet check.**
   - Even length, `0-9a-f` only → hex.
   - Length % 4 == 0, ends in `=`, mixes case + `+/` → Base64.
   - All caps + digits `2-7` → Base32.
   - 32/40/64 hex chars and no spaces → maybe a hash, not a message.
3. **All letters, preserves spacing?** → Caesar / Vigenère / substitution.
4. **Visible `26{` or `26%7B`?** → almost certainly a ROT or URL-encoded flag.
5. **Run through CyberChef Magic** with intensive flag on.
6. **Try ROT 1–25** (loop above).
7. **Try Base64 → hex** (the encoding-chain pattern).
8. **Frequency analysis** if the letters are clearly English-shaped.
9. **Last resort**: it's actually something modern. Move to [modern-crypto.md](modern-crypto.md).

---

## Worked example — putting it together

You're handed: `JWZE26{XAUXPWFX_HJWXPVG}`.

- Visible `26{...}` → it's a flag, just rotated.
- All caps letters + `_` and `{}` preserved → substitution-style cipher.
- The `_` was not shifted, so only A-Z is being shifted (typical Vigenère).
- The flag prefix in plaintext is `CSOT`. The ciphertext prefix is `JWZE`. Differences: `J-C=7`, `W-S=4`, `Z-O=11`, `E-T=11`. These don't match a single shift → not Caesar.
- Try Vigenère with the differences as the key: `H=7, E=4, L=11, L=11` → `HELL`. Hmm, partial English word.
- Actually try the obvious course-key first: `CSOT`. Differences yield correct decryption.

That's the [vigenere-notes](../../CTFs/week-04/vigenere-notes/) challenge mental walkthrough. Hints in CTF challenges almost always point at the answer — read them.

---

## Practice progression

- **Week 4 lab challenges** — [caesar-shift](../../CTFs/week-04/caesar-shift/), [encoding-chain](../../CTFs/week-04/encoding-chain/), [vigenere-notes](../../CTFs/week-04/vigenere-notes/). Solve all three before moving on.
- **OverTheWire Krypton** — wargame that walks you through Caesar, Vigenère, substitution, one-time pad. Excellent reinforcement.
- **CryptoHack "Introduction to Cryptohack"** track — covers ASCII, hex, Base64, XOR before getting to real crypto.
- **picoCTF Cryptography practice** — beginner-friendly classical-crypto challenges with hints.

---

## Further reading

- [Practical Cryptography — Classical ciphers reference](http://practicalcryptography.com/ciphers/classical-era/) — every classical cipher you'll meet, with crackers.
- [Wikipedia — Index of coincidence](https://en.wikipedia.org/wiki/Index_of_coincidence) — math behind Friedman test.
- [CTF Wiki — Classical encryption](https://ctf-wiki.org/en/crypto/classical/intro/) — categorized walkthroughs.
- [Cryptopals Challenges, Set 1](https://cryptopals.com/sets/1) — Matasano's legendary intro problems, mostly XOR and frequency.

---

## Next module

[modern-crypto.md](modern-crypto.md) — From shifts to AES, RSA, and why the XOR habit from this module is dangerous when you scale it up.
