# Deep Dive 22 — Regular expressions, untrusted log text and safe parsing strategies

> **Hands-on:** [Chapter 22 Guided Lab](../lab-manual/22-GUIDED-LAB.md) · [100 worked answers](../solutions/by-exercise/README.md). Test realistic error conditions before proceeding.

**Level:** beginner → intermediate · **Estimated study:** 7–10 hours.

## Goal
Use Python's regular expressions to extract structured fields from *bounded* text, understand greedy versus lazy matches, identify when regex is the wrong parser, and avoid expensive patterns on adversarial input.

## 1. Raw strings and regex syntax

Python's `re` module defines a regular-expression language:
- `.` matches most characters (not newline by default).
- `^`/`$` anchor beginning/end under the relevant flags; `re.fullmatch` is often clearer for complete validation.
- `\d` digits, `\w` word characters, `\s` whitespace (Unicode-aware unless configured).
- `+` one or more; `*` zero or more; `?` optional or non-greedy modifier in quantifier context.
- `{m,n}` repetition bounds.
- `(...)` capture group; `(?:...)` noncapturing group.
- `(?P<name>...)` named capture.
- `[...]` character class, `|` alternation.

Use raw string literals like `r"\d+"` so Python does not treat backslashes as string escapes. Remember Unicode versus ASCII digit definitions.

## 2. Validation is not extraction

`re.search` finds a substring anywhere; `re.fullmatch` requires the complete input to match. For validation, a substring match can be dangerously permissive.

```python
import re
PORT_TEXT = re.compile(r"[0-9]{1,5}")

def validate_port_text(raw: str) -> int:
    if not isinstance(raw, str) or PORT_TEXT.fullmatch(raw) is None:
        raise ValueError("port must be 1-5 ASCII digits")
    number = int(raw)
    if not 1 <= number <= 65535:
        raise ValueError("port outside range")
    return number

assert validate_port_text("443") == 443
for bad in ("443junk", "65536", "-1", ""):
    try:
        validate_port_text(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid port accepted")
```

**Why ASCII [0-9]?** `\d` can match digits from scripts beyond ASCII. If a protocol specifically requires ASCII numerals, define it explicitly rather than assuming `\d` has that meaning.

## 3. Greedy and non-greedy matches

`.*` is greedy and may consume too far. `.*?` is lazy, but neither is guaranteed to be a correct parser for nested or quoted formats.

```python
import re
line = "user=[alice] action=[login_failure]"
matches = re.findall(r"\[([^\]]+)\]", line)
assert matches == ["alice", "login_failure"]
```

Here the character class says "read until ]", which is more constrained than `.*`. It still fails for escaped closing brackets or newlines unless a precise input grammar is defined.

## 4. Catastrophic backtracking (ReDoS)

Certain ambiguous patterns (especially nested repetitions) may try enormous numbers of alternatives for carefully chosen long strings. Input from logs, query parameters or user-provided patterns may create CPU exhaustion. Mitigations:
- Prefer fixed, unambiguous grammars.
- Put **byte-size bounds before decoding and regex matching**.
- Avoid nested ambiguous quantifiers.
- Consider specialized parsers or bounded-time engines for complex untrusted patterns.
- Measure worst-case inputs locally; set per-request time/CPU limits at the application boundary.
- Do not expose arbitrary regex compilation/execution to anonymous users without resource controls.

A "reasonable" average input is not enough for safety when an adversary chooses the worst case.

## 5. Parsing real log formats

Not every log format should be parsed with regex. For JSONL, use `json.loads` with validation and size limits; for CSV, use `csv`; for syslog, use well-tested parsers aware of spec variants; for free-form text, targeted regex may be pragmatic but preserve original messages and count parse failures.

### Toy text log parsing
```python
import re
LOG = re.compile(
    r"time=(?P<time>[0-9TZ:+-]+) "
    r"user=(?P<user>[A-Za-z0-9_.-]{1,64}) "
    r"action=(?P<action>login_success|login_failure)"
)

def parse_toy_log(line: str) -> dict[str, str]:
    if not isinstance(line, str) or len(line) > 1024:
        raise ValueError("line too long or wrong type")
    match = LOG.fullmatch(line.strip())
    if match is None:
        raise ValueError("unsupported toy log format")
    return match.groupdict()

assert parse_toy_log(
    "time=2026-01-01T10:00:00Z user=alice action=login_failure"
)["user"] == "alice"
```

The time pattern is deliberately lexical, *not* a full timestamp validator. After extracting it, parse with `datetime.fromisoformat` and require a timezone.

## 6. Security-relevant pitfalls
- `re.search` when full validation was intended.
- Unbounded `.*` over huge untrusted lines.
- Assuming `\w` only matches ASCII.
- Using string regexes to validate IP addresses instead of `ipaddress`.
- Assuming regex prevents SQL or shell injection (use parameterization, safe APIs).
- Discarding unparseable logs as though they never existed.
- Parsing nested JSON/XML/HTML with a brittle regex.
- Allowing user-defined complex patterns on production data without budgets.

## 7. Exercises and answer checks
1. Write an ASCII-only username grammar allowing letters, digits, underscores and hyphens, 1–32 chars. Test accented characters, whitespace and length limits.
2. Compare `search` and `fullmatch` on `"PORT=443junk"`. Expected: a substring can match even though the whole input is invalid.
3. Extract two bracketed values using `\[[^\]]+\]`; explain how escaped brackets break it.
4. Parse a 5,000-line synthetic file with a strict per-line cap and report errors by line number.
5. Explain three mitigations for ReDoS without relying on a magic regex flag.
6. Explain why a regex accepting a domain name doesn't prove it is an approved network destination.

**References:** [re](https://docs.python.org/3/library/re.html), [regex HOWTO](https://docs.python.org/3/howto/regex.html), [OWASP input validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html).


## 8. End-to-end untrusted log parsing example

**Scenario:** a toy log line is `time=2026-01-01T10:00:00Z user=alex action=login_failure`. You want to extract exactly three fields without accepting extra suffixes, ambiguous whitespace or arbitrarily large input.

### Define the grammar first

```text
line        := "time=" iso_lexeme " user=" username " action=" action
iso_lexeme  := 1..40 ASCII chars from [0-9T:+-.Z]
username    := 1..64 ASCII letters/digits/underscore/dash/dot
action      := "login_success" | "login_failure"
```

A **lexical** grammar only controls the shape. You still need a semantic timestamp parser and a timezone requirement.

### Complete parser with full-string validation

```python
import re
from datetime import datetime, timezone

PATTERN = re.compile(
    r"time=(?P<time>[0-9T:+.Z-]{1,40}) "
    r"user=(?P<user>[A-Za-z0-9_.-]{1,64}) "
    r"action=(?P<action>login_failure|login_success)"
)

def parse_lab_log(line: str) -> dict:
    if type(line) is not str or not 1 <= len(line) <= 160:
        raise ValueError("line type/length invalid")
    match = PATTERN.fullmatch(line)
    if match is None:
        raise ValueError("line does not match toy grammar")
    parts = match.groupdict()
    try:
        timestamp = datetime.fromisoformat(
            parts["time"].replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timezone offset required")
    return {
        "time_utc": timestamp.astimezone(timezone.utc).isoformat(),
        "user": parts["user"],
        "action": parts["action"],
    }

event = parse_lab_log(
    "time=2026-01-01T10:00:00Z user=alex action=login_failure"
)
assert event["user"] == "alex"
assert event["time_utc"] == "2026-01-01T10:00:00+00:00"
```

**Walkthrough:**
1. Cap the whole input string length *before* matching.
2. Use an ASCII grammar rather than unqualified `\w` or `\d` when protocol semantics require ASCII.
3. Use `fullmatch` to reject trailing or leading payloads.
4. Extract named groups rather than brittle numerical group indexes.
5. Parse timestamp semantics with `datetime` and require an offset.
6. Return structured normalized data, not raw text.

A log's original string should be kept separately in an evidence system. This example intentionally handles only one invented format; do not assume its grammar covers systemd journald or Windows Event Logs.

## 9. Demonstrate two security-relevant mistakes

### Mistake 1: searching instead of validating

```python
import re
assert re.search(r"[0-9]+", "port=443EVIL") is not None
assert re.fullmatch(r"[0-9]+", "port=443EVIL") is None
```

A successful substring search does not mean the full input is valid. This can lead to authorization or parsing errors if the application silently ignores suffixes.

### Mistake 2: assuming regex prevents SQL injection

Even if a username matches a restricted grammar, SQL must use parameters. Validation and parameterization solve **different** problems. Regex is not a substitute for HTML output encoding, path safety, or per-object authorization either.

## 10. ReDoS and resource budgeting

Regex denial of service arises when a pattern explores exponentially many paths for adversarial text, particularly with ambiguous nested quantifiers. Avoid using dangerous expressions on long untrusted inputs. Before matching:
- Cap byte size, not only Python characters.
- Prefer anchored/simple bounded patterns.
- Avoid backtracking-heavy nested repetition.
- Use specialized format parsers for JSON/CSV/HTML/XML.
- Consider execution time/CPU caps for user-configurable patterns.
- Don't accept arbitrary user-supplied regex on privileged production telemetry without review.

A length cap helps, but on its own does not guarantee predictable runtime for every pathological pattern. The regex engine and pattern structure both matter.

## 11. Tests and answer keys

```python
bad_lines = [
    " time=2026-01-01T10:00:00Z user=alex action=login_failure",
    "time=2026-01-01T10:00:00 user=alex action=login_failure",
    "time=2026-01-01T10:00:00Z user=alex action=login_failure extra",
    "time=2026-01-01T10:00:00Z user= action=login_failure",
    "time=2026-01-01T10:00:00Z user=alex action=unknown",
]
for line in bad_lines:
    try:
        parse_lab_log(line)
    except ValueError:
        continue
    raise AssertionError("invalid line accepted")
```

**Exercise A:** Modify the grammar to allow a quoted user field with spaces. Explain why naive splitting at spaces fails and choose a proper escaping/quoting specification.

**Exercise B:** Accept IPv4 and IPv6 source addresses. Use regex only for lexical extraction and `ipaddress.ip_address` for semantic validation.

**Exercise C:** Compare `re.match`, `re.search` and `re.fullmatch`. Which should a strict validator use? Usually `fullmatch` when the entire value must conform.

**Exercise D:** Construct a local-only performance test comparing a safe bounded regex with a poorly designed backtracking pattern under time limits. Do not deploy it to a real service.

**Exercise E:** Decide whether rejecting non-ASCII usernames is appropriate. Answer: depends on policy; many real identities are Unicode, so preserve intended semantics and define normalization rather than imposing ASCII arbitrarily.

**Exercise F:** Describe why a legitimate-looking log message might still be untrustworthy: attacker-generated inputs can be recorded by authentic logging infrastructure.

**References:** [Python regular expressions](https://docs.python.org/3/library/re.html), [OWASP Input Validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html).
