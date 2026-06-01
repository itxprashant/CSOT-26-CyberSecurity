# Week 1 assignments — bash scripting

These are **optional practice** exercises. They are not scored — **only weekend CTF flags count** toward your course standing. Complete them to build scripting habits before the CTF.

Share work with coordinators only if they ask for demos or study groups; there is no assignment submission portal requirement unless announced in the [course WhatsApp group](https://chat.whatsapp.com/BJN7duZuObq1gbGPrped0y).

**General requirements for all assignments:**
- Include a proper shebang (`#!/bin/bash`) as the first line
- Make the file executable (`chmod +x script.sh`)
- Handle missing or invalid arguments gracefully (print usage and exit with code 1)
- Use meaningful variable names
- Test on your Kali/WSL environment before you consider them done

---

## Assignment 1: Log finder

### Objective

Write `log_finder.sh` that searches a directory tree for recently modified log files and produces a summary report.

### Requirements

The script must:

1. Accept a directory path as the first argument
2. Find all `.log` files under that directory (recursively) that were modified in the last **7 days**
3. Count the total number of lines across all found files
4. Print a formatted summary with:
   - Number of log files found
   - Total lines across all files
   - A sorted list of filenames with their individual line counts

### Usage

```bash
./log_finder.sh /var/log
```

### Expected output format

```
=== Log Finder Report ===
Directory: /var/log
Time range: last 7 days

Files found: 5
Total lines: 12,847

--- File details (sorted by size) ---
  8,201 lines  /var/log/syslog
  2,340 lines  /var/log/auth.log
  1,892 lines  /var/log/kern.log
    312 lines  /var/log/dpkg.log
    102 lines  /var/log/apt/history.log
```

### Error handling

- If no argument is given: print `Usage: ./log_finder.sh <directory>` and exit 1
- If the argument is not a valid directory: print an error and exit 1
- If no `.log` files are found: print "No log files modified in the last 7 days" and exit 0

### Hints

- `find <dir> -name "*.log" -mtime -7` finds files modified in the last 7 days
- `wc -l < file` counts lines without printing the filename
- You can store results in an array or a temp file for sorting
- `sort -rn` sorts numerically in reverse (largest first)

### Self-check

- [ ] Shebang and executable bit set
- [ ] Usage and error messages for bad/missing directory
- [ ] Finds `.log` files modified in the last 7 days
- [ ] Line counts match manual `wc -l` spot checks
- [ ] Output format matches the specification

---

## Assignment 2: System report

### Objective

Write `sys_report.sh` that collects system health information and saves it to a timestamped file. This simulates a common sysadmin task — periodic system snapshots that help you spot anomalies.

### Requirements

The script must collect and save the following sections:

1. **Header** — report timestamp, hostname, current user
2. **System uptime** — output of `uptime`
3. **Disk usage** — disk usage of the user's home directory (`df -h` for the mount point containing `$HOME`)
4. **Memory usage** — output of `free -h`
5. **Running processes** — total count and top 5 by CPU usage
6. **Active network connections** — listening ports (`ss -tulpn` or `netstat`)
7. **Recent logins** — last 5 login entries (`last | head -5`)
8. **Footer** — end marker with total generation time

The output file must be named `sys_report_YYYYMMDD_HHMMSS.txt` in the current directory.

### Usage

```bash
./sys_report.sh
# Creates: sys_report_20260525_143022.txt
```

### Error handling

- If a command is not available (e.g., `netstat` not installed), print "Command not available" in that section instead of failing
- The script should complete even if individual sections have errors

### Hints

- Use `date +%Y%m%d_%H%M%S` for the filename timestamp
- Use `SECONDS` bash variable or `date +%s.%N` to measure generation time
- `ps aux --sort=-%cpu | head -6` gives top 5 by CPU (plus header)
- Wrap section commands in functions for cleaner code
- `command -v <cmd>` checks if a command exists

### Self-check

- [ ] Timestamped filename generated correctly
- [ ] All sections present with sensible data
- [ ] Graceful handling when optional commands are missing
- [ ] Readable headers and footer with generation time

---

## Assignment 3: Password generator

### Objective

Write `gen_pass.sh` that generates cryptographically random passwords with configurable options. This teaches you about randomness sources in Linux, argument parsing, and file I/O.

### Requirements

1. Accept password length as first argument (default: 16 if not provided)
2. Accept count (number of passwords) as second argument (default: 1)
3. Generate passwords using uppercase letters, lowercase letters, digits, and symbols
4. Print each generated password to stdout
5. Append each password with a timestamp to `passwords.log` in the current directory
6. Validate inputs: length must be 8–128, count must be 1–100

### Character set

Include at least these characters:
- Uppercase: `A-Z`
- Lowercase: `a-z`
- Digits: `0-9`
- Symbols: `!@#$%^&*()-_=+[]{}|;:,.<>?`

### Usage

```bash
# Generate 1 password of length 16 (defaults)
./gen_pass.sh

# Generate 1 password of length 24
./gen_pass.sh 24

# Generate 5 passwords of length 20
./gen_pass.sh 20 5
```

### Expected stdout output

```
Generated passwords (length=20, count=3):
  1) kR9#mP2$xL5&nQ8!wJ4@
  2) Bf7*cH3^tY1!vN6&zA9#
  3) pL4@dW8#jK2$mX5!qR7^
```

### Expected `passwords.log` format

```
[2026-05-25 14:30:22] kR9#mP2$xL5&nQ8!wJ4@
[2026-05-25 14:30:22] Bf7*cH3^tY1!vN6&zA9#
[2026-05-25 14:30:22] pL4@dW8#jK2$mX5!qR7^
```

### Error handling

- Length < 8: print "Error: Minimum password length is 8" and exit 1
- Length > 128: print "Error: Maximum password length is 128" and exit 1
- Count < 1 or > 100: print appropriate error and exit 1
- Non-numeric input: print "Error: Arguments must be positive integers" and exit 1

### Randomness source

Use `/dev/urandom` as your randomness source. Example approaches:

```bash
# Approach 1: tr + /dev/urandom
tr -dc 'A-Za-z0-9!@#$%^&*()-_=+' < /dev/urandom | head -c "$length"

# Approach 2: openssl
openssl rand -base64 "$length" | tr -dc 'A-Za-z0-9!@#$%^&*' | head -c "$length"
```

### Hints

- `/dev/urandom` is a kernel-provided source of pseudo-random bytes
- `tr -dc 'charset'` deletes everything NOT in the charset
- `head -c N` takes exactly N characters
- Use a regex to validate numeric input: `[[ "$var" =~ ^[0-9]+$ ]]`
- The `date` command with format string creates timestamps: `date '+%Y-%m-%d %H:%M:%S'`

### Self-check (before the CTF)

- [ ] Correct shebang and executable
- [ ] Default values work when no args provided
- [ ] Validates length range (8–128) and count range (1–100)
- [ ] Handles non-numeric input gracefully
- [ ] Generated passwords contain all character classes and differ each run
- [ ] Correct stdout formatting
- [ ] Correctly appends to `passwords.log` with timestamp
- [ ] Code structure and readability

---

## Practice checklist

Before the weekend CTF, verify:

- [ ] All three scripts have `#!/bin/bash` as line 1
- [ ] All three scripts are executable (`chmod +x`)
- [ ] All three scripts handle missing arguments with usage messages
- [ ] All three scripts handle invalid arguments with error messages
- [ ] You've tested each script on your Kali/WSL environment
- [ ] Running `bash -n script.sh` produces no syntax errors (static check)
- [ ] Running [ShellCheck](https://www.shellcheck.net/) produces no critical warnings (optional but recommended)

---

## Tips for success

1. **Start simple** — get the basic functionality working first, then add error handling and formatting
2. **Test incrementally** — run your script after every few lines you add, not just at the end
3. **Use ShellCheck** — paste your script at shellcheck.net to catch common bugs
4. **Read error messages** — bash errors tell you the line number and what went wrong
5. **Use `set -x`** — run `bash -x script.sh` to see exactly what bash is executing

---

**Scoring reminder:** Weekend CTF flags (`csot26{...}`) are the only scored component for Week 1. These scripts prepare you for scripting-themed CTF challenges.
