# Deep Dive 22 — Regular expressions, untrusted log text and safe parsing strategies

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
