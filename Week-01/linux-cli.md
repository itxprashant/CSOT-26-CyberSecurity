# Linux command line essentials

The Linux command line (shell) is the primary interface for security work. GUI tools exist, but understanding the CLI gives you speed, scriptability, and the ability to work on remote systems where no GUI is available. Every CTF category — from web to forensics to crypto — ultimately requires comfortable shell usage.

This module covers the commands you'll use daily throughout the course and in real-world security work.

---

## Understanding the shell

When you open a terminal, you're interacting with a **shell** — a program that reads your commands, executes them, and shows the output. The default shell on most Linux systems is **bash** (Bourne Again Shell).

### The prompt

```
kali@kali:~/Documents$ 
│     │    │          │
│     │    │          └── $ means regular user (# means root)
│     │    └── Current directory (~ = home)
│     └── Hostname
└── Username
```

### How commands work

```bash
command [options] [arguments]
```

- **Command:** The program to run (`ls`, `grep`, `find`)
- **Options:** Modify behavior (usually start with `-` or `--`)
- **Arguments:** What the command operates on (files, directories, strings)

Example: `ls -la /var/log`
- Command: `ls` (list directory contents)
- Options: `-l` (long format) + `-a` (show hidden files), combined as `-la`
- Argument: `/var/log` (the directory to list)

---

## Filesystem navigation

Linux organizes everything as a tree starting from `/` (root). Understanding the standard directory structure helps you know where to look for things:

### Key directories

| Directory | Contains | CTF relevance |
|-----------|----------|---------------|
| `/` | Root of the filesystem | Starting point for absolute paths |
| `/home/user/` | User's personal files | Where your work lives; `~` shortcut |
| `/etc/` | Configuration files | Passwords (`/etc/shadow`), hosts, services |
| `/var/log/` | Log files | Evidence of activity; timestamps |
| `/tmp/` | Temporary files | Often world-writable; used for exploits |
| `/proc/` | Process information (virtual) | Environment variables, running process details |
| `/usr/bin/` | User programs | Where most commands live |
| `/root/` | Root user's home | Usually contains flags in CTFs |
| `/opt/` | Optional software | Third-party tools often installed here |

### Navigation commands

```bash
pwd                        # Print Working Directory — where am I right now?
ls                         # List files in current directory
ls -la                     # List ALL files (including hidden) in long format
ls -lah                    # Same but with human-readable file sizes
cd /path/to/dir            # Change to an absolute path
cd relative/path           # Change to a path relative to current location
cd ~                       # Go to your home directory (same as cd alone)
cd ..                      # Go up one level (parent directory)
cd -                       # Go back to the previous directory
```

### Understanding `ls -la` output

```
drwxr-xr-x 2 kali kali 4096 May 25 10:30 Documents
│├─┤├─┤├─┤ │ │    │    │    │             │
││  │  │  │ │ │    │    │    │             └── Name
││  │  │  │ │ │    │    │    └── Last modified date
││  │  │  │ │ │    │    └── Size in bytes
││  │  │  │ │ │    └── Group owner
││  │  │  │ │ └── User owner
││  │  │  │ └── Hard link count
││  │  │  └── Others: r-x (read + execute)
││  │  └── Group: r-x (read + execute)
││  └── Owner: rwx (read + write + execute)
│└── File type: d=directory, -=file, l=symlink
└── First character: file type indicator
```

### Path types

| Type | Example | Meaning |
|------|---------|---------|
| Absolute | `/var/log/syslog` | Full path from root; always starts with `/` |
| Relative | `./scripts/run.sh` | Relative to current directory; `./` means "here" |
| Home | `~/Documents/` | Expands to `/home/yourusername/Documents/` |
| Parent | `../sibling-dir/` | Go up one level, then into sibling-dir |

---

## File operations

### Creating files and directories

```bash
touch newfile.txt                # Create empty file (or update timestamp)
mkdir projects                   # Create a directory
mkdir -p a/b/c/d                 # Create nested directories (all at once)
```

### Copying, moving, and renaming

```bash
cp source.txt destination.txt    # Copy a file
cp -r source_dir/ dest_dir/      # Copy a directory recursively
mv oldname.txt newname.txt       # Rename a file
mv file.txt /other/location/     # Move a file to another directory
```

### Deleting (be careful!)

```bash
rm file.txt                      # Delete a file (no undo!)
rm -r directory/                 # Delete a directory and everything inside
rm -rf directory/                # Force delete without confirmation (DANGEROUS)
```

**Warning:** There is no trash/recycle bin in the terminal. `rm` is permanent. Always double-check your path before pressing Enter, especially with wildcards or `-rf`.

### Viewing file contents

```bash
cat file.txt                     # Print entire file to screen
less file.txt                    # Paginated viewer (q to quit, / to search)
head -n 20 file.txt              # First 20 lines
tail -n 20 file.txt              # Last 20 lines
tail -f /var/log/syslog          # Follow a file in real-time (Ctrl+C to stop)
wc -l file.txt                   # Count lines in a file
wc -w file.txt                   # Count words
```

### File information

```bash
file mystery_document            # Identify file type by content (not extension!)
stat file.txt                    # Detailed metadata (size, timestamps, inode)
du -sh directory/                # Disk usage of a directory (human-readable)
```

**CTF tip:** Always run `file` on unknown files. A file named `image.png` might actually be a ZIP archive or a text file with a misleading extension.

---

## Searching for files and content

Searching is probably the most important skill for CTFs. You need to find files by name, find content within files, and filter large outputs.

### `find` — locate files by name, type, or attributes

```bash
# Find by name
find . -name "flag.txt"                    # In current dir and below
find / -name "*.conf" 2>/dev/null          # Everywhere; suppress permission errors

# Find by type
find /home -type f                         # Files only
find /home -type d                         # Directories only
find /home -type l                         # Symbolic links only

# Find by modification time
find /var/log -mtime -7                    # Modified in last 7 days
find . -mmin -30                           # Modified in last 30 minutes
find . -newer reference_file               # Modified after reference_file

# Find by permissions
find / -perm -4000 2>/dev/null             # Files with SUID bit set (important for privilege escalation)
find / -perm -0002 -type f 2>/dev/null     # World-writable files

# Find by size
find . -size +1M                           # Files larger than 1 MB
find . -size 0                             # Empty files (sometimes interesting)

# Find and execute
find . -name "*.log" -exec grep "error" {} \;   # Search inside found files
find . -name "*.tmp" -delete                     # Delete found files (careful!)
```

### `grep` — search content within files

```bash
# Basic usage
grep "pattern" file.txt                    # Lines containing "pattern"
grep -i "pattern" file.txt                 # Case-insensitive
grep -r "pattern" directory/               # Recursive search through all files
grep -ri "password" /etc/ 2>/dev/null      # Find "password" in configs (ignore case)

# Context
grep -n "pattern" file.txt                 # Show line numbers
grep -C 3 "error" log.txt                 # 3 lines before and after each match
grep -B 2 "pattern" file.txt              # 2 lines before each match
grep -A 2 "pattern" file.txt              # 2 lines after each match

# Matching control
grep -v "pattern" file.txt                 # Invert: lines NOT matching
grep -c "pattern" file.txt                 # Count matches
grep -l "pattern" *.txt                    # List filenames with matches
grep -w "word" file.txt                    # Match whole words only

# Regular expressions
grep -E "error|warning|critical" log.txt   # Extended regex: OR matching
grep "^Start" file.txt                     # Lines starting with "Start"
grep "end$" file.txt                       # Lines ending with "end"
grep "csot26{.*}" file.txt                 # Match flag format
```

### `locate` — fast filename search (uses pre-built index)

```bash
sudo updatedb                              # Update the index (run first time)
locate flag.txt                            # Instant filename search
```

---

## File permissions

Permissions control who can read, write, and execute files. Understanding them is critical for CTF challenges (especially privilege escalation) and real-world security.

### Reading permissions

```bash
ls -l file.txt
# -rw-r--r-- 1 kali kali 1234 May 25 10:30 file.txt
```

| Position | Meaning |
|----------|---------|
| `-` | File type: `-` = regular file, `d` = directory, `l` = link |
| `rw-` | Owner permissions: read, write, no execute |
| `r--` | Group permissions: read only |
| `r--` | Others permissions: read only |

### Permission values

| Symbol | Octal | Meaning |
|--------|-------|---------|
| `r` | 4 | Read: view contents |
| `w` | 2 | Write: modify contents |
| `x` | 1 | Execute: run as program (or enter if directory) |
| `-` | 0 | Permission not granted |

### Octal notation

Permissions are often expressed as 3-digit octal numbers:

```
Owner  Group  Others
 rwx    r-x    r-x    = 755
 4+2+1  4+0+1  4+0+1  = 755
```

| Octal | Permissions | Common use |
|-------|-------------|------------|
| `755` | rwxr-xr-x | Executable scripts, directories |
| `644` | rw-r--r-- | Regular files (readable by all) |
| `600` | rw------- | Private files (SSH keys, `.env`) |
| `777` | rwxrwxrwx | World-writable (almost always a bad idea) |
| `4755` | rwsr-xr-x | SUID binary (runs as file owner, not caller) |

### Changing permissions

```bash
chmod 755 script.sh               # Set exact permissions (octal)
chmod +x script.sh                # Add execute permission for all
chmod u+w file.txt                # Add write for owner (u=user/owner)
chmod g-w file.txt                # Remove write for group
chmod o-rx file.txt               # Remove read+execute for others
chown user:group file.txt         # Change ownership (requires root)
```

### Special permissions (CTF-critical)

| Bit | Octal | Effect | Why it matters |
|-----|-------|--------|----------------|
| **SUID** | 4000 | File executes as the file's owner, not the user running it | If root owns a SUID binary, it runs as root — a privilege escalation vector |
| **SGID** | 2000 | File executes with the file's group; new files in SGID dirs inherit the group | Less common in CTFs but used in some challenges |
| **Sticky** | 1000 | Only file owner can delete files in the directory | `/tmp` has this — prevents users from deleting each other's files |

```bash
# Find SUID binaries (potential privilege escalation)
find / -perm -4000 -type f 2>/dev/null

# Example: if /usr/bin/readflag is SUID root, running it gives you root-level access to read the flag
```

---

## Processes

Understanding running processes is essential for CTF challenges that involve background services, and for system administration.

```bash
ps aux                            # List all running processes
ps aux | grep python              # Find specific processes
top                               # Real-time process monitor (q to quit)
htop                              # Better version of top (install with apt)

kill PID                          # Terminate a process gracefully
kill -9 PID                       # Force kill (last resort)
killall process_name              # Kill all processes with that name

# Background and foreground
command &                         # Run in background
jobs                              # List background jobs
fg %1                             # Bring job 1 to foreground
Ctrl+Z                            # Suspend current process
bg                                # Resume suspended process in background
```

### The `/proc` filesystem

Linux exposes process information as files in `/proc/`. This is extremely useful in CTFs:

```bash
ls /proc/                         # Each numbered directory = a running process (PID)
cat /proc/self/environ            # Environment variables of current shell
cat /proc/1234/cmdline            # Command line that started process 1234
tr '\0' '\n' < /proc/1234/environ # Environment variables of process 1234 (readable format)
cat /proc/1234/status             # Process status, memory usage, UID
ls -la /proc/1234/fd/             # Open file descriptors
```

---

## Pipes and redirection

Pipes connect commands together, allowing you to build complex data processing from simple tools. This is the Unix philosophy: small programs that do one thing well, combined via pipes.

### Pipes (`|`)

The `|` operator sends the output of one command as input to the next:

```bash
# Count how many lines contain "error"
grep "error" log.txt | wc -l

# Find the 10 most common IP addresses in a log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# List all users with bash as their shell
cat /etc/passwd | grep "/bin/bash" | cut -d: -f1

# Find flag in a large file
strings binary_file | grep "csot26{"
```

### Output redirection

| Operator | Meaning | Example |
|----------|---------|---------|
| `>` | Write stdout to file (overwrite) | `echo "hello" > out.txt` |
| `>>` | Append stdout to file | `echo "line 2" >> out.txt` |
| `2>` | Write stderr to file | `find / -name "x" 2> errors.txt` |
| `2>/dev/null` | Discard stderr (suppress errors) | `find / -name "flag" 2>/dev/null` |
| `&>` | Write both stdout and stderr to file | `command &> all_output.txt` |
| `<` | Read stdin from file | `sort < unsorted.txt` |

### Command substitution

```bash
# Use output of one command inside another
echo "Today is $(date)"
echo "I am $(whoami) on $(hostname)"
files=$(find . -name "*.log")    # Store output in a variable
```

### Useful pipe patterns for CTFs

```bash
# Decode base64 content from a file
cat encoded.txt | base64 -d

# Extract URLs from a web page
curl -s http://example.com | grep -oP 'https?://[^\s"]+' 

# Sort and deduplicate lines
sort file.txt | uniq

# Count occurrences and show most common
sort data.txt | uniq -c | sort -rn | head -20

# Extract specific field from structured data
cat /etc/passwd | cut -d: -f1,7  # Username and shell

# Convert hex to ascii
echo "68656c6c6f" | xxd -r -p
```

---

## Text processing tools

These commands are the building blocks for data analysis in CTFs:

| Command | Purpose | Example |
|---------|---------|---------|
| `sort` | Sort lines | `sort -n numbers.txt` (numeric sort) |
| `uniq` | Remove adjacent duplicates | `sort file \| uniq -c` (count occurrences) |
| `cut` | Extract columns | `cut -d',' -f2 data.csv` (2nd CSV field) |
| `awk` | Pattern scanning and processing | `awk '{print $3}' file` (3rd whitespace-separated field) |
| `sed` | Stream editor (find/replace) | `sed 's/old/new/g' file` |
| `tr` | Translate/delete characters | `tr 'a-z' 'A-Z'` (lowercase to uppercase) |
| `rev` | Reverse each line | `echo "dlrow olleh" \| rev` |
| `tee` | Write to file AND stdout | `command \| tee output.txt` |
| `xargs` | Build commands from input | `find . -name "*.tmp" \| xargs rm` |

---

## Archives and compression

CTF challenges often involve nested or unusual archives:

```bash
# tar archives
tar -xf archive.tar              # Extract .tar
tar -xzf archive.tar.gz          # Extract .tar.gz (gzip compressed)
tar -xjf archive.tar.bz2         # Extract .tar.bz2 (bzip2 compressed)
tar -xJf archive.tar.xz          # Extract .tar.xz (xz compressed)
tar -czf output.tar.gz dir/      # Create .tar.gz archive
tar -tf archive.tar.gz           # List contents without extracting

# Other formats
gzip -d file.gz                  # Decompress gzip
bzip2 -d file.bz2               # Decompress bzip2
xz -d file.xz                   # Decompress xz
unzip archive.zip                # Extract zip
7z x archive.7z                  # Extract 7z (install p7zip-full)

# Identify unknown archives
file mystery_archive             # Let `file` command tell you what it is
```

**CTF pattern:** Challenges sometimes nest archives inside archives (a .tar.gz containing a .zip containing a .tar.xz containing the flag). Script the extraction:

```bash
# Example: extract nested archives
tar -xzf layer1.tar.gz
cd extracted/
unzip layer2.zip
tar -xJf layer3.tar.xz
cat flag.txt
```

---

## Network utilities (basics)

These will be expanded in Week 2, but you need the basics now:

```bash
ping -c 3 8.8.8.8               # Test connectivity (3 packets)
curl -I https://example.com      # HTTP headers only
curl -s https://example.com      # Silent mode (content only)
wget https://example.com/file    # Download a file
ip addr                          # Show network interfaces and IPs
ss -tulpn                        # Show listening ports (what's running?)
```

---

## Getting help

```bash
man ls                           # Full manual page for any command
command --help                   # Quick usage summary
whatis command                   # One-line description
apropos keyword                  # Search manual pages by keyword
```

**Online tools:**
- [ExplainShell](https://explainshell.com/) — paste a complex command to see each part explained
- [tldr pages](https://tldr.sh/) — simplified man pages with practical examples

---

## Practice exercises

Try these in your terminal to build muscle memory:

1. Create a directory `~/ctf-practice/week1/` with nested subdirectories
2. Create 5 text files with different content in various subdirectories
3. Find all `.txt` files you just created using `find`
4. Search for a specific word across all of them using `grep -r`
5. Create a hidden file (starting with `.`) and verify `ls -la` shows it
6. Set a file's permissions to `600` and verify only you can read it
7. Chain commands: find all files, count their total lines using `wc -l`
8. Create a tarball of your practice directory, then extract it somewhere else

---

## External resources

- [Linux Journey](https://linuxjourney.com/) — interactive beginner tutorial
- [ExplainShell](https://explainshell.com/) — paste commands to see explanations
- [OverTheWire Bandit](https://overthewire.org/wargames/bandit/) — hands-on practice that matches this module
- [The Linux Command Line (book)](https://linuxcommand.org/tlcl.php) — free, comprehensive reference

---

## Next module

[bash-scripting.md](bash-scripting.md) — Combine these commands into reusable scripts.
