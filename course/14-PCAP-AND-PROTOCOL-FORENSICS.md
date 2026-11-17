# Deep Dive 14 — Offline packet captures and Python protocol forensics

**Level:** intermediate → advanced · **Estimated study:** 10–14 hours.

## Learning outcome
Inspect offline packet captures, extract bounded metadata, reconstruct basic flow statistics, understand why encrypted or lost data limits conclusions, and write a report that does not exaggerate what a capture proves.

## 1. A packet capture is evidence, not ground truth

PCAP/PCAPNG files record captured packets and timestamps. Capture quality depends on interface, filter, buffer, link type, packet truncation (snap length), clock and network path. Some traffic may never appear in the file. A tool must not assume that all conversations are complete.

**Legal/operational scope:** sniffing third-party traffic can reveal passwords, private messages and other sensitive data. Only use captures from a VM or systems you own or are explicitly authorized to monitor.

## 2. Layers and important fields

### Ethernet
Destination MAC, source MAC, EtherType. Not every capture includes an Ethernet header (e.g. loopback or special link layers).

### IPv4
Version, header length, total length, identification, flags, fragment offset, TTL, protocol, header checksum, source and destination addresses.

### IPv6
Version, traffic class, flow label, payload length, next-header, hop limit and 128-bit addresses. Extension headers and fragmentation are not laid out like IPv4.

### TCP
Source/destination ports, sequence/acknowledgment numbers, flags, window size, options and payload. TCP flags often include SYN, ACK, FIN, RST, PSH and URG; interpretations must consider direction and state.

### UDP
Ports, length, checksum and payload. UDP doesn't promise reliable delivery or ordering.

### DNS
Query name/type, response code, record type and TTL. A burst of NXDOMAIN responses may reflect a misconfiguration, generated names or suspicious activity, not necessarily malicious behavior.

### TLS
Handshake messages may reveal certificates and some metadata, depending on protocol version and privacy mechanisms. Application records are encrypted; a normal packet capture does not expose HTTPS plaintext.

## 3. Basic Scapy workflow (offline only)

```python
# Optional dependency: pip install scapy
from collections import Counter
from scapy.all import PcapReader, IP, IPv6, TCP, UDP

counts = Counter()
with PcapReader("your-own-lab.pcap") as capture:
    for packet in capture:
        if IP in packet:
            counts["ipv4"] += 1
        elif IPv6 in packet:
            counts["ipv6"] += 1
        if TCP in packet:
            counts["tcp"] += 1
        elif UDP in packet:
            counts["udp"] += 1
print(counts)
```

**Why streaming matters:** `rdpcap` may load all frames into memory; `PcapReader` reads incrementally. Set an upper frame count and time budget. Treat untrusted captures as potentially malicious input to parsing libraries; use isolation and updates.

### Important nuance
Counting "protocol appearances" is not the same as counting flows, hosts or bytes. One TCP connection can contain hundreds of frames, and one packet may contain multiple encapsulated protocol layers.

## 4. Five-tuple flows

A common approximation for an IP transport flow is:
`(src_ip, dst_ip, src_port, dst_port, transport_protocol)`.

Direction matters; a bidirectional conversation involves forward and reverse tuples. Normalization can map both directions into a canonical conversation key, but this may lose important directionality. NAT can obscure original endpoints; reused ports and long time ranges can merge distinct sessions.

```python
from collections import Counter

def canonical_pair(ip_a: str, ip_b: str) -> tuple[str, str]:
    # Purely lexical order is illustrative, not a semantic IP ordering.
    return tuple(sorted((ip_a, ip_b)))

peers = Counter()
for a, b in [("192.0.2.1", "192.0.2.2"), ("192.0.2.2", "192.0.2.1")]:
    peers[canonical_pair(a, b)] += 1
assert peers[("192.0.2.1", "192.0.2.2")] == 2
```

For robust IP normalization, use `ipaddress` and separate address family from lexical representation; never infer user identity solely from a source IP.

## 5. TCP stream reconstruction caveats

A parser that concatenates TCP payload bytes in capture order may be wrong because of retransmissions, out-of-order delivery, missing segments and sequence number wraparound. Reassembly requires TCP sequence-aware handling, stream boundaries, direction and overlaps. Prefer a mature protocol analysis engine for production analysis; Python is helpful for controlled metadata and enrichment.

## 6. TLS visibility and limitations

A modern TLS session uses certificate validation and authenticated encryption. Some handshake information can be seen in ordinary captures, but encrypted application data cannot be assumed to be readable. Avoid interpreting random-looking ciphertext as malicious. If decryption keys are available through an authorized test environment, preserve their confidentiality and use approved tools.

## 7. Example hypothesis: unusual DNS activity

Observation: a synthetic lab capture contains 200 DNS requests from one machine in 60 seconds. Possible explanations:
- Broken application retry loop.
- Browser prefetch/caching behavior.
- Software update or telemetry service.
- Data movement hypothesis requiring more evidence.

The count itself is a **signal**, not a verdict. Investigate time distribution, query labels, response codes, source process (if endpoint data exists) and comparison with normal baseline.

## 8. False positive/false negative analysis

**FP example:** monitoring agent periodically calls DNS. Rule flags it as beaconing. **FN example:** network capture misses packets because interface is wrong or TLS hides payload. Both must be documented when reporting detection performance.

For volume, report frames captured, parse failures, truncated count, unrecognized link types, number of flows, time range and gaps. A confident negative statement "no suspicious traffic" is rarely justified from a partial capture alone.

## 9. Lab: local HTTP capture
1. Bind a Python HTTP server to 127.0.0.1 port 8765.
2. Use your browser or local HTTP client to request one file.
3. Capture traffic on the **loopback interface only**, with permission.
4. Save as `lab.pcap`; inspect in Wireshark.
5. Run `python -m examples.offline_pcap lab.pcap` (with Scapy installed).
6. Compare frame/protocol counts, explain link type and capture loss.
7. Confirm HTTP response status, not security state.
8. Delete captures if unnecessary under your lab retention policy.

If your capture tool cannot record loopback traffic on a platform, use an isolated VM network and **only** VMs you own.

## 10. Exercises and checks

**A:** Why does a TCP retransmission cause naive packet-byte counters to overestimate application bytes? *It repeats the same logical data.*

**B:** Why isn't a source IP the same as an authenticated user? *NAT, proxies, VPNs, shared devices and spoofing considerations.*

**C:** Explain three reasons packet counts from Scapy and Wireshark may differ: filtering, dissection differences, capture truncation, link type or handling.

**D:** Design a bounded output schema for flow summaries with source, destination, ports, protocol, first/last seen and count. State privacy risks.

**E:** Describe which TLS details can normally be inferred without decryption and which cannot. A good answer distinguishes metadata from plaintext.

**References:** [Wireshark user's guide](https://www.wireshark.org/docs/), [Scapy](https://scapy.readthedocs.io/), [Python ipaddress](https://docs.python.org/3/library/ipaddress.html).
