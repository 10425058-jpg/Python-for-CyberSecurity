# Deep Dive 09 — TCP/IP, sockets, DNS, TLS and network defensive programming

**Level:** intermediate · **Estimated study:** 12–16 hours.

## Scenario
You operate an approved local lab server. You need to understand why a client connects, how a packet differs from a message, and what TLS certificate verification really guarantees. You should never report an open port as proof of compromise.

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
