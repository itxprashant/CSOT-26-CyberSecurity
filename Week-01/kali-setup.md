# Kali Linux setup

Kali Linux is a Debian-based distribution preloaded with hundreds of security tools — from network scanners to password crackers to web proxies. It's the standard environment for penetration testing and CTF competitions.

**You don't need Kali specifically** — any Linux environment works for CSOT. But Kali saves you hours of manual tool installation and is what most tutorials assume you're using.

---

## Choosing your setup method

| Method | Best for | Pros | Cons |
|--------|----------|------|------|
| **WSL2** (Windows) | Windows users who want minimal disruption | Fast, integrates with Windows filesystem, low overhead | No GUI tools by default; some network tools behave differently |
| **VirtualBox** | Any OS; maximum isolation | Full Kali experience with GUI, complete network control | Uses more RAM/CPU; slower than native |
| **Native Linux** | Already running Linux | Fastest performance; no virtualization overhead | Risk of breaking daily-use system; install tools manually |
| **VMware** | Prefer VMware over VirtualBox | Better performance than VirtualBox for some hardware | Requires license for Pro features |
| **Cloud VM** | Limited local resources | Nothing to install locally; accessible from anywhere | Requires internet; potential latency |

**Recommendation for most CSOT students:** WSL2 if you're on Windows (quickest to get started), VirtualBox if you want the full Kali desktop experience.

---

## Option A — WSL2 (Windows 10/11)

WSL2 (Windows Subsystem for Linux 2) runs a real Linux kernel inside Windows. It's fast and well-integrated.

### Prerequisites

- Windows 10 version 2004+ or Windows 11
- Virtualization enabled in BIOS (usually VT-x or AMD-V)
- At least 4 GB free RAM

### Installation

Open **PowerShell as Administrator** (right-click → Run as administrator):

```powershell
# Enable WSL and install Kali
wsl --install -d kali-linux
```

If WSL is already installed but you don't have Kali:

```powershell
# List available distributions
wsl --list --online

# Install Kali specifically
wsl --install -d kali-linux
```

After installation completes, **restart your computer**. Then open **Kali Linux** from the Start menu.

### First-time setup

You'll be prompted to create a username and password. Then update the system:

```bash
# Update package lists and upgrade all packages
sudo apt update && sudo apt upgrade -y

# Install the default security tool collection (large download, ~2–3 GB)
sudo apt install -y kali-linux-default

# Or for a minimal install with just the tools we need for Week 1:
sudo apt install -y git curl wget nmap python3 python3-pip binutils file
```

### Accessing Windows files from WSL

```bash
# Your Windows C: drive is mounted at:
ls /mnt/c/Users/YourWindowsUsername/

# Create a symlink for convenience:
ln -s /mnt/c/Users/YourName/Documents/github ~/github
```

### Accessing WSL files from Windows

In File Explorer, navigate to: `\\wsl$\kali-linux\home\yourusername\`

### WSL networking notes

- WSL2 uses NAT networking — it has its own IP address
- `localhost` from Windows forwards to WSL (for web servers)
- Some raw socket tools (like `nmap -sS`) may need `sudo` or behave differently than native Linux

---

## Option B — VirtualBox (any OS)

VirtualBox provides a complete isolated virtual machine with full Kali GUI.

### Step 1: Install VirtualBox

Download from [virtualbox.org/wiki/Downloads](https://www.virtualbox.org/wiki/Downloads) for your operating system.

### Step 2: Download Kali VM

Get the pre-built VM image from [kali.org/get-kali/#kali-virtual-machines](https://www.kali.org/get-kali/#kali-virtual-machines).

Choose the **VirtualBox** image (`.ova` file, approximately 3–4 GB).

### Step 3: Import and configure

1. Open VirtualBox → File → Import Appliance → select the `.ova` file
2. Before importing, adjust settings:

| Setting | Recommended value | Minimum |
|---------|-------------------|---------|
| RAM | 4096 MB (4 GB) | 2048 MB |
| CPUs | 2 cores | 1 core |
| Video memory | 128 MB | 64 MB |
| Storage | 40 GB (dynamic) | 20 GB |
| Network | NAT (default) | NAT |

3. Click Import and wait for it to complete

### Step 4: First boot

Default credentials: **`kali`** / **`kali`**

**Immediately change the password:**

```bash
passwd
# Enter new password (won't show characters while typing)
```

### Step 5: Update system

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 6: Install VirtualBox Guest Additions (for better performance)

Inside the Kali VM:

```bash
sudo apt install -y virtualbox-guest-x11
sudo reboot
```

After reboot, you'll have:
- Automatic screen resizing
- Shared clipboard (copy/paste between host and VM)
- Shared folders

### Setting up shared folders

1. In VirtualBox: Settings → Shared Folders → Add new
2. Choose a host folder (e.g., your course repo directory)
3. Check "Auto-mount" and "Make Permanent"
4. Inside Kali, access it at `/media/sf_FolderName/`

```bash
# Add yourself to the vboxsf group to access shared folders
sudo usermod -aG vboxsf $USER
# Log out and back in for the change to take effect
```

### Taking snapshots

Before making risky changes (installing experimental tools, running unknown scripts):

1. VirtualBox → Machine → Take Snapshot
2. Name it descriptively: "Clean Week 1 Setup"
3. If something breaks: Machine → Restore Snapshot

---

## Option C — Native Linux / macOS

If you already run Linux or macOS, install tools as needed rather than switching to Kali.

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y \
  nmap git python3 python3-pip curl wget \
  binutils file net-tools dnsutils \
  whois nikto dirb gobuster \
  forensics-extra steghide exiftool \
  john hashcat wireshark
```

### Arch Linux

```bash
sudo pacman -S nmap git python python-pip curl wget \
  binutils file net-tools bind dnsutils \
  whois wireshark-qt john hashcat
```

### macOS (with Homebrew)

```bash
brew install nmap git python3 curl wget binutils \
  dnsutils whois wireshark hashcat exiftool
```

Note: Some Linux-specific tools (like `ss`, reading `/proc`) won't work identically on macOS. Consider a Linux VM for those exercises.

---

## Verifying your installation

Run these commands to confirm everything works:

```bash
# Basic system info
whoami          # Should print your username
uname -a        # Should show Linux kernel info
which bash      # Should print /bin/bash or /usr/bin/bash

# Essential tools
which nmap      # Network scanner
which git       # Version control
which python3   # Python interpreter
which curl      # HTTP client
which grep      # Pattern matching

# Test a command
echo "Setup verified!" | base64
# Should output: U2V0dXAgdmVyaWZpZWQhCg==

echo "U2V0dXAgdmVyaWZpZWQhCg==" | base64 -d
# Should output: Setup verified!
```

If any `which` command returns nothing, install the missing package:

```bash
sudo apt install <package-name>
```

---

## Installing Burp Suite (preview for Week 3)

Burp Suite is the industry-standard web application testing tool. Install it now so it's ready for Week 3.

### Download

Get **Burp Suite Community Edition** (free) from [portswigger.net/burp/communitydownload](https://portswigger.net/burp/communitydownload).

### Install

```bash
# Make the installer executable
chmod +x burpsuite_community_linux_*.sh

# Run the installer
./burpsuite_community_linux_*.sh
```

Or on Kali (pre-installed):

```bash
# Already available — just run it
burpsuite
```

### Quick verification

1. Launch Burp Suite
2. Create a temporary project
3. Go to Proxy tab → confirm it says "Intercept is off"
4. Close it — we'll configure it properly in Week 3

---

## Docker (for CTF challenges)

Some Week 1 CTF challenges use Docker containers. Install Docker if you don't have it:

### On Kali/Ubuntu/Debian

```bash
sudo apt install -y docker.io
sudo systemctl enable docker --now

# Add yourself to the docker group (avoids needing sudo every time)
sudo usermod -aG docker $USER
# Log out and back in for this to take effect
```

### Verify Docker

```bash
docker run hello-world
# Should pull the image and print "Hello from Docker!"
```

### On WSL2

Install Docker Desktop for Windows, then enable WSL2 integration in Docker Desktop settings.

---

## Recommended terminal configuration

A few quality-of-life improvements for your shell:

```bash
# Add to ~/.bashrc or ~/.zshrc:

# Better history (up arrow searches history)
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# Useful aliases
alias ll='ls -la'
alias grep='grep --color=auto'
alias ports='ss -tulpn'
alias myip='curl -s ifconfig.me'
```

After editing, reload: `source ~/.bashrc`

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| WSL won't install | Virtualization disabled | Enter BIOS settings; enable VT-x (Intel) or AMD-V |
| WSL: "no network" | DNS or WSL networking issue | `wsl --shutdown` from PowerShell, then restart WSL |
| VirtualBox VM won't start | VT-x not available | Disable Hyper-V in Windows Features; enable VT-x in BIOS |
| VM extremely slow | Insufficient resources | Increase RAM to 4 GB; allocate 2+ CPU cores |
| `command not found` | Package not installed | `sudo apt install <package>` |
| `E: Unable to locate package` | Package lists outdated | `sudo apt update` first, then retry install |
| Docker permission denied | Not in docker group | `sudo usermod -aG docker $USER` then re-login |
| Shared clipboard not working | Guest Additions not installed | Install virtualbox-guest-x11 and reboot |

---

## Documentation and help

- [Kali Linux documentation](https://www.kali.org/docs/) — official guides
- [Kali tools listing](https://www.kali.org/tools/all-tools/) — every pre-installed tool with descriptions
- [WSL documentation](https://learn.microsoft.com/en-us/windows/wsl/) — Microsoft's WSL guides
- [VirtualBox manual](https://www.virtualbox.org/manual/) — detailed VM configuration

---

## Next module

[linux-cli.md](linux-cli.md) — Now that your environment is ready, learn to use it effectively.
