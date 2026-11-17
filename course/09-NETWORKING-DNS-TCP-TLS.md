# Deep Dive 09 — TCP/IP, sockets, DNS, TLS and network defensive programming

> **Hands-on:** [Chapter 09 Guided Lab](../lab-manual/09-GUIDED-LAB.md) · [100 worked answers](../solutions/by-exercise/README.md). Run negative tests and document limitations.

**Level:** intermediate · **Estimated study:** 12–16 hours.

## Scenario
You operate an approved local lab server. You need to understand why a client connects, how a packet differs from a message, and what TLS certificate verification really guarantees. You should never report an open port as proof of compromise.

## Masterclass — DNS validation has a time-of-check/time-of-use boundary

An application's "allowed URL" logic can appear correct while still contacting a forbidden destination. The problem is that a **hostname**, its **DNS response**, and the **actual connected peer address** are different facts. DNS can change between a preliminary check and connection, and an HTTP redirect can change the destination entirely. Treat each resolution/redirect as a new trust decision.

**Defender's question:** may a server fetch `https://updates.example.test/check`? A hostname allowlist is only one control. It must be paired with the right network egress restrictions and verification of where the client *actually connects*. A substring check like `"example.test" in url` is not authorization.

| Candidate URL | What a robust policy notices |
|---|---|
| `https://updates.example.test/check` | approved exact host, scheme and port |
| `http://updates.example.test/check` | wrong scheme |
| `https://updates.example.test.attacker.invalid` | hostname suffix is different |
| `https://updates.example.test@127.0.0.1/` | user-info tricks human readers |
| `https://updates.example.test:8443/` | unexpected port |
| HTTP redirect to `127.0.0.1` | must re-validate destination |

**Offline test — pure policy checks and a simulated DNS response:**

```python
# MASTERCLASS_RUNNABLE
from urllib.parse import urlsplit
import ipaddress

EXPECTED_HOST = "updates.example.test"

def approved_url(raw: str) -> bool:
    if type(raw) is not str or not 1 <= len(raw) <= 512:
        return False
    try:
        parsed = urlsplit(raw)
        return (parsed.scheme == "https"
                and parsed.hostname == EXPECTED_HOST
                and parsed.username is None
                and parsed.password is None
                and parsed.port in (None, 443)
                and not parsed.fragment)
    except ValueError:
        return False

def simulated_public_destination(address_text: str) -> bool:
    address = ipaddress.ip_address(address_text)
    return address.is_global

assert approved_url("https://updates.example.test/check")
for bad in (
    "http://updates.example.test/check",
    "https://updates.example.test.attacker.invalid/",
    "https://updates.example.test@127.0.0.1/",
    "https://updates.example.test:8443/",
):
    assert not approved_url(bad)
assert not simulated_public_destination("127.0.0.1")
assert not simulated_public_destination("169.254.169.254")
assert simulated_public_destination("8.8.8.8")
```

**What this code deliberately does *not* do:** it does not fetch the URL, follow redirects, resolve DNS, validate certificates, or prove that a connection is safe. `ipaddress.is_global` is a useful property but not a complete organizational egress policy. The string `updates.example.test` is an invented lab allowlist target. A production fetcher typically needs fixed approved destinations, restricted outbound network paths, careful resolution/connect handling and a maximum total response size/deadline.

**Separate concepts:** TCP connect success establishes reachability at one moment; TLS certificate validation can establish a server identity under a trust store and hostname rules; neither authorizes that server to receive sensitive user data. An API resource permission check must still happen at the application layer.

**Transfer exercise:** imagine the initial hostname resolves to a public IP but the actual connection uses a loopback IP. Which check was invalidated? Propose a design where the destination policy is enforced at the network boundary in addition to application validation. Explain why redirects need repeated policy checks.


## 1. From application data to packets

Think in layers:
1. **Application:** HTTP, DNS application messages, SSH, SMTP. These define meaning.
2. **Transport:** TCP (reliable ordered stream), UDP (datagrams with no built-in delivery guarantee).
3. **Internet:** IPv4/IPv6 addressing and routing.
4. **Link:** Ethernet/Wi-Fi delivery across one local segment.

A browser request is not "one packet." An HTTP response may cross multiple TCP segments, may be retransmitted, and may be encrypted by TLS. A packet capture can be incomplete due to capture loss or asymmetric routing.

### IP address versus hostname
`192.0.2.5` is an example IPv4 address in a documentation-reserved range. A hostname such as `example.com` maps to addresses through DNS; answers may change across time and location. A port is an endpoint number, not a statement about security posture.

```python
import ipaddress
address = ipaddress.ip_address("2001:db8::1")
network = ipaddress.ip_network("2001:db8::/32")
assert address in network
assert not ipaddress.ip_address("8.8.8.8") in ipaddress.ip_network("192.0.2.0/24")
```

Prefer `ipaddress` to string-based prefixes like `ip.startswith("192.168")`. Prefix strings are not CIDR semantics and are error-prone.

## 2. TCP mechanics

The TCP three-way handshake ordinarily exchanges SYN → SYN/ACK → ACK. A connection then carries an ordered byte stream. Sequence numbers, acknowledgments, retransmissions, receive windows and congestion control influence the transport. Closing involves FIN exchanges, while RST abruptly resets.

A `connect()` success means the TCP connection was established; it does **not** prove the remote application speaks the protocol you expect, uses trustworthy TLS or is vulnerable.

### One `recv` is not one message

```python
# Conceptual anti-pattern:
# data = sock.recv(1024)
# message = json.loads(data)  # MAY BE PARTIAL OR MULTIPLE MESSAGES
```

If your protocol requires a six-byte header, you must read *exactly six* bytes, then read an indicated bounded payload length. See [Deep Dive 04](04-BYTES-ENCODING-BINARY-PARSERS.md).

## 3. Local-only socket lab

Server in terminal A:
```bash
python -m http.server 8765 --bind 127.0.0.1
```

Client in terminal B:
```python
import socket

def local_connect(port: int, timeout: float = 1.0) -> bool:
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("port out of range")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex(("127.0.0.1", port)) == 0

print(local_connect(8765))
```

Test after shutting the server down. Expected: ordinarily `True` when the listener is up and `False` when not, subject to local firewall and race conditions.

### Timeouts and scope
A failed connection may mean refused, filtered, timed out, no route or temporary failure. A diagnostic should distinguish error categories when possible, and log request scope, timestamp, and confidence. Even local checks should avoid unlimited fan-out.

## 4. DNS: resolution is not permanent authorization

DNS record types include A, AAAA, CNAME, MX, TXT, NS, SOA and PTR. DNS answers can be cached and may change. A service that checks a user-controlled hostname once and later connects to a different resolved IP can be exposed to SSRF via DNS rebinding.

### Correct security model for URL fetchers
- Prefer a strict allowlist of approved service identities and destinations.
- Reject unsupported schemes, embedded credentials and unnecessary redirects.
- Revalidate **actual connected destination IPs** throughout redirects and changes.
- Enforce outbound network firewall/egress policy, not only application string checks.
- Prevent requests to link-local/cloud metadata endpoints unless explicitly required.
- Set timeouts, response-body caps, authentication and audit records.
- Recognize mixed IPv4/IPv6 and address normalization complexities.

A single regex or hostname suffix check is not sufficient to prevent SSRF.

## 5. TLS: authentication and encryption are distinct

TLS can provide confidentiality, integrity and **server authentication** when certificate validation and hostname verification succeed. Important concepts:
- Certificate chain to trusted roots.
- Subject Alternative Name and expected hostname.
- Expiration and acceptable algorithms.
- SNI, which helps virtual hosts choose a certificate.
- Forward secrecy, session resumption and protocol versions.
- Mutual TLS (both parties present certificates) for some enterprise services.

`ssl.create_default_context()` uses secure client defaults for ordinary hostname-validated TLS. **Never disable verification to make errors disappear.**

```python
import ssl
context = ssl.create_default_context()
assert context.check_hostname
assert context.verify_mode == ssl.CERT_REQUIRED
```

A trusted TLS connection does **not** mean that the requested user is authorized to view the resource. TLS authenticates the server endpoint under a trust model; application authorization is an independent layer.

### Certificates are not magical security indicators
A self-signed certificate can be appropriate in a controlled environment if explicitly trusted/pinned. A publicly trusted certificate is not proof that the application code has no vulnerabilities. Certificate revocation checking depends on client/platform policy.

## 6. HTTP requests and APIs

A request has a method, path, headers and optional body. A response has status, headers and body. Common codes:
- 200: success response.
- 201: created.
- 204: success with no response body.
- 301/302/307/308: redirects with differing method-preservation semantics.
- 400: invalid request.
- 401: unauthenticated.
- 403: authenticated/recognized but forbidden (in typical APIs).
- 404: not found; sometimes intentionally used to avoid resource enumeration.
- 429: rate limited.
- 500/502/503: server/gateway/unavailable errors.

Do not assume all 2xx bodies are JSON or that errors reveal trustworthy details. Verify content type, size and schema at client boundaries. Handle redirects and authentication carefully so tokens are not sent to unintended hosts.

## 7. Packet analysis versus packet crafting

Tools such as Scapy can inspect PCAP files and also transmit crafted packets. Begin with offline captures you produced in a VM. Learn:
- Ethernet frame header and EtherType.
- IPv4 header size, TTL, fragmentation fields.
- IPv6 extension headers and differences from IPv4.
- TCP flags, ports, sequence numbers and stream reconstruction.
- UDP length/checksum and datagram semantics.
- DNS transaction IDs, response codes and resolution behavior.
- TLS handshake metadata; encrypted application contents are not normally visible.

Scapy's `PcapReader` streams offline packets and avoids loading a large capture entirely into memory; it still needs resource caps and parser isolation for untrusted PCAPs.

## 8. Worked network observation report

Lab: You start a local server, issue one HTTP GET, stop the server and retry. A reasonable observation report includes:

| Field | Example |
|---|---|
| Scope | 127.0.0.1:8765, own machine |
| Client code | `socket` connect with one-second timeout |
| Time | 2026-01-01 10:00 UTC (synthetic) |
| Result while running | TCP connection established |
| Result after stop | refused/not reachable (environment-specific) |
| Conclusion | port reachability changed |
| **Not concluded** | no proof of vulnerability or compromise |

## 9. Exercises with verification
1. **TCP stream model:** explain how two `sendall` calls could be combined into one `recv`. **Answer:** TCP does not preserve application write boundaries.
2. **IPv6:** parse and normalize `2001:0db8:0000::1`. Expected: compressed canonical representation.
3. **TLS:** explain why `verify=False` can expose credentials to interception. **Answer:** removes authentication of the server identity.
4. **DNS:** describe a DNS rebinding problem and at least two independent mitigations.
5. **Packet triage:** use a *local* PCAP to count TCP vs UDP frames; compare with Wireshark and discuss dropped packets.

## Review quiz
What is the difference between TCP and UDP? Why is `recv(1024)` insufficient as an application parser? What does TLS establish? What does an HTTP 403 mean? Why does an open port not demonstrate a vulnerability?

**References:** [Python sockets](https://docs.python.org/3/library/socket.html), [Python SSL](https://docs.python.org/3/library/ssl.html), [Wireshark](https://www.wireshark.org/docs/), [OWASP SSRF](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).


## 10. A complete TCP framing walkthrough: why one `recv` cannot parse one message

A monitoring client connects to a locally owned service. The server sends two JSON records, each preceded by a four-byte big-endian unsigned length. TCP does not preserve the sender's `send` boundaries: the receiver may get a header fragment, an entire record, or bytes from multiple records in one read.

### Build a loopback-only echo lab

```python
import socket
import struct

MAX_FRAME = 4096

def receive_exact(sock: socket.socket, count: int) -> bytes:
    if type(count) is not int or not 0 <= count <= MAX_FRAME:
        raise ValueError("invalid byte count")
    parts = bytearray()
    while len(parts) < count:
        chunk = sock.recv(count - len(parts))
        if not chunk:
            raise EOFError("connection closed during frame")
        parts.extend(chunk)
    return bytes(parts)

def receive_message(sock: socket.socket) -> bytes:
    size = struct.unpack("!I", receive_exact(sock, 4))[0]
    if size > MAX_FRAME:
        raise ValueError("peer declared oversized frame")
    return receive_exact(sock, size)

def send_message(sock: socket.socket, body: bytes) -> None:
    if not isinstance(body, bytes) or len(body) > MAX_FRAME:
        raise ValueError("payload must be bounded bytes")
    sock.sendall(struct.pack("!I", len(body)) + body)
```

**Trace:** header `00 00 00 05` means 5 bytes. If `recv(4)` returns only 2 bytes, `receive_exact` loops until all 4 have arrived or EOF occurs. If the header declares 5000, reject *before reading or allocating that body*. The application still needs an overall deadline; `sock.settimeout(...)` alone is an idle-operation timeout, not always a job deadline.

### Socket lifecycle and scope

```python
# Local-only concept: use a test listener bound to 127.0.0.1,
# rather than arbitrary user-controlled remote hostnames.
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind(("127.0.0.1", 0))  # OS chooses a local ephemeral port
    server.listen(1)
    chosen_port = server.getsockname()[1]
    assert 1 <= chosen_port <= 65535
```

This snippet demonstrates binding, not a fully functioning server/client. In a real lab, run the listener and client as separate processes/tasks so one can accept while the other connects.

## 11. DNS and TLS trust-boundary cases

**Scenario:** a web app fetches a URL supplied by a caller. A regex checks that it begins with a familiar domain. Is this safe? No. URL parsers, redirects, DNS rebinding, IPv6 representation and actual connected IP can undermine naive checks. For secure server-side fetchers, prefer fixed destinations and network-level egress controls, then validate resolution and every redirect/connection.

| Control | Protects against | Does not by itself solve |
|---|---|---|
| Strict scheme/host allowlist | obvious unauthorized destinations | DNS rebinding |
| DNS resolution checks | unexpected IP ranges at that moment | changed answers at connect |
| Connect destination validation | unexpected final IP when correctly enforced | compromised trusted endpoint |
| Outbound firewall | prohibited internal address ranges | application authorization |
| TLS certificate validation | unauthenticated server identity | vulnerability of authenticated server |
| Per-request timeout + byte cap | stuck/excessive response | incorrect business logic |

TLS validates a connection to an expected server identity under trust-store assumptions. A TLS certificate does **not** say a service is authorized to receive your user's data. Correct authentication and authorization remain separate.

### Correctly interpret a port result

A successful TCP connection to 127.0.0.1:8765 proves only that a local listener accepted a handshake at that moment. It does not tell you the software version, application protocol, certificate configuration, ownership or exploitability. A failed connection could mean no listener, firewall filtering, timeout or transient network state.

## 12. Exercises with expected observations

**A:** Create a local client/server pair on loopback and send the same 5-byte message in 1-byte chunks. The reader must reconstruct the original bytes. Test premature EOF.

**B:** Demonstrate how `int.from_bytes(b"\x01\x00","big")` differs from `"little"`. Answer: 256 versus 1.

**C:** Write a report for an observed port 8765 accepting a connection, including what is *not* proven.

**D:** Threat-model an API accepting arbitrary URLs; list three application controls and one network-level control. Explain why each is distinct.

**E:** Check `ssl.create_default_context()` and explain the roles of CA trust, hostname verification and certificate expiration. Never disable verification just to pass a demo.

**F:** For an allowed hostname that resolves to both IPv4 and IPv6, explain why checks must consider **all** candidate addresses and the actual connected peer.

**Reference:** [Python socket docs](https://docs.python.org/3/library/socket.html), [OWASP SSRF guidance](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).
