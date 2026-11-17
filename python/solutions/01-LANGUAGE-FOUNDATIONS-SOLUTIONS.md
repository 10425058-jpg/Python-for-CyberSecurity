# Chapter 01 — Worked Solutions to 25 Independent Exercises

**Read [the exercises](../exercises/01-LANGUAGE-FOUNDATIONS-EXERCISES.md) first.** These are reference approaches, not the only possible solutions. Run each fenced block separately from the repository root on Python 3.11+. All examples are local/synthetic. Explain each line before checking the answer.

## Solution 01.01 — Expression versus statement

**Expected:** total evaluates to integer 5.

```python
total = 2 + 3
assert total == 5 and type(total) is int
```

**Reasoning:** An expression is evaluated before its result is bound to a name.

**Cybersecurity/engineering connection:** A variable name and an object are not the same entity.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.02 — Rebinding and in-place mutation

**Expected:** First creates a new list; second mutates aliased list.

```python
a=[1,2]
b=a
a=a+[3]
assert b==[1,2] and a is not b
a=b
a += [3]
assert a is b and b==[1,2,3]
```

**Reasoning:** Assignment rebinds names; list augmented assignment extends an existing object.

**Cybersecurity/engineering connection:** Do not mutate shared event evidence accidentally.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.03 — Shallow versus deep copy

**Expected:** A shallow copy shares nested dict objects.

```python
items=[{'x':[1]}]
copy=items.copy()
copy[0]['x'].append(2)
assert items[0]['x']==[1,2]
```

**Reasoning:** The outer list is new; nested references still point to original objects.

**Cybersecurity/engineering connection:** A shallow redaction copy can alter source data.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.04 — Equality and identity

**Expected:** == true; is false for distinct objects.

```python
x=[1,2]
y=list(x)
assert x==y and x is not y
```

**Reasoning:** Identity checks whether the objects are the same, while equality uses values.

**Cybersecurity/engineering connection:** Use is None for the None sentinel, not generic value comparison.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.05 — The bool-int inheritance trap

**Expected:** Exact int type accepted only within 0..100.

```python
def count(v):
    if type(v) is not int or not 0 <= v <= 100:
        raise ValueError('count')
    return v
assert count(0)==0 and count(100)==100
for v in (True, False, 2.0, '2', -1, 101):
    try: count(v)
    except ValueError: pass
    else: raise AssertionError(v)
```

**Reasoning:** bool subclasses int; isinstance alone would accept booleans.

**Cybersecurity/engineering connection:** Trust-boundary validators must reflect domain types.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.06 — Floating-point and Decimal

**Expected:** Float comparison false; Decimal string computation exact.

```python
from decimal import Decimal
assert (0.1+0.2)==0.3 is False
assert Decimal('0.1')+Decimal('0.2')==Decimal('0.3')
```

**Reasoning:** Binary floating point usually approximates tenths; string Decimal preserves exact intended digits.

**Cybersecurity/engineering connection:** Use decimal or integer fixed-point for exact accounting contracts.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.07 — Negative floor division

**Expected:** Quotient -4; remainder +1.

```python
q,r=divmod(-7,2)
assert (q,r)==(-4,1)
assert -7==q*2+r
```

**Reasoning:** Floor division rounds down toward negative infinity.

**Cybersecurity/engineering connection:** Packet offsets should use documented unsigned integer arithmetic.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.08 — Presence is not truthiness

**Expected:** {'limit':0} is valid; {} is missing.

```python
def get_limit(p):
    if 'limit' not in p: raise ValueError('missing')
    v=p['limit']
    if type(v) is not int or not 0<=v<=10: raise ValueError('invalid')
    return v
assert get_limit({'limit':0})==0
try: get_limit({})
except ValueError: pass
else: raise AssertionError
```

**Reasoning:** A falsy value may be present and valid.

**Cybersecurity/engineering connection:** Using p.get('limit') or 5 silently changes security policy.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.09 — Short-circuit operators

**Expected:** 9, 5, False; division never runs.

```python
assert (0 or 9)==9
assert ('x' and 5)==5
assert (False and (1/0)) is False
```

**Reasoning:** and/or are short-circuit expressions that return operands.

**Cybersecurity/engineering connection:** Parenthesize access-control conditions and validate inputs.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.10 — Chained comparisons

**Expected:** It evaluates x once in the chain.

```python
def between(v):
    if type(v) is not int: raise ValueError('int')
    return 1 < v < 5
assert between(3)
assert not between(1) and not between(5)
```

**Reasoning:** Python comparison chains evaluate intermediate operands once.

**Cybersecurity/engineering connection:** Don't rely only on a numeric range: guard the input type.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.11 — Unicode code points versus bytes

**Expected:** 1 vs 2 code points; 2 vs 3 bytes.

```python
a='é'
b='e\u0301'
assert len(a)==1 and len(b)==2
assert len(a.encode('utf-8'))==2 and len(b.encode('utf-8'))==3
```

**Reasoning:** Unicode code points and encoded bytes have distinct meanings.

**Cybersecurity/engineering connection:** Enforce protocol byte caps before decoding.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.12 — Unicode normalization

**Expected:** NFC makes the two example sequences equal.

```python
import unicodedata
assert unicodedata.normalize('NFC','é')==unicodedata.normalize('NFC','e\u0301')
```

**Reasoning:** Canonical normalization can align different code-point sequences.

**Cybersecurity/engineering connection:** Identity normalization must follow authoritative provider semantics.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.13 — Strict UTF-8 decoding

**Expected:** UnicodeDecodeError raised.

```python
try:
    b'\xff'.decode('utf-8','strict')
except UnicodeDecodeError:
    pass
else:
    raise AssertionError
```

**Reasoning:** Strict mode preserves visibility of invalid source bytes.

**Cybersecurity/engineering connection:** Replacing or ignoring undecodable evidence can hide data integrity problems.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.14 — Slicing and reverse traversal

**Expected:** [1,3] and [4,3,2,1,0].

```python
numbers=[0,1,2,3,4]
assert numbers[1:4:2]==[1,3]
assert numbers[::-1]==[4,3,2,1,0]
```

**Reasoning:** Slice stop is excluded and step changes traversal.

**Cybersecurity/engineering connection:** A slice of a nested list is only shallow.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.15 — Comprehension versus generator

**Expected:** List built immediately; generator yields values as consumed.

```python
values=[1,2,3]
output=[x*x for x in values]
lazy=(x*x for x in values)
assert output==[1,4,9]
assert next(lazy)==1
assert list(lazy)==[4,9]
```

**Reasoning:** A list stores results; a generator produces items when iterated.

**Cybersecurity/engineering connection:** Streaming input alone does not bound memory of accumulated outputs.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.16 — Starred unpacking

**Expected:** Middle is a new list; fewer than two items raises ValueError.

```python
head,*middle,tail=[1,2,3,4]
assert (head,middle,tail)==(1,[2,3],4)
try:
    head,*middle,tail=[1]
except ValueError: pass
else: raise AssertionError
```

**Reasoning:** Unpacking assigns separate names and enforces shape.

**Cybersecurity/engineering connection:** Validate shape before interpreting heterogeneous event fields.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.17 — Enumerate and strict zip

**Expected:** Mismatched lengths raise ValueError.

```python
pairs=list(zip(['a','b'],['1','2'],strict=True))
assert list(enumerate(pairs,1))[1]==(2,('b','2'))
try: list(zip(['a','b'],['1'],strict=True))
except ValueError: pass
else: raise AssertionError
```

**Reasoning:** Ordinary zip silently truncates to the shortest iterable.

**Cybersecurity/engineering connection:** A misaligned source column is an incomplete data condition.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.18 — Loop else

**Expected:** No-match branch only after normal loop completion.

```python
def find(rows,key):
    for i,value in enumerate(rows):
        if value==key: return i
    else: return None
assert find(['a','b'],'b')==1
assert find(['a','b'],'z') is None
```

**Reasoning:** Loop else means no break prevented normal exhaustion.

**Cybersecurity/engineering connection:** Do not confuse a complete no-match with an interrupted scan.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.19 — Structural pattern matching

**Expected:** Mapping pattern can match a dictionary with extra fields.

```python
def parse(row):
    match row:
        case {'action':'fail','actor':str(actor)} if actor:
            return actor
        case _: raise ValueError('shape')
assert parse({'action':'fail','actor':'alex'})=='alex'
assert parse({'action':'fail','actor':'alex','extra':1})=='alex'
```

**Reasoning:** Mapping patterns match required keys but may allow extras.

**Cybersecurity/engineering connection:** Use exact key-set validation when the protocol requires a strict schema.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.20 — Mutable default arguments

**Expected:** Two independent calls return separate lists.

```python
def add(x,items=None):
    if items is None: items=[]
    items.append(x)
    return items
assert add('a')==['a']
assert add('b')==['b']
```

**Reasoning:** Defaults are evaluated when the function definition executes.

**Cybersecurity/engineering connection:** Cross-request shared state may leak data.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.21 — Late-bound closures

**Expected:** Bind i=i at function definition.

```python
callbacks=[lambda i=i:i for i in range(3)]
assert [f() for f in callbacks]==[0,1,2]
```

**Reasoning:** The loop otherwise shares one enclosing binding.

**Cybersecurity/engineering connection:** Capture validated values explicitly when building deferred alert tasks.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.22 — LEGB and nonlocal

**Expected:** Consecutive calls return 1 then 2.

```python
def make_counter():
    count=0
    def inc():
        nonlocal count
        count+=1
        return count
    return inc
c=make_counter()
assert c()==1 and c()==2
```

**Reasoning:** nonlocal rebinds an enclosing function variable.

**Cybersecurity/engineering connection:** Hidden mutable state needs documented ownership and test resets.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.23 — Formatting and output context

**Expected:** alice: 003 and &lt;...&gt; for HTML text.

```python
from html import escape
assert f"{'alice'}: {3:03d}"=='alice: 003'
assert escape('<b>hi</b>')=='&lt;b&gt;hi&lt;/b&gt;'
```

**Reasoning:** Formatting creates text, while escaping responds to a particular output context.

**Cybersecurity/engineering connection:** HTML escaping does not prevent SQL injection.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.24 — Schema-driven defensive parsing

**Expected:** Bad actor, unknown action, and extra field rejected.

```python
def parse(row):
    if type(row) is not dict or set(row)!={'actor','action'}: raise ValueError('schema')
    if type(row['actor']) is not str or not row['actor']: raise ValueError('actor')
    if row['action'] not in ('fail','success'): raise ValueError('action')
    return row
assert parse({'actor':'alex','action':'fail'})['actor']=='alex'
for bad in ({'actor':None,'action':'fail'},{'actor':'a','action':'bad'},{'actor':'a','action':'fail','x':1}):
    try: parse(bad)
    except ValueError: pass
    else: raise AssertionError
```

**Reasoning:** A narrow schema validator is the boundary between raw and interpreted data.

**Cybersecurity/engineering connection:** Parsing valid JSON still does not authenticate the sender.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Solution 01.25 — Project readiness: complete log reporting

**Expected:** 8 unique events and 7 failures for alex; malformed file fails.

```python
from pathlib import Path
from projects.foundations.auth_summary import summarize
report=summarize(Path('fixtures/foundations-auth.jsonl'))
assert report['complete'] and report['input_unique_events']==8
assert report['failures_by_actor']=={'alex':7}
try: summarize(Path('fixtures/foundations-invalid-third.jsonl'))
except ValueError: pass
else: raise AssertionError
```

**Reasoning:** Completeness must be established before publishing findings.

**Cybersecurity/engineering connection:** This is a reference check, not permission to deploy on external identity providers.

**Extension:** Change a valid boundary into an invalid input; assert the precise failure or changed behavior and explain why it is correct.

## Reproduce the whole learning progression

Run `python -m unittest tests.test_foundations_deep_examples tests.test_foundations_projects -v` from the repository root. Add independent tests before consulting the [reference local project](../../projects/foundations/auth_summary.py). Keep original source data distinct from normalized output.
