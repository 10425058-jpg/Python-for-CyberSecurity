"""Project 4: offline evaluation of labeled toy detection outcomes.

Input JSONL exact schema: {"case_id":"...","actual":0|1,"predicted":0|1}.
All labels are synthetic. No production claims.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

MAX_LINE = 4096
MAX_RECORDS = 100_000


def evaluate_cases(cases: list[dict]) -> dict:
    counts={"tp":0,"fp":0,"fn":0,"tn":0}
    seen=set()
    if len(cases)>MAX_RECORDS:
        raise ValueError("too many cases")
    for i,row in enumerate(cases,1):
        if type(row) is not dict or set(row)!={"case_id","actual","predicted"}:
            raise ValueError(f"case {i}: exact schema required")
        case_id=row["case_id"]
        if type(case_id) is not str or not 1<=len(case_id)<=128 or case_id in seen:
            raise ValueError(f"case {i}: invalid or duplicate ID")
        seen.add(case_id)
        a,p=row["actual"],row["predicted"]
        if type(a) is not int or type(p) is not int or a not in (0,1) or p not in (0,1):
            raise ValueError(f"case {i}: labels must be integer 0 or 1")
        counts[("tp" if a==1 else "fp") if p==1 else ("fn" if a==1 else "tn")]+=1
    tp,fp,fn,tn=(counts[k] for k in ("tp","fp","fn","tn"))
    return {
        "complete":True, "cases":len(cases), "counts":counts,
        "precision":tp/(tp+fp) if tp+fp else None,
        "recall":tp/(tp+fn) if tp+fn else None,
        "false_positive_rate":fp/(fp+tn) if fp+tn else None,
        "f1":2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
        "limitations":"Metrics apply only to this labeled synthetic sample"
    }


def read_cases(path: Path) -> list[dict]:
    cases=[]
    with path.open("rb") as source:
        while True:
            raw=source.readline(MAX_LINE+1)
            if not raw:
                break
            if len(raw)>MAX_LINE:
                raise ValueError(f"line {len(cases)+1}: exceeds byte cap")
            if not raw.strip():
                continue
            if len(cases)>=MAX_RECORDS:
                raise ValueError("record cap exceeded")
            try:
                cases.append(json.loads(raw.decode("utf-8","strict")))
            except (UnicodeDecodeError,json.JSONDecodeError) as exc:
                raise ValueError(f"line {len(cases)+1}: invalid JSON") from exc
    return cases


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("path",type=Path)
    args=p.parse_args(argv)
    try:
        report=evaluate_cases(read_cases(args.path))
    except (OSError,ValueError) as exc:
        print(f"incomplete evaluation: {exc}",file=sys.stderr)
        return 2
    print(json.dumps(report,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
