# Runnable examples (local-first)

All examples use synthetic/local data. Most require only the Python standard library. `offline_pcap.py` optionally needs Scapy and works on **offline** user-supplied PCAP files. A reachable TCP port does not imply a vulnerability; entropy does not imply malware; log alerts require human review.

## Expanded-chapter runnable examples

- [Chapter case studies](chapter_cases.py): strict byte-bound JSON policy validator, toy log regex/time normalization, tenant-specific authorization, confusion-matrix metrics and atomic SQLite batch semantics.
- [Offline regression tests](../tests/test_chapter_cases.py) cover field types, duplicate keys, invalid timestamps, cross-tenant denial, zero denominators, duplicate event IDs and transaction rollback.

## Deep-dive, end-to-end examples

- [Strict toy binary frame parser](strict_frame.py): validates magic/version/type/length, strict UTF-8 JSON, duplicate keys, malformed input and payload caps. Guided [Workshop 01](../workshops/01-BINARY-FRAMING.md).
- [Advanced offline mini SOC pipeline](mini_soc_pipeline.py): bounded JSONL, UTC normalization, source-qualified dedup, event-time threshold logic and atomic report writes. Guided [Workshop 02](../workshops/02-MINI-SOC-DETECTION.md).
- [Unit tests for both](../tests/test_deep_examples.py) cover bad inputs, window reset and output atomicity.

## Commands
```bash
python -m examples.strict_frame
python -m examples.chapter_cases
python -m examples.mini_soc_pipeline --input fixtures/synthetic-auth.jsonl --output findings.jsonl
python -m examples.file_manifest fixtures
python -m examples.log_detector fixtures/synthetic-auth.jsonl --threshold 3
python -m examples.local_port_check 80 443 8080
python -m examples.binary_triage fixtures/synthetic-auth.jsonl
python -m examples.indicator_normalizer fixtures/synthetic-indicators.jsonl
python -m examples.sqlite_safety_demo
python -m examples.archive_inspector some-owned-test.zip
python -m unittest discover -s tests -v
```

## Engineering lessons
- Make operations read-only by default.
- Check file/record size, type and valid values before processing.
- Clearly distinguish observations from proof of a security incident.
- Do not scan external systems or upload real evidence.
- Avoid treating these teaching examples as hardened forensic tools or production detectors.
- Keep input fixtures synthetic and documented.
