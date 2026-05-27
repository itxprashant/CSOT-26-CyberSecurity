# Burp Suite

Burp Suite is the most widely used tool in web application security, and it'll be your home base for the rest of this week. At its core Burp is a **man-in-the-middle HTTP proxy**: your browser thinks it's talking to the server, the server thinks it's talking to the browser, and Burp sits between them, logging and letting you edit every byte. Once you've watched a single request flow through it, the abstract HTTP material from the previous module turns concrete.

This module is a practical walkthrough of Burp Community Edition: how to install it, how to wire it to your browser, what each major tab actually does, and the workflow patterns you'll use every day. We'll also cover the free alternatives — OWASP ZAP and `mitmproxy` — because they're better in some situations.

---

## What Burp actually is

Three things, sharing one window:

1. **A proxy.** Your traffic goes through it. You can stop, edit, and resume any request or response.
2. **A logger.** Everything you've already proxied is saved in the *HTTP history* and *Site map* and can be replayed.
3. **A toolbox.** Repeater, Intruder, Decoder, Comparer, Sequencer — each is a small purpose-built tool that operates on requests you've captured.

Community Edition is free and is what we use in the course. Professional adds an automated scanner, faster Intruder, save/restore of state, and a few QoL features. You will not need Pro for any CSOT material; PortSwigger Academy works fine with Community too.

---

## How a MITM proxy works

```
                  [no proxy]
Browser ────────── HTTP/HTTPS ─────────── Server

                  [with Burp]
Browser ──── HTTP/HTTPS ──── Burp ──── HTTP/HTTPS ──── Server
              ↑       ↓        ↑↓        ↑       ↓
              │       │     intercept    │       │
              │       │    log / edit    │       │
              └───────────────────────────────────┘
                         everything is visible
```

For HTTPS to work, the browser has to **trust Burp's certificate**, because Burp generates a new cert on the fly for every site you visit and signs it with its own internal CA. Without that trust, the browser will show a big "Your connection is not private" error. Installing the Burp CA is therefore step zero of HTTPS interception — and not a step you skip by clicking "Advanced → Proceed anyway", which can break some apps in subtle ways.

---

## Installation and first run

### Install

| OS | Method |
|----|--------|
| Kali / Parrot | Pre-installed: launch `burpsuite` |
| Debian / Ubuntu | [Download installer](https://portswigger.net/burp/communitydownload) and run; or `sudo apt install burpsuite` (older version) |
| WSL2 | Install Burp on the Windows host, point WSL traffic at the host IP |
| macOS / Windows | Download installer from PortSwigger |

Burp requires a JRE bundled into its installer — you don't need to manage Java separately.

### First launch

1. Choose **Temporary project** (Community can't save full projects).
2. Choose **Use Burp defaults**.
3. The main window opens on the **Dashboard** tab.

The proxy is already listening at `127.0.0.1:8080`. Confirm:

```bash
ss -tulpn | grep 8080
# tcp LISTEN 0 50 127.0.0.1:8080 0.0.0.0:* users:(("java",pid=12345,...))
```

If something else is bound to 8080, change Burp's listener in **Proxy → Proxy settings → Proxy listeners**.

---

## Browser setup

You have two reasonable options.

### Option A: Burp's built-in Chromium

**Proxy → Intercept → Open browser** spawns a pre-configured Chromium where the proxy and Burp CA are already wired up. This is the fastest path and the recommended one for the CSOT lab.

### Option B: Your real Firefox + FoxyProxy

When you want Burp on and off on demand:

1. Install the **FoxyProxy Standard** add-on in Firefox.
2. Add a profile: Title `Burp`, Type `HTTP`, Hostname `127.0.0.1`, Port `8080`.
3. Toggle FoxyProxy from the toolbar when you want to proxy traffic through Burp.

Why a separate browser profile or FoxyProxy: routing your *normal* browsing through Burp pollutes the history with every Slack heartbeat, ad-network call, and Reddit refresh, and it slows the browser. Keep your testing browser separate from your daily-driver browser.

### Install the Burp CA in Firefox

1. Make sure Burp is running and the proxy is active.
2. With FoxyProxy turned on, browse to `http://burp` (that exact URL).
3. Click **CA Certificate** to download `cacert.der`.
4. Firefox **Settings → Privacy & Security → Certificates → View Certificates → Authorities → Import**.
5. Select `cacert.der`, tick **Trust this CA to identify websites**.
6. Restart Firefox.

For Chromium-based browsers you import into the OS trust store (`Settings → Security → Manage Certificates → Authorities`). On Linux, system-wide installation is:

```bash
sudo cp cacert.der /usr/local/share/ca-certificates/burp.crt
sudo update-ca-certificates
```

After this, `curl` and `wget` will trust Burp's CA too — useful when scripting.

---

## The Burp window — major tabs

| Tab | Purpose | When you live here |
|-----|---------|--------------------|
| **Dashboard** | Activity overview, event log, issue activity | Rarely (Community is limited) |
| **Target** → **Site map** | Tree view of every host/path you've touched | Mapping the app, defining scope |
| **Target** → **Scope** | Whitelist of in-scope hosts | Always set this before doing anything |
| **Proxy** → **Intercept** | Stop the next request, let you edit, then forward or drop | Capturing the one request you want |
| **Proxy** → **HTTP history** | Everything that flowed through, replayable | Your timeline of the engagement |
| **Proxy** → **WebSockets history** | Same, for WS traffic | Real-time apps |
| **Proxy** → **Match and replace** | Auto-rewrite request/response headers and bodies | Inject test cookies, strip `Origin`, etc. |
| **Repeater** | Send one request, edit, resend — the daily driver | 70% of your time |
| **Intruder** | Fuzz a position in a request | Password lists, IDs, payload lists |
| **Sequencer** | Statistical analysis of token randomness | Auditing session IDs |
| **Decoder** | Base64, URL, hex, HTML, gzip — encode/decode | JWT inspection, payload prep |
| **Comparer** | Word-level diff between two blobs | "Same request, different cookie — what changed?" |
| **Extensions** (BApp Store) | Plugins | JWT Editor, Autorize, Logger++ |

---

## Scope — set this first, save yourself hours

Without scope, every browser tab pollutes Burp with thousands of third-party requests (Google Fonts, analytics, CDNs) and makes Intruder slower because it logs everything.

1. **Target → Scope settings**.
2. Add include rules: `http://127.0.0.1:5000` and `https://127.0.0.1:5000`. Use the **URL** field, not regex unless you need it.
3. Tick **"Use advanced scope control"** only when matching by regex.
4. Back in **Proxy → HTTP history**, set the filter to **Show only in-scope items**.

The Site map will now only grow with traffic for your target. Everything else is still proxied, just not loud.

```
Scope rule              Behavior in History filter
http://127.0.0.1:5000   ✅ shown
http://127.0.0.1:5000/* ✅ shown
http://192.168.1.10     ❌ hidden (out of scope)
https://google.com      ❌ hidden
```

---

## Proxy → Intercept

This is the famous "stop the request and let me edit it" feature.

```
1. Proxy → Intercept → set to ON
2. Browse to http://127.0.0.1:5000/login
3. Submit the login form
4. Burp captures the POST; you edit u/p in the request panel
5. Forward    → send the modified request onward
   Drop       → discard it (browser sees a connection failure)
   Action menu → "Send to Repeater" / "Send to Intruder" for follow-up work
```

**Pitfall:** Intercept stops *every* request including images, fonts, and XHR background pings. You'll spam-click **Forward** until you turn it off. Most of the time you work with **Intercept OFF**, browse freely, and use **HTTP history** to find the request you care about. Turn Intercept ON only when you need to modify a specific request you can predict.

---

## Repeater — the daily driver

Repeater is where 70% of your work happens. Workflow:

```
1. In HTTP history, right-click a request → "Send to Repeater" (Ctrl+R)
2. Switch to the Repeater tab — it's a two-panel view
3. Edit anything in the left panel (URL, method, headers, body)
4. Click "Send"
5. Read the response in the right panel
6. Tweak, send again, repeat
```

Each Repeater tab is independent. Open one per endpoint you're investigating. Rename tabs (double-click the label) so `/login`, `/search`, `/user?id=` aren't all called "Repeater 7".

### Repeater patterns you'll use this week

| Goal | Action |
|------|--------|
| Test a SQLi payload | Send `/login` to Repeater, change `u=admin'--`, send |
| Test IDOR | Send `/user?id=1` to Repeater, change to `id=2`, send |
| Reflect an XSS payload | Send `/search?q=hi` to Repeater, change `q` to `<script>alert(1)</script>`, send |
| Strip a header | Delete the `Origin` or `Referer` row, send |
| Change content type | Edit `Content-Type:` to `application/json` and re-encode body |
| Replay with a stolen cookie | Paste cookie from another session in the `Cookie:` header |

**CTF tip:** Repeater preserves your edit history per-tab. Click the dropdown next to "Send" to see your previous attempts and their responses — useful when you're not sure which payload finally worked.

---

## Intruder — fuzzing

Intruder takes one request, marks positions to vary, and replays it with many payloads. Community Edition rate-limits Intruder (slow but functional); Pro removes the throttle.

### The four attack types

| Attack | What it does | Use when |
|--------|--------------|----------|
| **Sniper** | One payload set; iterates one position at a time | Single param fuzzing (`?id=§§`) |
| **Battering ram** | One payload set; same value goes into all marked positions at once | Same value in two fields (e.g., username = password) |
| **Pitchfork** | Multiple payload sets, one per position; iterates in parallel (lockstep) | Known username:password pairs (creds.txt with both columns) |
| **Cluster bomb** | Multiple payload sets, one per position; tries every combination | Username list × password list |

```
Sniper:          [user1, user2, user3]      → 3 requests
Battering ram:   [pwd1, pwd2]               → 2 requests (same value in both positions)
Pitchfork:       [u1,p1], [u2,p2], [u3,p3]  → 3 requests (lockstep)
Cluster bomb:    users × passwords          → N × M requests
```

### Walking through an Intruder run

1. Send a request to Intruder (Ctrl+I).
2. **Positions** tab — clear auto-marks, manually mark each position with `§` (Add §).
3. **Payloads** tab — choose a payload set (Simple list, Brute forcer, Numbers, Runtime file).
4. Set **Payload processing** (URL-encode? Hash? Base64?) if needed.
5. **Settings** tab — **Grep — Match** lets you flag responses containing specific strings ("Welcome", "csot26{", "error in your SQL").
6. **Start attack**.
7. Sort results by status code, response length, or your grep marker. Outliers are usually the interesting ones.

Length is the most reliable signal: a successful login produces a different-sized response than a failed one even if both return 200. Burp shows length per row.

**Gotcha:** Community's Intruder is throttled to roughly one request per second. Don't use it for 100k-entry rockyou.txt — use `ffuf` or `hydra` for raw speed and reach for Intruder when you need its precision.

---

## Decoder

A standalone encode/decode pane. It accepts pasted text and a stack of operations.

| Operation | Direction | Notes |
|-----------|-----------|-------|
| URL | Encode/Decode | `%XX` |
| HTML | Encode/Decode | `&entity;` |
| Base64 | Encode/Decode | Watch padding |
| Base64-URL | Manual | JWT segments use `-`/`_` instead of `+`/`/` |
| ASCII Hex | Encode/Decode | `48 65 6c 6c 6f` |
| Gzip | Decode | Handy for `Content-Encoding: gzip` bodies |

JWT walkthrough: paste a token, split on the dots, base64-decode the first two segments. The header tells you the algorithm; the payload tells you the claims. We cover JWT inspection in depth in [jwt-and-apis.md](jwt-and-apis.md).

---

## Comparer

Highlights word- and byte-level differences between two payloads. Send two responses to Comparer (right-click → Send to Comparer) and pick **Words** or **Bytes**.

Use case: "I sent the same request with two different `?id=` values and one came back 20 bytes shorter — what changed?"

---

## Sequencer (brief)

Sequencer captures many tokens (session cookies, password-reset URLs, etc.) and runs FIPS-style randomness tests on them. If a token has only 30 bits of entropy you should be able to spot it here. Community works for this; Pro produces nicer reports.

Most of the time you won't need Sequencer for a CTF, but it's the right tool to reach for when an app uses a custom session ID generator.

---

## Match and replace

**Proxy → Match and replace** lets Burp automatically rewrite requests or responses based on rules you define. Useful patterns:

| Rule | Effect |
|------|--------|
| Replace request header `User-Agent: .*` with `User-Agent: csot-test/1.0` | Identify yourself politely |
| Replace request header `Cookie: .*` with `Cookie: session=ATTACKER` | Browse as another user automatically |
| Replace response header `Content-Security-Policy: .*` with empty | Disable CSP for testing XSS payloads in a permissive sandbox |
| Replace response body `secure: true` with `secure: false` | Flip a client-side gate |

Match-and-replace only applies to in-scope traffic by default. Keep it that way — global rewriting breaks the rest of the internet for your testing browser.

---

## Recommended Burp extensions

From the BApp Store (Extensions tab → BApp Store):

| Extension | What it adds |
|-----------|--------------|
| **JWT Editor** | Decode, edit, re-sign JWTs in-place inside Repeater |
| **Logger++** | Faster, more searchable history with column filters |
| **Autorize** | Replays every request as another user to spot broken access control |
| **Param Miner** | Discovers hidden parameters and headers |
| **Hackvertor** | Inline encoding tags inside Repeater (e.g., `<@base64>data<@/base64>`) |

Some require Pro (e.g., Active Scan++). Community gives you a huge subset for free.

---

## A complete worked example — IDOR on the lab

```
1. docker compose up -d --build           # ../../CTFs/week-03/_infra/
2. Open Burp's built-in browser
3. Browse to http://127.0.0.1:5000/user?id=1
   → response: {"name":"Alice","note":"public"}
4. Switch to Proxy → HTTP history → find the GET /user?id=1
5. Right-click → Send to Repeater (Ctrl+R)
6. In Repeater, change `id=1` to `id=2`
7. Send
   → response: {"name":"Bob","secret":"csot26{insecure_direct_object_reference}"}
```

Same flow for the XSS challenge:

```
GET /search?q=<script>alert(1)</script>   → response contains FLAGS["xss"]
```

You're now doing in 30 seconds what would have been a four-step debugging session in your terminal.

---

## Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Big "Connection is not private" page | Burp CA not trusted | Install it: browse to `http://burp` while proxied, import `cacert.der` into Firefox or OS trust store |
| Browser shows "no internet" | Intercept is ON, requests piling up | Toggle Intercept OFF and re-issue |
| HTTPS sites die silently in non-Burp browser | Forgot to disable proxy after Burp is closed | Toggle FoxyProxy off |
| Site map is huge with unrelated noise | Scope not set | Add target to scope and filter |
| Intruder is painfully slow | Community throttle | Use `ffuf` for raw speed; keep Intruder for surgical fuzz |
| Mobile app refuses to talk through Burp | Certificate pinning | Use Frida / objection on a rooted device, or test the API directly with `curl` |
| WebSocket traffic missing | WebSocket interception disabled | Proxy settings → "Intercept WebSocket messages" |
| Burp crashes / sluggish | Default JVM heap | Edit launcher: `java -Xmx2g -jar burp.jar` |

---

## Mobile testing in 30 seconds

Phones don't trust your laptop's Burp CA by default. Two paths:

1. **System-trust the CA.** Easy on iOS (install profile, then enable in Trust Store) and pre-Android-7 (install in user store). Modern Android requires rooting or a debug build that opts into user CAs via `network_security_config.xml`.
2. **Defeat certificate pinning.** Frida + Objection (`objection -g com.example.app explore`, then `android sslpinning disable`) on a rooted device. This is a step beyond what CSOT requires.

Whatever you do — the lab API is reachable directly. You can replay every endpoint with `curl` and skip the mobile dance entirely.

---

## Free alternatives

Burp Community is great. It is not the only game in town.

| Tool | Strength | Weakness |
|------|----------|----------|
| **OWASP ZAP** | Fully open-source, scriptable, has an active scanner without paywall | UI feels heavier; some pentesters find it less ergonomic |
| **mitmproxy** | Terminal-first, Python-scriptable, ideal for automation | Less hand-holding for fuzz workflows |
| **Caido** | New, fast, written in Rust, free tier | Smaller ecosystem; still evolving |

A real engagement often uses two tools in parallel: Burp for hands-on, ZAP or `mitmproxy` for automation.

### mitmproxy in two commands

```bash
mitmproxy --listen-port 8080 --mode regular           # interactive TUI
mitmweb --listen-port 8080                            # browser UI on :8081
```

Same MITM principle, no GUI overhead. Excellent for CI pipelines and headless scanning.

---

## Ethics and legality

The proxy itself is legal. What you do with it determines whether you're testing or attacking.

- **CSOT lab** (`127.0.0.1:5000`) — authorized, attack freely.
- **PortSwigger Academy** — labs run on portswigger-net.web-security-academy.net subdomains and are authorized for your account.
- **HackTheBox / TryHackMe** — authorized while you're on their VPN.
- **Your own deployed apps** — fine.
- **A friend's website "to help them out"** — only with **written** permission and a defined scope. "I asked them on WhatsApp" is not written permission.
- **Anything else** — unauthorized, illegal under the IT Act §43/§66, CFAA in the US, equivalents elsewhere.

A proxy logs everything you touch. If you accidentally browse to your bank while Burp is on, you'll have your real session in HTTP history. Clear projects between engagements, and never share a Burp save file.

---

## What to drill before moving on

1. Capture `GET /` of the lab and view it in HTTP history.
2. Send `GET /user?id=1` to Repeater, change to `id=2`, recover the IDOR flag.
3. Run a 10-payload Intruder Sniper on `/login` with usernames `[admin, root, guest, …]` and password `anything`. Sort by response length.
4. Decode the lab's `role` cookie in Decoder (it's plain ASCII — no encoding — but try the workflow).
5. Set up Match-and-replace to add header `X-CSOT-Tester: yourname` to every request and confirm it shows up in HTTP history.

If you can do all five smoothly, you're ready for the conceptual map.

---

## Further reading

- [PortSwigger — Burp documentation](https://portswigger.net/burp/documentation) — official.
- [PortSwigger Web Security Academy](https://portswigger.net/web-security) — free labs designed around Burp.
- [OWASP ZAP getting started](https://www.zaproxy.org/getting-started/) — for the alternative.
- [mitmproxy docs](https://docs.mitmproxy.org/stable/) — TUI proxy that scripts beautifully.

---

## Next module

[owasp-top10.md](owasp-top10.md) — the conceptual map of web vulnerabilities. Now that you can intercept and modify any HTTP request, here are the bug classes you'll be looking for.
