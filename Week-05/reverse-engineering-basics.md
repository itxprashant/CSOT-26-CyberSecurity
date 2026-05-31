# Reverse engineering basics

You have a binary. No source code. No comments. Just a file that runs and either prints a flag or refuses to. **Reverse engineering (RE)** is the discipline of understanding what a program does without the author's help — by reading disassembly, tracing execution, and reasoning about data flow.

RE shows up in CTFs as "Reversing" challenges, in malware analysis, in firmware research, and in vulnerability research when you need to understand *exactly* what a closed-source binary does before you exploit it. Week 5 introduces the workflow; mastery takes years, but the first 10 hours teach you patterns that recur everywhere.

> **Authorized targets only.** Reverse engineering someone else's software without permission can violate copyright and computer-access laws depending on jurisdiction and purpose. For CSOT: practice on course binaries, CrackMes, picoCTF, pwnable.kr/reversing, TryHackMe RE rooms, and binaries you compiled yourself. Do not RE commercial software, games, or campus systems to bypass licensing or protections.

---

## Why reverse engineering matters

| Context | What RE answers |
|---------|-----------------|
| **CTF** | "What input makes this program print the flag?" |
| **Malware analysis** | "What does this sample exfiltrate and how?" |
| **Vulnerability research** | "Where is the unsafe `strcpy` and what can I control?" |
| **Firmware / IoT** | "What protocol does this router speak?" |
| **Incident response** | "Is this dropped binary a backdoor?" |

RE complements **dynamic analysis** (running the program under a debugger). Static RE tells you what *could* happen; debugging shows what *does* happen on a given input. Professionals use both.

---

## Compiled programs in one page

High-level languages (C, C++, Rust, Go) compile to **machine code** — CPU instructions. The OS loads the binary, maps segments into memory, and jumps to an entry point (`_start` → `main`).

### ELF (Linux) vs PE (Windows)

| | ELF (Linux) | PE (Windows) |
|---|-------------|--------------|
| **Common extensions** | none, `.elf` | `.exe`, `.dll` |
| **Inspect with** | `file`, `readelf`, `objdump` | `file`, PE-bear, CFF Explorer |
| **Sections** | `.text` (code), `.data`, `.bss`, `.rodata` | `.text`, `.data`, `.rdata` |
| **CSOT focus** | Primary | Brief awareness |

```bash
file ./challenge
# ELF 64-bit LSB executable, x86-64, dynamically linked, ...

readelf -h ./challenge      # ELF header
readelf -S ./challenge      # section headers
readelf -l ./challenge      # program headers (segments)
```

### Stripped vs unstripped

- **Unstripped:** Symbol names like `main`, `check_password` appear in the binary — easier RE.
- **Stripped:** Symbols removed; functions appear as `FUN_00401234` in Ghidra — harder but normal in CTFs.

```bash
file ./challenge
# ... not stripped          ← symbols present
# ... stripped              ← symbols removed
```

---

## Static analysis workflow

Use this order on every unknown binary:

```
1. file          → architecture, bitness, stripped?
2. strings       → passwords, URLs, flag format, error messages
3. checksec      → protections (NX, PIE, canary, RELRO)
4. ltrace        → library calls at runtime (quick dynamic peek)
5. Ghidra/r2     → disassembly, decompiler, rename, annotate
6. gdb           → confirm hypotheses with breakpoints
```

### strings

```bash
strings -n 8 ./challenge | less
strings ./challenge | grep -iE 'flag|password|csot|error'
```

CTF authors often leave clues in plaintext. Always run `strings` before opening Ghidra.

### objdump (quick disassembly)

```bash
objdump -d ./challenge | less          # disassemble .text
objdump -M intel -d ./challenge | less   # Intel syntax (x86)
```

Useful for tiny binaries; Ghidra scales better.

### ltrace / strace (light dynamic)

```bash
ltrace ./challenge                     # library calls (strcmp, printf, ...)
echo "test" | ltrace ./challenge
strace ./challenge 2>&1 | head -50       # syscalls (open, read, write)
```

If the program calls `strcmp(input, "secret")`, `ltrace` may show the comparison string.

---

## Reading x86-64 assembly (minimum viable)

You do not need to write assembly fluently. You need to **recognise patterns**.

### Registers (64-bit Linux)

| Register | Role |
|----------|------|
| `rax` | Return value, accumulator |
| `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9` | First six integer arguments (System V AMD64 ABI) |
| `rsp` | Stack pointer |
| `rbp` | Frame pointer (optional) |
| `rip` | Instruction pointer |

**Function call convention (simplified):** caller puts args in `rdi`, `rsi`, `rdx`, ... then `call`. Callee may modify caller-saved registers; return value in `rax`.

### Instructions you'll see constantly

| Instruction | Meaning |
|-------------|---------|
| `mov dst, src` | Copy |
| `push` / `pop` | Stack |
| `call addr` | Call function |
| `ret` | Return |
| `cmp a, b` | Compare (sets flags) |
| `test a, b` | Bitwise AND for flags |
| `je` / `jne` / `jz` / `jnz` | Jump if equal / not equal / zero / not zero |
| `jmp` | Unconditional jump |
| `lea dst, [src]` | Load effective address |
| `xor eax, eax` | Zero register (common idiom) |

### Control flow patterns

**If/else:**
```asm
cmp    eax, 0x42
jne    fail_label
; success path
fail_label:
```

**Loop:**
```asm
loop_start:
    ...
    dec    ecx
    jnz    loop_start
```

**Function prologue / epilogue:**
```asm
push   rbp
mov    rbp, rsp
sub    rsp, 0x20        ; allocate stack frame
...
leave                   ; or mov rsp,rbp; pop rbp
ret
```

When decompiled code looks wrong, read the assembly at that address — the decompiler guesses; assembly does not lie.

---

## Ghidra — your primary RE environment

**Ghidra** is free, open source, and maintained by the NSA. It disassembles, decompiles to C-like pseudocode, and supports scripting.

### Install

```bash
# Kali often has it preinstalled
which ghidra || sudo apt install -y ghidra

# Or download from https://ghidra-sre.org/
```

### First session workflow

1. **New Project** → Non-Shared → name it `csot_re`
2. **Import File** → select binary → analyze when prompted (defaults OK)
3. **CodeBrowser** opens → double-click `entry` or `main` if listed
4. **Listing** (left): disassembly  
5. **Decompile** (right): pseudocode window
6. **Search** → For Strings → double-click interesting strings → see xrefs (who references this string?)

### Renaming and commenting

- Click a function → `L` to rename (`check_flag` instead of `FUN_00101234`)
- `;` to add comment
- Right-click variable → retype if Ghidra guessed wrong

Good RE is 50% tooling and 50% **documentation in the tool**. Future-you (and teammates) need your renames.

### Finding the flag check

Typical CTF pattern:

1. Search strings for `"Correct"`, `"Wrong"`, `"flag"`, `csot26`
2. Follow xrefs to the function that uses them
3. Read decompiler output for `strcmp`, `memcmp`, XOR loop, or arithmetic on input
4. Reimplement logic in Python or solve by hand

**Example pseudocode pattern:**
```c
void check(char *input) {
  if (strlen(input) != 32) { puts("Wrong length"); return; }
  for (i = 0; i < 32; i++) {
    if ((input[i] ^ 0x42) != target[i]) { puts("Nope"); return; }
  }
  puts("csot26{...}");
}
```

Recovery: `flag[i] = target[i] ^ 0x42`.

---

## Alternatives (know they exist)

| Tool | Strength |
|------|----------|
| **radare2 / r2** | CLI-first, scriptable, steep curve |
| **Cutter** | GUI for radare2 |
| **IDA Free** | Industry standard UI; size limits on free version |
| **Binary Ninja** | Excellent decompiler; paid (free cloud tier limited) |
| **angr** | Symbolic execution — automated path exploration |

For CSOT, **Ghidra + gdb** is enough. Add r2 when you want a faster CLI workflow.

---

## CrackMe practice path

| Level | Where | Skill |
|-------|-------|-------|
| 0 | [picoCTF Reversing](https://play.picoctf.org/) | strings, basic logic |
| 1 | [crackmes.one](https://crackmes.one/) (difficulty 1–2) | Ghidra, simple checks |
| 2 | TryHackMe "Intro to x86-64" / "Reversing" rooms | Guided RE |
| 3 | [reversing.kr](http://reversing.kr/) | Classic Korean RE challenges |
| 4 | [Microcorruption](https://microcorruption.com/) | MSP430 assembly game |

**TryHackMe rooms (recommended):**
- Intro to x86-64
- Reversing ELF
- Windows Reversing (optional)

---

## Dynamic debugging with gdb

Static RE finds *candidates*; gdb confirms them.

```bash
gdb ./challenge
(gdb) break main
(gdb) run
(gdb) disas
(gdb) info registers
(gdb) x/s $rdi          # examine string at rdi (first arg)
(gdb) break *0x401234   # break at address
(gdb) continue
```

**gef / pwndbg / peda** extend gdb with layout, heap views, and exploit helpers — install one:

```bash
# pwndgdb example
git clone https://github.com/pwndbg/pwndbg
cd pwndbg && ./setup.sh
```

For pure RE (not pwn), vanilla gdb + Ghidra is fine.

---

## Common CTF RE challenge types

| Type | Technique |
|------|-----------|
| **Password check** | Find strcmp/memcmp; recover expected bytes |
| **XOR / rolling key** | Loop in decompiler; script inverse |
| **Maze / state machine** | Trace transitions; solve path |
| **Anti-debug** | `ptrace`, timing checks — patch or bypass in gdb |
| **Packed binary** | `upx -d`, or find OEP (original entry point) |
| **.NET / Java** | Use dnSpy, jd-gui — different toolchain |

---

## Ethics and legal boundaries

- **CrackMes and CTF binaries:** designed to be reversed — go ahead.
- **Your own code:** always fair game.
- **Commercial software:** reversing EULAs often prohibit it; bypassing DRM or license checks is legally risky.
- **Malware:** only in isolated VMs; never on production networks.

Document your analysis like a lab report: file hash, tools, findings, IOCs — especially if simulating IR on a sample.

---

## Key takeaways

| Concept | Remember |
|---------|----------|
| `file` + `strings` first | Cheapest wins |
| Ghidra decompiler | Starting point, verify in assembly |
| xrefs to strings | Fast path to "where is the check?" |
| Rename in Ghidra | RE is a notebook, not a one-shot |
| Static + dynamic | Ghidra + gdb together |
| x86-64 calling convention | `rdi` = arg1, `rax` = return |

---

## Practice checklist

- [ ] Run `file`, `strings`, `checksec` on a provided ELF
- [ ] Import a binary into Ghidra and find `main` (or entry → main)
- [ ] Follow a string xref to a password-check function
- [ ] Write a 10-line Python script that inverts a XOR loop from decompiler output
- [ ] Set a gdb breakpoint on `strcmp` and read both arguments at runtime

---

## Advanced reading

- [Ghidra documentation](https://ghidra-sre.org/)
- [Practical Reverse Engineering](https://nostarch.com/reversing) — Dang et al.
- [x86-64 Assembly Language Programming with Ubuntu](https://www.egr.unlv.edu/~ed/assembly64.pdf) — free PDF
- [crackmes.one](https://crackmes.one/) — difficulty-rated CrackMes
- [Microcorruption](https://microcorruption.com/) — assembly puzzle game
- [LiveOverflow reversing playlist](https://www.youtube.com/c/LiveOverflow) — visual introductions

**Next module:** [binary-exploitation-intro.md](binary-exploitation-intro.md) — stack layout, buffer overflows, and pwntools.
