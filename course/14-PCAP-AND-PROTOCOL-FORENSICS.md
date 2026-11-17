# Deep Dive 14 — Offline packet captures and Python protocol forensics

> **Hands-on:** [Chapter 14 Guided Lab](../lab-manual/14-GUIDED-LAB.md) · [100 worked answers](../solutions/by-exercise/README.md). Run negative tests and document limitations.

**Level:** intermediate → advanced · **Estimated study:** 10–14 hours.

## Learning outcome
Inspect offline packet captures, extract bounded metadata, reconstruct basic flow statistics, understand why encrypted or lost data limits conclusions, and write a report that does not exaggerate what a capture proves.

## Masterclass — packets, TCP segments and application messages are different counting units

A PCAP can contain retransmitted TCP segments, missing frames, overlapping data and traffic captured only mid-connection. Counting the total payload length of every observed packet can therefore **overestimate application bytes**. Meanwhile, a capture with gaps may be unable to reconstruct a complete request.

To study the idea without external traffic or parser dependencies, use synthetic sequence-offset fragments. This toy logic handles only exact duplicates and simple gaps; **it is not** a real TCP reassembly engine.

| Offset | Payload | Interpretation |
|---|---|---|
| 0 | `ABC` | first three bytes |
| 0 | `ABC` | exact retransmission |
| 3 | `DEF` | next three bytes |
| 9 | `X` | gap at byte offsets 6–8 |

**Runnable offline stream sketch:**

```python
# MASTERCLASS_RUNNABLE
def summarize_fragments(parts: list[tuple[int, bytes]]):
    seen: dict[int, bytes] = {}
    duplicates = 0
    for offset, payload in parts:
        if type(offset) is not int or offset < 0:
            raise ValueError("invalid sequence offset")
        if type(payload) is not bytes or not payload or len(payload) > 1024:
            raise ValueError("invalid fragment")
        if offset in seen:
            if seen[offset] != payload:
                raise ValueError("conflicting fragment at same offset")
            duplicates += 1
        else:
            seen[offset] = payload
    gaps = []
    expected = 0
    for offset, payload in sorted(seen.items()):
        if offset > expected:
            gaps.append((expected, offset))
        elif offset < expected:
            raise ValueError("partial overlap needs full TCP reassembly")
        expected = offset + len(payload)
    return {"segments": len(seen), "retransmits": duplicates, "gaps": gaps}

parts = [(0, b"ABC"), (0, b"ABC"), (3, b"DEF"), (9, b"X")]
report = summarize_fragments(parts)
assert report == {"segments": 3, "retransmits": 1, "gaps": [(6, 9)]}
try:
    summarize_fragments([(0, b"ABC"), (0, b"XYZ")])
except ValueError:
    pass
else:
    raise AssertionError("conflicting content silently accepted")
```

**Read the output carefully:** the report says there are three distinct offset fragments, one exact duplicate and one missing byte interval. It does **not** say there was one HTTP request, a complete TCP connection or a malicious transfer. Real TCP sequence numbers can wrap, packets can arrive out of order, overlaps and fragmentation have complicated semantics, and capture loss may occur before the file is written.

**Operational bridge:** when analyzing an owned offline PCAP with Scapy or Wireshark, log the link-layer type, capture filters, timestamps, missing segments and what was actually observed. TLS usually encrypts application bodies; metadata may remain visible without allowing content interpretation.

**Challenge:** inject a fragment at offset 2 that overlaps existing bytes. Should the toy parser select first-seen or last-seen content? Neither is universally safe; this snippet intentionally **rejects** an ambiguous overlap. Explain why real forensic analysis needs a documented target-stack/reassembly policy and why different tools can disagree.


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


## 11. Deep case study: reconstructing useful metadata from an offline PCAP

Your approved capture includes HTTP traffic to a local lab service and some DNS queries. You want a compact report: frames analyzed, IPv4/IPv6 counts, TCP/UDP counts and the most frequent endpoint pairs. The purpose is *description*, not a declaration that an endpoint is malicious.

### Parsing strategy

Read one captured frame at a time. For each packet:
1. Check which IP layer is present.
2. Obtain source/destination IP without assuming IPv4.
3. Check transport layer (TCP or UDP).
4. Extract bounded metadata (ports, time, protocol).
5. Count only data you actually observed; handle missing layers and parse errors.
6. Stop at an explicit packet budget; report truncation.

### Example implementation (Scapy, offline only)

```python
# Optional: pip install scapy in your venv.
from collections import Counter
from scapy.all import PcapReader, IP, IPv6, TCP, UDP

def summarize_capture(path: str, limit: int = 100_000) -> dict:
    if type(limit) is not int or not 1 <= limit <= 1_000_000:
        raise ValueError("invalid packet limit")
    transport = Counter()
    peers = Counter()
    scanned = 0
    truncated = False
    with PcapReader(path) as capture:
        for packet in capture:
            if scanned >= limit:
                truncated = True
                break
            scanned += 1
            if IP in packet:
                src, dst = packet[IP].src, packet[IP].dst
                transport["IPv4"] += 1
            elif IPv6 in packet:
                src, dst = packet[IPv6].src, packet[IPv6].dst
                transport["IPv6"] += 1
            else:
                transport["non-IP"] += 1
                continue
            if TCP in packet:
                transport["TCP"] += 1
            elif UDP in packet:
                transport["UDP"] += 1
            else:
                transport["other transport"] += 1
            if len(peers) >= 10_000 and (src, dst) not in peers:
                raise ValueError("peer-pair cardinality cap")
            peers[(src, dst)] += 1
    return {
        "frames_analyzed": scanned,
        "stopped_at_limit": truncated,
        "protocols": dict(transport),
        "top_directional_pairs": peers.most_common(5),
    }
```

**What to check:** `PcapReader` avoids loading the entire file at once. `peers` remains bounded by a distinct-pair cap. Truncation status is **not** a statement about whether the underlying capture lost packets before recording. For operational PCAP parsers, validate file metadata/link types and execute against untrusted captures in an isolated environment.

## 12. How packet counts differ from flows and sessions

| Term | Meaning | Why it may be misleading |
|---|---|---|
| Captured frame | what capture tool recorded | dropped/filtered packets absent |
| IP packet | one network-layer datagram | fragmentation changes counts |
| TCP segment | byte stream transport unit | retransmission repeats data |
| 5-tuple flow | src/dst addresses, ports, protocol | NAT and reused ports |
| App transaction | HTTP request/response | may span many segments |
| TLS session | cryptographic connection state | app payload usually encrypted |

One HTTP response may appear as hundreds of TCP segments; counting packets does not give number of completed user requests. A naive reassembler must handle sequence numbers, retransmissions, gaps and overlaps, so use maintained tools for real stream reconstruction.

### Capture limitations table

| Observation | Can you infer? | Reason |
|---|---|---|
| One host sends 1000 DNS queries | yes, if captured and parsed | directly observed |
| Host is infected | no | benign software can do this |
| TLS data bytes sent | often yes | encrypted records have lengths |
| HTTPS message body content | generally no | encryption |
| No attacker traffic anywhere | no | coverage, encryption, timing gaps |
| TCP handshake completed | maybe | needs relevant SYN/SYN-ACK/ACK in capture |

## 13. Lab questions with answer keys

**A:** If the capture starts mid-flow, will a TCP session necessarily contain a SYN? No, the earlier handshake may have been missed.

**B:** A flow has 10 retransmitted segments. Does summing TCP payload bytes equal application bytes? No, repeated segments can inflate totals.

**C:** A source IP represents a user? No; NAT, proxy, VPN and shared networks break that assumption.

**D:** Two capture tools count different packet totals. List potential causes: filters, link-type interpretation, capture loss, truncated frames, parser choices, timing.

**E:** Compare an encrypted HTTPS exchange and plaintext HTTP in a loopback/VM lab. Document visible metadata without assuming the encryption is broken.

**F:** Produce one report from your own capture with top five directional peers and a clear "unobserved does not imply absent" limitation statement.
