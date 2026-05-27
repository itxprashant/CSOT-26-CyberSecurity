# Introduction to cybersecurity

## What is cybersecurity?

Cybersecurity is the practice of protecting computer systems, networks, programs, and data from unauthorized access, damage, theft, or disruption. It's not just about hackers in hoodies — it encompasses everything from the lock screen on your phone to the encryption protecting bank transactions to the firewalls guarding national infrastructure.

At its core, cybersecurity revolves around three principles known as the **CIA triad**:

### The CIA triad

| Principle | Meaning | Example violation |
|-----------|---------|-------------------|
| **Confidentiality** | Only authorized people can access the data | An attacker reads your private messages |
| **Integrity** | Data cannot be altered without detection | Someone modifies your bank balance in transit |
| **Availability** | Systems remain accessible when needed | A DDoS attack takes down a hospital's network |

Every security decision is a tradeoff between these three. For example:
- Encrypting a hard drive improves **confidentiality** but may slow access (**availability**)
- Requiring 3 approvals for a code deploy improves **integrity** but slows down the team (**availability**)
- Making a document public improves **availability** but sacrifices **confidentiality**

When analyzing a system's security posture, always ask: "Which part of CIA is at risk here?"

### Beyond CIA: Additional principles

| Principle | Meaning |
|-----------|---------|
| **Authentication** | Proving you are who you claim to be (passwords, biometrics, certificates) |
| **Authorization** | Proving you're allowed to do what you're trying to do (role checks, ACLs) |
| **Non-repudiation** | Ensuring someone cannot deny their actions (digital signatures, audit logs) |
| **Accountability** | Tracing actions back to individuals (logging, monitoring) |

---

## Offensive vs defensive security

The security field is broadly divided into two complementary camps:

### Red team (offensive)

Red teamers think like attackers. Their job is to find weaknesses before real adversaries do.

| Activity | Description |
|----------|-------------|
| Penetration testing | Systematically probing a system for vulnerabilities within a defined scope |
| Vulnerability research | Discovering new (0-day) bugs in software |
| Social engineering | Testing whether humans in the organization can be tricked |
| Physical security testing | Attempting to gain unauthorized physical access to facilities |
| CTF competitions | Practicing offensive skills in controlled environments |

### Blue team (defensive)

Blue teamers protect, detect, and respond. They build the systems that make attacks harder and catch them faster.

| Activity | Description |
|----------|-------------|
| Security Operations Center (SOC) | 24/7 monitoring for suspicious activity |
| Incident response | Containing and investigating active breaches |
| Threat hunting | Proactively searching for hidden attackers |
| Security architecture | Designing systems that are hard to compromise |
| Compliance and auditing | Ensuring systems meet regulatory requirements |

### Purple team

Purple teams bridge the gap — red team findings directly feed into blue team improvements. Modern organizations increasingly use this collaborative model rather than treating offense and defense as separate silos.

### Why we teach with a red-team lens

This course focuses on offensive techniques because:
1. **You can't defend what you don't understand** — knowing how SQL injection works makes you write secure queries naturally
2. **Attacker mindset is transferable** — the "what could go wrong?" thinking applies to code review, architecture design, and DevOps
3. **It's engaging** — breaking things is a powerful motivator to understand how they work
4. **CTFs reward it** — the competition format tests offensive thinking directly

---

## The attack lifecycle

Real-world attacks follow a general pattern. Understanding this helps you see where each week's material fits:

```
1. Reconnaissance    → Gathering information about the target (Week 2: OSINT)
2. Scanning          → Probing for open ports, services, versions (Week 2: nmap)
3. Gaining access    → Exploiting a vulnerability to get in (Week 3: web attacks)
4. Maintaining access → Persistence, backdoors (Week 5)
5. Covering tracks   → Deleting logs, hiding presence (Week 5)
```

Defenders work to detect and block each stage. The earlier you catch an attacker, the less damage they do.

---

## Common career paths

Cybersecurity is a broad field. Here are paths you might pursue after this course:

| Career | What you do | Typical entry point |
|--------|------------|---------------------|
| **Penetration tester** | Break into systems legally, write reports | CTFs, eJPT/OSCP cert, bug bounties |
| **Security engineer** | Build and maintain security infrastructure | SWE background + security interest |
| **Security architect** | Design secure systems at scale | Senior engineering + threat modeling |
| **Incident responder** | Investigate and contain breaches in real-time | SOC analyst → IR team |
| **Forensic analyst** | Recover and analyze digital evidence | Forensics coursework, DFIR certifications |
| **AppSec engineer** | Find and fix vulnerabilities in code | Development background + OWASP knowledge |
| **Bug bounty researcher** | Find vulnerabilities in live products for rewards | Self-taught, platform reputation |
| **Security-aware developer** | Write secure code as part of a dev team | This course + strong programming skills |
| **GRC analyst** | Governance, risk, and compliance work | Business/policy background + security certs |

You don't need to choose now. This course gives you broad exposure; specialization comes with practice and preference.

---

## Legal and ethical baseline

This is not optional. These rules define the boundary between security research and criminal activity:

### The four rules

1. **Authorization** — Only test systems you own or have explicit written permission to test. "I was just learning" is not a legal defense.

2. **Scope** — Stay within agreed boundaries. If you're authorized to test a web app, don't pivot into the database server's operating system unless that's explicitly in scope.

3. **Responsible disclosure** — If you find a vulnerability, report it to the owner. Give them reasonable time to fix it before making any public disclosure. Many organizations have formal disclosure policies or bug bounty programs.

4. **Privacy** — Do not exfiltrate, store, or publish real personal data you encounter in labs or accidentally. Report it and move on.

### Legal frameworks (awareness level)

| Law/Framework | Jurisdiction | Relevance |
|---------------|--------------|-----------|
| IT Act, 2000 (India) | India | Unauthorized access (Sec 43, 66) carries penalties |
| CFAA | United States | Broad computer fraud law; even exceeding "authorized access" can be criminal |
| GDPR | EU | Handling personal data has strict rules |
| Bug bounty safe harbors | Various | Some companies explicitly protect researchers who follow their rules |

**CSOT labs are legal sandboxes.** The challenges, VMs, and infrastructure provided in this course are intentionally vulnerable and you have permission to attack them. Do not apply the same techniques to anything else without authorization.

---

## How this course is structured

Each week follows the same cycle:

```
Read modules → Practice on external platforms → Complete assignments → Weekend CTF
```

You are **not** expected to memorize every tool or technique. You **are** expected to:
- **Search** — Google error messages, read man pages, check Stack Overflow
- **Experiment** — Try commands with different flags; break things in your VM
- **Document** — Keep notes on what worked, what didn't, and what you learned
- **Collaborate** — Discuss approaches (not solutions) with classmates

### Note-taking recommendation

Keep a personal "security journal" — a markdown file or notebook where you record:
- Commands that solved problems
- Interesting techniques from readings
- Dead ends and why they didn't work
- Links to resources you want to revisit

This becomes invaluable during CTFs and after the course.

---

## Further reading

- [GeeksforGeeks — Introduction to ethical hacking](https://www.geeksforgeeks.org/ethical-hacking/introduction-to-ethical-hacking/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) — how enterprises think about security
- [OWASP Foundation](https://owasp.org/) — open-source application security community
- [Krebs on Security](https://krebsonsecurity.com/) — investigative journalism on cybercrime
- [RESOURCES.md](../RESOURCES.md) — full curated link collection for this course

---

## Next module

[digital-safety.md](digital-safety.md) — Practical operational security for your devices and accounts before we start offensive work.
