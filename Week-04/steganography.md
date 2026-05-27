# Steganography

Cryptography hides the **meaning** of a message — anyone can see ciphertext, no one can read it. Steganography hides the **existence** of a message — the carrier looks like an innocuous photo, audio clip, or document, and there's "nothing to read" unless you know where to look.

In CTFs, steganography (or "stego") is the category where a JPEG turns out to be a ZIP, a PNG carries text in its trailing bytes, and a wav file hides a flag in its spectrogram. It's the most visual, most playful category — and the one where the right tool finds the answer in seconds.

---

## Why this module matters

- **You will absolutely see stego in CTFs.** It's a staple of every beginner board. Often worth 100–300 points with low difficulty for anyone with the right toolkit.
- **Real attackers use it.** Malware drops payloads inside PNG icons. Command-and-control traffic hides commands in Twitter avatars. Insider threats exfiltrate data inside outgoing image attachments. Defenders need to recognise the patterns.
- **It teaches "look at the file, not the filename."** Half the CTF stego challenges are just `file mystery.png` revealing the file isn't actually a PNG — the same instinct you need for malware triage.

---

## The core distinction — stego ≠ encryption

| | Steganography | Encryption |
|---|---------------|------------|
| **Goal** | Hide that a message exists | Hide what the message says |
| **Adversary sees** | A "normal" file | Visible ciphertext |
| **Security model** | Security through obscurity (the carrier looks ordinary) | Security through math (the key is the secret) |
| **What it gives you** | Plausible deniability, covert channel | Confidentiality |
| **Combine?** | Yes — encrypt the payload, then hide the ciphertext inside the carrier | Often combined in practice |

**Stego on its own is not security.** Anyone running the right `binwalk`/`zsteg`/`exiftool` pipeline will find the payload. Treat it as a covert channel, not as protection. CTFs deliberately make it easy to find — your job is to know the workflow.

---

## File carriers — what can hide what

Almost any file format can carry hidden data, because:

- File formats have **slack space** (unused regions where you can stuff bytes).
- They have **metadata fields** (comments, EXIF, ID3 tags).
- They use **lossless encodings** that ignore low-order bits an attacker can flip.
- They have **defined end markers** — anything after the marker is ignored by the renderer but still on disk.

| Carrier | Common stego techniques |
|---------|-------------------------|
| **PNG** | LSB encoding, appended bytes after IEND, ancillary chunks (tEXt, zTXt), metadata |
| **JPEG** | EXIF metadata, comment field, appended bytes after EOI (`FF D9`), JSTEG/F5/Outguess in DCT coefficients |
| **GIF** | Palette manipulation, appended bytes, animation frame slack |
| **BMP** | LSB encoding (very common — BMP is uncompressed) |
| **WAV** | LSB on samples, spectrogram text, channel manipulation |
| **MP3** | ID3 tags, frame padding, MP3stego in MDCT bins |
| **PDF** | Metadata, JavaScript, embedded files, white-on-white text |
| **DOCX / Office** | XML metadata, embedded objects, hidden text |
| **Any** | Appending data after the format's logical end |

---

## File magic — the most important table in this module

Every file format starts with a specific byte sequence called the **magic number** or **signature**. `file` reads the first few bytes and tells you what the file actually is, regardless of extension.

| Format | Magic (hex) | Magic (ASCII) | Footer |
|--------|-------------|---------------|--------|
| PNG | `89 50 4E 47 0D 0A 1A 0A` | `.PNG....` | `49 45 4E 44 AE 42 60 82` (IEND chunk) |
| JPEG | `FF D8 FF E0` or `FF D8 FF E1` | (binary) | `FF D9` |
| GIF87a | `47 49 46 38 37 61` | `GIF87a` | `3B` |
| GIF89a | `47 49 46 38 39 61` | `GIF89a` | `3B` |
| BMP | `42 4D` | `BM` | none |
| ZIP / DOCX / APK / JAR | `50 4B 03 04` | `PK..` | `50 4B 05 06` |
| RAR (v1.5+) | `52 61 72 21 1A 07 00` | `Rar!...` | none |
| 7-Zip | `37 7A BC AF 27 1C` | `7z....` | none |
| GZIP | `1F 8B` | (binary) | none |
| PDF | `25 50 44 46` | `%PDF` | `%%EOF` |
| ELF (Linux exe) | `7F 45 4C 46` | `.ELF` | none |
| PE (Windows exe) | `4D 5A` | `MZ` | none |
| WAV | `52 49 46 46 ... 57 41 56 45` | `RIFF....WAVE` | none |
| MP3 (with ID3) | `49 44 33` | `ID3` | none |
| OGG | `4F 67 67 53` | `OggS` | none |
| FLAC | `66 4C 61 43` | `fLaC` | none |
| Sqlite DB | `53 51 4C 69 74 65 20 66 6F 72 6D 61 74 20 33 00` | `SQLite format 3.` | none |

> **CTF tip.** Run `file` on every artifact you get. A "PNG" with a `PK` magic is actually a ZIP, full stop. The Week 4 [hidden-png](../../CTFs/week-04/hidden-png/) challenge is exactly this kind of mismatch — `challenge.png` isn't a real PNG, and the flag is sitting in the trailing text.

### Inspecting with `xxd`

```bash
xxd hidden.png | head -2
# 00000000: 8950 4e47 0d0a 1a0a 0000 000d 4948 4452  .PNG........IHDR
# 00000010: 0000 0064 0000 0064 0802 0000 00ff 8095  ...d...d........
```

The first 8 bytes (`89 50 4E 47 0D 0A 1A 0A`) confirm it's a real PNG. Compare to:

```bash
xxd ../../CTFs/week-04/hidden-png/challenge.png
# 00000000: ef bf bd 50 4e 47 0a 0a 63 73 6f 74 32 36 7b 73  ...PNG..csot26{s
# ...
```

The first three bytes are `EF BF BD` (the UTF-8 replacement character), not the real PNG signature. It's not a PNG — it's a text file with a fake header. `cat` solves it; the hint of the challenge literally says `strings challenge.png`.

---

## The triage workflow — order of operations

Whatever the carrier looks like, walk this in order:

```
1. file       — what is it really?
2. exiftool   — metadata?
3. strings    — embedded ASCII / UTF-8 text?
4. binwalk    — embedded files (carving)?
5. xxd / hex viewer — look for anomalies near magic/footer
6. Format-specific tool (zsteg, steghide, foremost, stegsolve, sonic-visualiser)
```

You will find ~80% of CTF stego with steps 1–4. Reach for specialised tools only when these fail.

### Step 1: `file`

```bash
file unknown
# unknown: PNG image data, 100 x 100, 8-bit/color RGB, non-interlaced
# unknown: Zip archive data, at least v2.0 to extract
# unknown: ASCII text
# unknown: data                ← suspicious; no recognised format
```

### Step 2: `exiftool`

```bash
exiftool image.jpg
# ExifTool Version Number         : 12.76
# File Name                       : image.jpg
# Software                        : GIMP 2.10
# Comment                         : csot26{exif_does_not_lie}
# GPS Position                    : 28.6139 N, 77.2090 E
# Create Date                     : 2024:05:25 23:06:00
```

If the flag is hiding in metadata, you see it here. The Week 4 [metadata-leak](../../CTFs/week-04/metadata-leak/) challenge is exactly this — the flag is in a `Comment` field. The challenge ships a text artifact instead of a real JPEG to keep the repo small, but the workflow is identical: `exiftool challenge.jpg`.

You can also read the comment with `strings` or `cat` for the synthetic version provided.

### Step 3: `strings`

`strings` prints all printable-ASCII runs of length ≥ 4 in a file.

```bash
strings -n 6 image.png | grep -i csot26
# csot26{strings_find_secrets}
```

`-n 6` raises the minimum run length to 6, cutting noise. For Unicode, add `-e l` (16-bit little-endian).

For the Week 4 [hidden-png](../../CTFs/week-04/hidden-png/) challenge:

```bash
strings ../../CTFs/week-04/hidden-png/challenge.png
# PNG
# csot26{strings_find_secrets}
```

One line found, challenge solved.

### Step 4: `binwalk`

`binwalk` scans for embedded file signatures within a larger file. Crucial for "file inside a file" challenges (polyglots).

```bash
binwalk suspicious.png

# DECIMAL       HEXADECIMAL     DESCRIPTION
# --------------------------------------------------------------------------------
# 0             0x0             PNG image, 800 x 600
# 1024          0x400           Zip archive data, at least v2.0 to extract
# 1432          0x598           End of Zip archive

binwalk -e suspicious.png       # extract embedded files into _suspicious.png.extracted/
```

If `binwalk` reports a ZIP inside your PNG, that's a **polyglot file** — valid as both formats simultaneously. The image viewer stops at IEND; `unzip` finds its PK signature and reads from there. Both work. Both fool naïve scanners.

### Step 5: `xxd` and hex inspection

When automated tools find nothing, look at the bytes yourself.

```bash
xxd image.png | less
```

Things to look for:

- Bytes after the format's expected end marker (PNG IEND at `49 45 4E 44 AE 42 60 82`; JPEG EOI at `FF D9`).
- Long runs of suspicious-looking ASCII inside what should be compressed data.
- Mismatched dimensions in headers (e.g. PNG IHDR says 100x100 but the file is 50 KB — way too big for that resolution).

```bash
# Show only bytes after a JPEG's EOI marker
python3 -c "
import sys
data = open('image.jpg','rb').read()
i = data.rfind(b'\xff\xd9')
sys.stdout.buffer.write(data[i+2:])
" > trailer.bin

file trailer.bin
```

---

## LSB steganography

**Least Significant Bit (LSB)** hiding is the canonical "embed data in an image" technique. The idea: each pixel's RGB values are 0–255 (8 bits per channel); flipping the lowest bit changes the colour by ±1, which the human eye can't see. You can stash one bit of secret per channel per pixel — a 1000×1000 image carries 375 KB of hidden data.

```
Original pixel:  R=10101100  G=01110011  B=11001011
Hide bits "101": R=10101101  G=01110010  B=11001011
                          ↑          ↑          ↑
                          1 bit      0 bit      1 bit (unchanged)
```

### Format matters

| Format | LSB works? | Why |
|--------|------------|-----|
| **PNG** | Yes | Lossless — every bit you wrote stays |
| **BMP** | Yes | Uncompressed |
| **GIF** | Limited | Palette-indexed, fewer channels |
| **JPEG** | **No** for naïve LSB | Lossy DCT compression destroys low bits |
| **WAV** | Yes | Uncompressed audio samples |
| **MP3** | No for naïve LSB | Lossy compression |

This is why CTF LSB challenges almost always use PNG or BMP. If you're handed a JPEG and asked about "LSB," the technique is JSTEG/F5/Outguess — embedding in DCT coefficients instead of raw pixels.

### Tools

```bash
# zsteg — best automated LSB scanner for PNG/BMP
sudo gem install zsteg
zsteg challenge.png

# steghide — embed/extract with passphrase, works on JPEG, BMP, WAV, AU
sudo apt install steghide
steghide extract -sf cover.jpg          # prompts for passphrase
steghide extract -sf cover.jpg -p ''    # try empty passphrase

# stegsolve — Java GUI for visual LSB / channel exploration
java -jar stegsolve.jar
# Then File → Open, and step through bit planes / channels

# outguess — JPEG-aware extractor
sudo apt install outguess
outguess -k 'password' -r cover.jpg payload.bin

# StegOnline — browser-based for when you can't install
# https://georgeom.net/StegOnline/
```

`zsteg` is the workhorse for PNG. It tries dozens of bit-plane / channel-order combinations automatically and reports anything that decodes to text or known formats.

```bash
zsteg -a challenge.png
# b1,r,lsb,xy         .. text: "csot26{lsb_hidden}"
# b1,g,lsb,xy         .. <empty>
# ...
```

> **CTF tip.** If `zsteg` finds nothing, try `zsteg --all challenge.png` for an exhaustive scan, and also try [StegOnline](https://georgeom.net/StegOnline/) — its visual bit-plane viewer sometimes reveals patterns automated tools miss (e.g. a QR code visible only in the blue-channel LSB).

---

## Audio steganography

Two main techniques:

1. **LSB on samples** — same idea as images, on WAV samples. Use `steghide` or write your own Python with `wave`.
2. **Spectrogram drawing** — text or images literally painted into the time-frequency plot. Open in Audacity (`View → Spectrogram`) or Sonic Visualiser; if a flag is encoded this way you'll see it as words floating in the spectrogram.

```bash
sudo apt install sonic-visualiser audacity

sonic-visualiser audio.wav
# Layer → Add Spectrogram
```

> **CTF tip.** If the audio sounds harsh or "buzzy" at certain frequencies, suspect spectrogram drawing. Plain LSB audio is inaudible.

---

## File-in-file and polyglot tricks

A **polyglot** is a single file valid as multiple formats. Common combinations:

- PNG + ZIP (image renderers stop at IEND; ZIP parsers find PK signature later in the file).
- JPEG + PHP (image renderers stop at EOI; web servers execute PHP from anywhere in the file).
- PDF + JS (PDF specs allow JavaScript blocks).

### Detect with `binwalk`

```bash
binwalk -e mystery.png
# If it reports both PNG and ZIP, it's a polyglot.

ls _mystery.png.extracted/
# 400.zip
unzip _mystery.png.extracted/400.zip
# secret.txt -> csot26{poly_glot_payload}
```

### Detect with `file -k`

The `-k` flag tells `file` to keep going past the first match:

```bash
file -k mystery.png
# mystery.png: PNG image data, 800 x 600
# \012- data
# \012- Zip archive data, at least v2.0 to extract
```

### Manual carving

If `binwalk` misbehaves, carve the embedded archive manually using `dd`:

```bash
xxd mystery.png | grep -m1 'PK'
# 00000400: 504b 0304 ...  ← offset 0x400 = decimal 1024

dd if=mystery.png of=hidden.zip bs=1 skip=1024
unzip hidden.zip
```

---

## File carving with `foremost` and `scalpel`

When the file isn't a polyglot but is a chunk of disk containing recoverable fragments (think USB-image forensics), `foremost` reads the magic-byte table and pulls every recognisable file from anywhere in the input.

```bash
sudo apt install foremost
foremost -i disk.img -o carved/
ls carved/
# audit.txt   jpg/   png/   pdf/   zip/
```

`foremost` is also the right answer for the Week 4 [carved-note](../../CTFs/week-04/carved-note/) challenge, though for that specific blob `strings blob.bin | grep csot26` is faster — the flag is literally in the ASCII text. Use the right hammer for the nail.

```bash
strings ../../CTFs/week-04/carved-note/disk/blob.bin
# junk junk csot26{carved_from_garbage} more junk
```

---

## When passphrases come into play

Tools like `steghide` and `outguess` are passphrase-protected. The CTF will hint at the passphrase — sometimes blatantly (`password is "course"`), sometimes via the challenge title, file name, or other artifacts in the problem set. Try in this order:

1. Empty passphrase: `steghide extract -sf cover.jpg -p ''`.
2. Obvious words from the challenge text/title.
3. Common stego passwords: `password`, `secret`, `flag`, `steghide`, the challenge's own filename.
4. Brute force with [stegcracker](https://github.com/Paradoxis/StegCracker) (a `steghide` brute-force wrapper over a wordlist):

```bash
pip install stegcracker
stegcracker cover.jpg /usr/share/wordlists/rockyou.txt
```

This is, in spirit, the same as Week 4's [hash-cracking.md](hash-cracking.md) — just throwing a wordlist at a different oracle.

---

## A worked example — the canonical PNG stego flow

You're handed `mystery.png`. Walk the steps:

```bash
# 1. What is it really?
file mystery.png
# mystery.png: PNG image data, 800 x 600, 8-bit/color RGB, non-interlaced

# 2. Metadata?
exiftool mystery.png
# (nothing suspicious)

# 3. Embedded text?
strings -n 8 mystery.png | grep -i csot26
# (nothing)

# 4. Embedded files?
binwalk mystery.png
# 0   PNG image, 800 x 600
# (nothing else)

# 5. LSB scan
zsteg -a mystery.png
# b1,b,lsb,xy   .. text: "csot26{lsb_lives_in_blue}"
```

That's the LSB-only variant. If `zsteg` had also found nothing, you'd inspect bit planes manually in StegSolve or write a small Python script to dump the LSB of each channel and look for headers (`csot26{`, `PK`, `BM`, `RIFF`, etc.).

---

## Mini Python LSB extractor

When tools refuse, code your own:

```python
from PIL import Image

def extract_lsb(path, channel=0, max_chars=200):
    img = Image.open(path).convert("RGB")
    bits = []
    for px in img.getdata():
        bits.append(px[channel] & 1)
    bytes_out = bytearray()
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for b in bits[i:i+8]:
            byte = (byte << 1) | b
        bytes_out.append(byte)
        if len(bytes_out) >= max_chars:
            break
    return bytes_out

# Try each channel
for ch_name, ch in [("R", 0), ("G", 1), ("B", 2)]:
    data = extract_lsb("mystery.png", ch)
    print(ch_name, data[:60])
```

Two more variants you might need: change the bit-ordering (`MSB-first` vs `LSB-first` per byte), and the pixel traversal order (`row-major` vs `column-major`). Modify the loop accordingly.

---

## Tool table

| Tool | Carrier | Use |
|------|---------|-----|
| `file` | any | Identify true format |
| `exiftool` | image/PDF/Office | Metadata fields |
| `strings` | any | Embedded ASCII / UTF-8 |
| `binwalk` | any | Detect embedded files |
| `foremost`, `scalpel` | any | File carving |
| `xxd`, `hexdump`, `bvi` | any | Manual hex inspection |
| `zsteg` | PNG, BMP | Automated LSB scan |
| `steghide` | JPEG, BMP, WAV, AU | Passphrase-protected embed/extract |
| `outguess` | JPEG | JPEG-specific DCT stego |
| `StegSolve` | PNG, BMP | Visual bit-plane viewer |
| `StegOnline` | PNG, BMP, JPEG | Browser version of the same |
| `Audacity`, `Sonic Visualiser` | audio | Spectrograms |
| `pdfinfo`, `pdf-parser`, `peepdf` | PDF | Object & metadata analysis |
| `mat2` | any | Strip metadata (defensive use) |

---

## Defensive — stripping metadata on the way out

Stego cuts both ways. The same EXIF that solves a CTF challenge leaks GPS from a holiday selfie. If you publish files publicly:

```bash
exiftool -all= -overwrite_original photo.jpg
mat2 photo.jpg                              # creates photo.cleaned.jpg
```

`mat2` is more thorough — it also clears XMP, IPTC, and Office hidden metadata that `exiftool` may miss.

---

## CSOT CTF cross-reference

| Challenge | Technique | Tool of choice |
|-----------|-----------|----------------|
| [hidden-png](../../CTFs/week-04/hidden-png/) | Flag in embedded text after fake header | `strings` |
| [metadata-leak](../../CTFs/week-04/metadata-leak/) | Flag in EXIF/comment metadata | `exiftool` (or `cat comment.txt` for the synthetic artifact) |
| [carved-note](../../CTFs/week-04/carved-note/) | Flag inside a binary blob | `strings`, `foremost`, or `binwalk -e` |

These three intentionally cover the spectrum: appended text, structured metadata, raw carving. If you can handle all three, you can handle most beginner-board stego.

---

## Ethics and legal context

Steganography on **your own** data is fine. Embedding payloads into someone else's file and publishing it, or using stego to exfiltrate data from a system you don't own, crosses into IT Act §43 / §66 territory just like any other unauthorized access. The classroom rule:

- Stego practice → CSOT challenges, public CTFs (picoCTF, OverTheWire, HackTheBox), your own personal files.
- Off-limits → anyone else's files without consent, anything that crosses into a real network.

Stego is also disproportionately used by **malware authors** for command-and-control and payload delivery. Reading a "how to hide a payload in a PNG" tutorial doesn't make you a malware author, but writing one and shipping it does. Stay on the analyst side of the line.

---

## Practice progression

- **Week 4 CTF**: solve [hidden-png](../../CTFs/week-04/hidden-png/), [metadata-leak](../../CTFs/week-04/metadata-leak/), [carved-note](../../CTFs/week-04/carved-note/).
- **picoCTF Forensics gym** — beginner stego challenges (`Matryoshka doll`, `extensions`, `Glory of the garden`).
- **TryHackMe — "c4ptur3-th3-fl4g"** — covers stego and encoding together.
- **HackTheBox — beginner stego challenges** under "Steganography" tag.
- **CTFlearn — Forensics section** — short stego puzzles with hints.

---

## Further reading

- [zsteg README](https://github.com/zed-0xff/zsteg) — every flag explained, with example artifacts.
- [Stego Lab guide on GitBook](https://0xrick.github.io/lists/stego/) — wide reference of stego tools.
- [SANS — Steganography in the Modern Attack Landscape](https://www.sans.org/white-papers/steganography-modern-attack-landscape/) — defensive perspective.
- [Stegano Python library](https://stegano.readthedocs.io/) — for scripting your own embeds/extracts.
- [Aperisolve](https://www.aperisolve.com/) — online automated stego pipeline that runs `binwalk`, `zsteg`, `exiftool`, `strings`, and more.

---

## Next module

[digital-forensics.md](digital-forensics.md) — Stego is one technique inside the broader discipline of forensics. Next we look at the full toolkit: carving disks, reading PCAPs, hunting through logs, and treating evidence the way a real responder would.
