# HTTP fundamentals

Every web vulnerability you'll meet this week — SQL injection, XSS, IDOR, CSRF, broken auth — is delivered over HTTP. Before you can break or defend a web app, you need to read an HTTP exchange as fluently as a Linux command. This module is the layer-by-layer reference you'll come back to whenever a request "looks weird in Burp" and you have to explain why.

HTTP is a stateless, plain-text request/response protocol. Stateless means the server forgets about you after each request, so the entire mechanism of "logged in" is bolted on top via cookies, headers, and tokens. Plain-text means anyone on the wire who isn't blocked by TLS can read and modify what you send — which is why HTTPS is non-negotiable in production and why your interception proxy (Burp) can sit in the middle and edit traffic at all.

---

## Anatomy of a request

```
┌────────────── request line ──────────────┐
GET /search?q=hello HTTP/1.1                ← method, path+query, version
Host: 127.0.0.1:5000                        ← MANDATORY in HTTP/1.1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) ← who's asking
Accept: text/html,application/xhtml+xml
Accept-Language: en-US,en;q=0.9
Cookie: session=eyJ1c2VyIjoiZ3Vlc3QifQ     ← state lives here
Referer: http://127.0.0.1:5000/             ← previous page
Connection: keep-alive
                                            ← blank line = end of headers
                                            ← body would go here (POST/PUT)
```

A few things are easy to miss:

- The **request line** has three parts: method, *path + query*, version. The query string (`?q=hello`) is part of the URL, not a separate header.
- The blank line between headers and body is **mandatory**. Forgetting it is the most common bug when you talk HTTP by hand with `nc`.
- `Host:` is required because one IP can serve many virtual hosts. Strip it and the server doesn't know which site you wanted.

### Anatomy of the response

```
HTTP/1.1 200 OK                             ← status line
Server: nginx/1.25.3                        ← who answered (often leaks version)
Date: Wed, 27 May 2026 18:30:00 GMT
Content-Type: text/html; charset=utf-8       ← how to interpret body
Content-Length: 187
Set-Cookie: session=abc123; HttpOnly; Path=/ ← server hands you state
X-Frame-Options: DENY
                                            ← blank line
<html>…response body…</html>
```

The **status line** is `version  code  reason-phrase`. The reason phrase is for humans; tools only look at the numeric code.

---

## Methods (verbs)

| Method | Idempotent? | Body? | Typical use | Security note |
|--------|-------------|-------|-------------|---------------|
| `GET` | Yes | No (RFC) | Read a resource | Never use for state changes — gets logged in history, referer, CDNs |
| `POST` | No | Yes | Create / submit form / RPC | The catch-all; check CSRF protections |
| `PUT` | Yes | Yes | Replace a resource by ID | Often the IDOR vector on REST APIs |
| `PATCH` | No | Yes | Partial update | Same — check object-level auth |
| `DELETE` | Yes | Optional | Remove a resource | Authz check absolutely required |
| `HEAD` | Yes | No | Same as GET, response has no body | Cheap way to read headers |
| `OPTIONS` | Yes | No | Ask what's allowed (CORS preflight) | Often reveals enabled methods |
| `TRACE` | Yes | No | Echo request back (debugging) | Disable in production; XST risk |
| `CONNECT` | No | No | Open tunnel (used by proxies for HTTPS) | Should be locked down on web servers |

**Idempotent** means "running it N times has the same effect as running it once". That matters because browsers, CDNs, and retry layers will silently repeat `GET`/`PUT`/`DELETE`. If a `GET /delete-account` actually deletes the account, a single page reload nukes it twice.

**Gotcha:** Many frameworks accept `POST` with a `_method=PUT` field, or honor an `X-HTTP-Method-Override` header. This is how testers sometimes turn a `GET` into a `DELETE` against badly configured servers.

---

## Status codes

There are exactly five classes. Memorize the class, look up the specific code as needed.

| Class | Meaning |
|-------|---------|
| `1xx` | Informational (rare in app code) |
| `2xx` | Success |
| `3xx` | Redirect |
| `4xx` | Client error (you did something wrong) |
| `5xx` | Server error (server did something wrong) |

| Code | Meaning | Tester's read |
|------|---------|---------------|
| `200 OK` | Success | "Whatever I sent, the server accepted." |
| `201 Created` | New resource made | Look in `Location:` for the URL of the new resource |
| `204 No Content` | Success, no body | Common on `DELETE`/`PUT` |
| `301 Moved Permanently` | Redirect, method **may** change to GET | Cached forever — careful when testing |
| `302 Found` | Redirect, method **may** change to GET | The classic "POST then redirect" pattern |
| `303 See Other` | Redirect, method **must** become GET | Cleanest "POST/Redirect/GET" |
| `304 Not Modified` | Cached copy is still good | Caching response, no body |
| `307 Temporary Redirect` | Redirect, method **preserved** | A POST stays a POST |
| `308 Permanent Redirect` | Redirect, method **preserved** | A POST stays a POST, cached |
| `400 Bad Request` | Malformed input | Often hides parser bugs / SQL syntax errors |
| `401 Unauthorized` | Authentication missing or invalid | "Who are you?" — try sending a token |
| `403 Forbidden` | You authenticated, but you're not allowed | "I know you, you can't do that." IDOR territory |
| `404 Not Found` | No such resource | …or the server is lying to hide one (use `405`/`200` to differentiate) |
| `405 Method Not Allowed` | Wrong verb | Try other methods (`OPTIONS` will list them) |
| `429 Too Many Requests` | Rate limited | Slow your scanner; check `Retry-After` |
| `500 Internal Server Error` | Server blew up | Look at the response body — stack traces and SQL errors leak here |
| `502 / 503 / 504` | Upstream / overloaded / gateway timeout | Often points at a backend distinct from the edge |

**Tester tip:** A `401` and a `403` look the same to a user, but they tell you very different things. `401` means "log in first." `403` means "I know who you are, you can't have this." When you flip from `401` to `403` after sending a session cookie, that's the moment to start probing horizontal/vertical access control.

The 301 vs 302 vs 307 vs 308 distinction matters most when you `POST` to a URL that then redirects: 301/302 historically let the browser drop you to a `GET`, dumping your body; 307/308 force the method (and body) through. Bug-bounty hunters have found auth-bypass chains by exploiting exactly this confusion.

---

## Headers that matter for security

Headers are where most of the "is this app safe?" answer lives. Every Burp session begins with reading the headers.

### Set-Cookie attributes

A cookie is just `name=value`. The attributes that follow control its security:

```
Set-Cookie: session=eyJ1IjoxfQ;
            Domain=example.com;
            Path=/;
            Expires=Wed, 27 May 2026 23:00:00 GMT;
            Max-Age=3600;
            HttpOnly;
            Secure;
            SameSite=Lax
```

| Attribute | What it does | Why it matters |
|-----------|--------------|----------------|
| `Domain` | Which hosts can read the cookie | Too broad = subdomain takeover risk |
| `Path` | Which paths get the cookie | Defense-in-depth, rarely the main control |
| `Expires` / `Max-Age` | When the cookie dies | Long-lived session = bigger blast radius if stolen |
| `HttpOnly` | JS can't read it via `document.cookie` | Stops XSS from stealing the cookie. **Must be set on session cookies.** |
| `Secure` | Only sent over HTTPS | Stops the cookie from leaking over plaintext HTTP |
| `SameSite=Strict` | Cookie not sent on **any** cross-site request | Blocks CSRF, breaks some legitimate flows |
| `SameSite=Lax` | Cookie sent on top-level navigation only (default in modern browsers) | Sensible default |
| `SameSite=None` | Always sent cross-site (requires `Secure`) | Use only when you really need cross-site cookies |

The CSOT lab in [../../CTFs/week-03/session-cookie/](../../CTFs/week-03/session-cookie/) deliberately sets a cookie with `httponly=False` so you can read it from JavaScript — confirm that yourself with the browser dev console.

### Defensive response headers

| Header | Purpose | Example |
|--------|---------|---------|
| `Content-Security-Policy` | Whitelist where scripts/styles/images can come from. The single strongest XSS mitigation. | `default-src 'self'; script-src 'self' 'nonce-abc'` |
| `Strict-Transport-Security` (HSTS) | Force HTTPS for N seconds | `max-age=31536000; includeSubDomains; preload` |
| `X-Frame-Options` | Stop your site being iframed by another (clickjacking) | `DENY` or `SAMEORIGIN` |
| `X-Content-Type-Options` | Stop browsers from sniffing MIME types | `nosniff` |
| `Referrer-Policy` | Control what the `Referer:` header leaks | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Disable APIs (camera, mic, geolocation) | `camera=()` |
| `Cross-Origin-Resource-Policy` | Restrict who can embed your resources | `same-site` |
| `Cache-Control` | Stop sensitive responses being cached | `no-store` on anything with personal data |

**Recon pattern:** the first thing any web tester does is `curl -I` the target. Missing `CSP`, `HSTS`, `X-Frame-Options` is not itself an exploit, but it tells you the team's security posture and what defenses you don't have to bypass.

### CORS (Cross-Origin Resource Sharing) headers

CORS is the browser's mechanism for allowing controlled cross-origin requests. The server, not the client, decides who's allowed.

| Header | Purpose |
|--------|---------|
| `Access-Control-Allow-Origin` | Which origins can read responses |
| `Access-Control-Allow-Credentials` | Whether cookies are sent on cross-origin requests |
| `Access-Control-Allow-Methods` | Which methods are allowed |
| `Access-Control-Allow-Headers` | Which custom headers the client may send |

The single most common misconfiguration: `Access-Control-Allow-Origin: *` **with** `Access-Control-Allow-Credentials: true`. Browsers actually reject that combination, but a custom reflective version — "echo whatever Origin you receive" — is a real bug class that lets a malicious page read authenticated responses.

### Request headers worth knowing

| Header | What it carries | Test ideas |
|--------|-----------------|------------|
| `Host` | The virtual host being addressed | Tamper for **host header injection**, password-reset poisoning |
| `Authorization` | `Basic base64(user:pass)` or `Bearer <jwt>` | Drop, swap, or modify the token |
| `Cookie` | Session state | Tamper, replace with another user's, encode tricks |
| `X-Forwarded-For` / `X-Real-IP` | Client IP behind a reverse proxy | Spoof for IP-based ACLs |
| `Referer` | Previous URL | Used by CSRF defenses and analytics — try removing it |
| `Origin` | The page's origin (CORS / Fetch) | Mandatory for non-GET cross-origin checks |
| `Content-Type` | What the body is | Switch from `application/json` to `application/x-www-form-urlencoded` to bypass naive parsers |
| `Content-Length` | Body size | Mismatching it is the basis of **HTTP request smuggling** |

---

## Request body formats

Three formats cover ~99% of what you'll see:

### `application/x-www-form-urlencoded`

What HTML forms send by default.

```
POST /login HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/x-www-form-urlencoded
Content-Length: 19

u=admin&p=hunter2
```

Each field is URL-encoded. Spaces become `+` (or `%20`); special characters become `%XX`.

```bash
curl -X POST http://127.0.0.1:5000/login \
  -d "u=admin&p=hunter2"
```

### `application/json`

What modern APIs use.

```
POST /api/notes HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/json
Content-Length: 42

{"title":"meeting","tags":["work","urgent"]}
```

```bash
curl -X POST http://127.0.0.1:5000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"hello","role":"admin"}'
```

### `multipart/form-data`

For file uploads or when fields contain binary data.

```
POST /upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----xYz

------xYz
Content-Disposition: form-data; name="title"

my photo
------xYz
Content-Disposition: form-data; name="file"; filename="evil.php"
Content-Type: image/png

<?php system($_GET['c']); ?>
------xYz--
```

```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "title=my photo" \
  -F "file=@./evil.php;type=image/png"
```

**CTF tip:** Many parsers trust the `Content-Type` you declare per-part. Uploading a PHP webshell with `Content-Type: image/png` defeats naive extension/MIME filters.

---

## Sessions, tokens, and the stateless reality

Because HTTP is stateless, "logged in" is always implemented one of three ways:

| Mechanism | How it works | Where the secret lives |
|-----------|--------------|------------------------|
| **Server-side session** | Opaque ID in cookie; server looks up state in Redis/DB | Server. Cookie just maps to it. |
| **Stateless token (JWT)** | Signed JSON in `Authorization: Bearer` | Client. Server only verifies the signature. |
| **API key** | Long static string sent with every request | Client. Server matches against a stored value. |

We'll spend a whole module on JWTs in [jwt-and-apis.md](jwt-and-apis.md). For now, remember:

- Anything sent by the browser is **attacker-controllable**. The server must verify it.
- The session cookie or token is the single highest-value secret in the app. Steal it and you're the user.
- Tokens without expiry are tokens that never get invalidated when revoked.

---

## Redirects and how clients follow them

A `3xx` response with a `Location:` header tells the client to fetch a different URL. The trick is what happens to the original method and body:

| Code | Method preserved on redirect? | Body preserved? | Typical use |
|------|-------------------------------|-----------------|-------------|
| `301` | Historically: no (often becomes GET) | No | "Page permanently moved" |
| `302` | Historically: no (often becomes GET) | No | Default redirect |
| `303` | No (always becomes GET) | No | POST/Redirect/GET |
| `307` | Yes | Yes | "Try this URL with the same request" |
| `308` | Yes | Yes | Permanent variant of 307 |

```bash
curl http://127.0.0.1:5000/old-path        # stops at the 302, shows you the Location
curl -L http://127.0.0.1:5000/old-path     # -L = follow redirects
curl -L -v http://127.0.0.1:5000/old-path  # see the whole chain
```

**Gotcha:** `curl` does **not** follow redirects by default. Many bugs (e.g., "the app silently sets a cookie on the way to login") are invisible if you don't add `-L -v` or check `Location:` manually.

**Open-redirect**: any endpoint that takes a user-controlled URL and sends a `Location:` header to it (`/logout?next=https://evil.tld`) is a CSRF and phishing helper. Look for one wherever you see `?next=`, `?redirect=`, `?return_url=`.

---

## Conditional requests and caching

These don't carry obvious vulns, but they explain weird Burp behavior.

| Header | Direction | Purpose |
|--------|-----------|---------|
| `ETag` | Response | Opaque version tag for the resource |
| `If-None-Match` | Request | "Only respond if the ETag changed." 304 if not. |
| `Last-Modified` | Response | Timestamp |
| `If-Modified-Since` | Request | "Only respond if newer than this." |
| `Cache-Control` | Both | `no-store`, `no-cache`, `max-age=N`, `private`, `public` |
| `Vary` | Response | Tells caches which request headers affect the response |

A bug pattern called **web cache deception** abuses the fact that `/profile/cat.jpg` looks cacheable to a CDN even when it actually serves your private profile data. We won't exploit it this week, but be aware that caching and authorization interact.

---

## HTTP versions in 90 seconds

| Version | Year | Key change | Tester impact |
|---------|------|-----------|---------------|
| HTTP/0.9 | 1991 | Single line `GET /path` | Historical curiosity |
| HTTP/1.0 | 1996 | Headers, status codes | Almost gone |
| HTTP/1.1 | 1997 | `Host`, keep-alive, chunked encoding, pipelining | The protocol Burp shows you by default |
| HTTP/2 | 2015 | Binary framing, multiplexing over one TCP connection, header compression (HPACK) | Burp displays it as 1.1-equivalent text; smuggling bugs exist |
| HTTP/3 | 2022 | Over QUIC (UDP), no head-of-line blocking | Browsers use it; intercepting proxies often downgrade to HTTP/2 |

For learning, treat everything as HTTP/1.1. Burp normalizes HTTP/2 traffic so the readable representation is the same.

---

## Where TLS fits

HTTPS = HTTP **inside** TLS. The TLS handshake happens once per connection:

```
1. ClientHello   → supported ciphers, SNI (target hostname), random
2. ServerHello   ← chosen cipher, random
3. Server sends certificate (signed by a CA your OS trusts)
4. Key exchange (ECDHE) — both sides derive the same shared secret
5. Finished      ↔ encrypted application data flows
```

Why this matters as a tester:

- **SNI** (Server Name Indication) is sent in clear, so a network observer sees *which* HTTPS site you visited, even if they can't see the content.
- **Certificate pinning** breaks Burp by design. Mobile apps and some desktop clients refuse to use your local CA. We'll handle that in [burp-suite.md](burp-suite.md).
- A **certificate error** in Burp is almost always Burp's CA not being trusted by the browser. The fix is installing the Burp CA, not clicking through.

---

## A complete worked exchange

Here's the lab `/login` (the SQLi challenge), captured end to end with `curl -v`:

```
$ curl -v -X POST http://127.0.0.1:5000/login \
       -d "u=admin&p=anything"

* Connected to 127.0.0.1 (127.0.0.1) port 5000
> POST /login HTTP/1.1
> Host: 127.0.0.1:5000
> User-Agent: curl/8.5.0
> Accept: */*
> Content-Length: 18
> Content-Type: application/x-www-form-urlencoded
>
* upload completely sent off: 18 bytes
< HTTP/1.1 401 UNAUTHORIZED
< Server: Werkzeug/3.0.1 Python/3.12.0
< Date: Wed, 27 May 2026 18:30:00 GMT
< Content-Type: text/html; charset=utf-8
< Content-Length: 18
<
Invalid credentials
* Connection #0 to host 127.0.0.1 left intact
```

Every part of this is visible in Burp's *Proxy → HTTP history* tab too, just in a nicer UI. Recognize the structure here and you'll recognize it there.

---

## curl recipes for the rest of the week

```bash
curl -I http://127.0.0.1:5000/                            # headers only (HEAD)
curl -v -X POST http://127.0.0.1:5000/login \
     -d "u=admin&p=test"                                   # verbose POST

curl -b 'role=admin' http://127.0.0.1:5000/                # send a cookie
curl -c cookies.txt -b cookies.txt http://127.0.0.1:5000/  # cookie jar (across requests)

curl -L http://127.0.0.1:5000/old                          # follow redirects
curl --max-redirs 0 -I http://127.0.0.1:5000/old           # see only the first hop

curl -H 'X-Forwarded-For: 127.0.0.1' http://target/admin   # spoof source IP header
curl -H 'Content-Type: application/json' \
     -d '{"role":"admin"}' http://127.0.0.1:5000/api/notes # JSON body

curl --resolve target.tld:443:1.2.3.4 https://target.tld/  # force a specific IP
curl --proxy http://127.0.0.1:8080 -k http://target/       # route through Burp (-k = ignore Burp CA)
curl -G --data-urlencode 'q=<script>alert(1)</script>' \
     http://127.0.0.1:5000/search                           # safely encode a tricky query
```

The `--proxy http://127.0.0.1:8080` flag is the bridge to the next module. Anything you can `curl`, you can throw through Burp and inspect.

---

## Gotchas worth tattooing

- A `200` with an empty body looks fine in `curl` until you check the **content length**. Compare `Content-Length` against what you saw — discrepancies hint at smuggling bugs.
- Headers are case-insensitive. `Cookie:` and `cookie:` are the same header.
- Cookies in your browser don't always match what the server sees: extensions, ad-blockers, and HTTPS-only flags filter them.
- The `Referer` header is **literally misspelled** in the spec ("referrer" vs "referer"). Don't lose 30 minutes to a typo.
- `OPTIONS` to any endpoint will usually list the methods allowed there. Free reconnaissance.
- A web app's behavior on `POST /` versus `GET /` is often very different. Try both.

---

## What you should be able to do now

- Write a raw HTTP request with `nc` or `curl` from memory.
- Read a response and identify every part: status, headers, cookies, body.
- Name the cookie attributes that stop XSS-stolen sessions and CSRF.
- Predict whether a redirect drops or keeps the request body.
- Recognize when a `Set-Cookie:` is missing `HttpOnly`, `Secure`, or `SameSite`.
- Send a tampered cookie or header through `curl`.

If any of that is shaky, replay the lab's `/login`, `/search`, and `/user?id=1` with `curl -v` and watch the bytes. Then move on.

---

## Further reading

- [MDN — HTTP overview](https://developer.mozilla.org/en-US/docs/Web/HTTP) — best free reference for every header.
- [RFC 9110 — HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110) — the spec, surprisingly readable.
- [OWASP — Secure headers](https://owasp.org/www-project-secure-headers/) — what every response should send.
- [PortSwigger — HTTP basics](https://portswigger.net/web-security/essential-skills) — companion to the Web Security Academy.

---

## Next module

[burp-suite.md](burp-suite.md) — turn everything you just read into a workflow. Burp lets you intercept, edit, replay, and fuzz the requests we've been describing, and it'll be your home for the rest of the week.
