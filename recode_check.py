#!/usr/bin/env python3
"""
recode_check.py - Blind re-coding check (SKILL.md, step 2b).

Two subcommands:

  sample   Draw a random sample of items (default 10%, minimum 10) and write a BLANK coding sheet
           that contains only the id column and the columns listed in --keep (e.g. a link).
           The second coder fills this sheet using the written rubric only, never the first codes.
    python recode_check.py sample --items items.csv --config config.json --out recode_sheet.csv [--frac 0.10] [--min-n 10] [--keep link]

  agree    Compare the second coder's sheet with the first codes and report per-dimension agreement.
    python recode_check.py agree --items items.csv --config config.json --recode recode_sheet.csv --out agreement.csv [--threshold 0.6]

Metrics per dimension:
  - pct_agree        : share of items with identical codes
  - kappa            : Cohen's kappa (nominal) for categorical dimensions
  - kappa_w          : linearly weighted Cohen's kappa for ordinal dimensions (partial credit for near misses)
  - status           : PASS if (weighted) kappa >= threshold AND pct_agree >= pct_threshold; REVIEW otherwise.
Kappa is undefined (NaN) when both coders used a single identical value; status then falls back to pct_agree.
"""
import argparse, json, sys
import numpy as np, pandas as pd

def cohen_kappa(a, b, labels, weights=None):
    """Cohen's kappa from scratch (no sklearn dependency); weights=None (nominal) or 'linear' (ordinal)."""
    idx = {v: i for i, v in enumerate(labels)}; n = len(labels)
    M = np.zeros((n, n))
    for x, y in zip(a, b): M[idx[x], idx[y]] += 1
    M /= M.sum()
    E = np.outer(M.sum(1), M.sum(0))
    if weights == "linear":
        W = np.abs(np.subtract.outer(np.arange(n), np.arange(n))) / max(n - 1, 1)
    else:
        W = 1 - np.eye(n)
    den = (W * E).sum()
    return float("nan") if den == 0 else float(1 - (W * M).sum() / den)

def load_cfg(path):
    with open(path, encoding="utf-8") as f: cfg = json.load(f)
    cfg.setdefault("ordinal", {}); return cfg

def cmd_sample(a):
    cfg = load_cfg(a.config); df = pd.read_csv(a.items)
    n = max(a.min_n, int(np.ceil(a.frac * len(df)))); n = min(n, len(df))
    s = df.sample(n, random_state=a.seed)
    keep = [cfg["id_col"]] + [c for c in a.keep if c in df]
    sheet = s[keep].copy()
    for d in list(cfg["categorical"]) + list(cfg["ordinal"]): sheet[d] = ""
    sheet.to_csv(a.out, index=False)
    print(f"Wrote blank sheet with {n} of {len(df)} items to {a.out}. Give it to a second coder with the rubric only.")

def cmd_agree(a):
    cfg = load_cfg(a.config); idc = cfg["id_col"]
    first = pd.read_csv(a.items).set_index(idc); second = pd.read_csv(a.recode).set_index(idc)
    missing = set(second.index) - set(first.index)
    if missing: sys.exit(f"Items in recode sheet not found in items CSV: {missing}")
    first = first.loc[second.index]
    rows = []
    for d, spec in cfg["categorical"].items():
        x, y = first[d].astype(str), second[d].astype(str)
        labels = sorted(set(map(str, spec["values"])) | set(x) | set(y))
        rows.append({"dimension": d, "type": "categorical", "n": len(x), "pct_agree": round(float((x == y).mean()), 3),
                     "kappa": round(cohen_kappa(x, y, labels), 3)})
    for d, (lo, hi) in cfg["ordinal"].items():
        x, y = first[d].astype(int), second[d].astype(int)
        labels = list(range(int(lo), int(hi) + 1))
        rows.append({"dimension": d, "type": "ordinal", "n": len(x), "pct_agree": round(float((x == y).mean()), 3),
                     "kappa": round(cohen_kappa(x, y, labels, "linear"), 3)})
    r = pd.DataFrame(rows)
    ok_k = r.kappa.fillna(1.0) >= a.threshold
    r["status"] = np.where(ok_k & (r.pct_agree >= a.pct_threshold), "PASS", "REVIEW")
    diffs = []
    for i in second.index:
        for d in list(cfg["categorical"]) + list(cfg["ordinal"]):
            if str(first.at[i, d]) != str(second.at[i, d]): diffs.append({idc: i, "dimension": d, "first": first.at[i, d], "second": second.at[i, d]})
    r.to_csv(a.out, index=False)
    pd.DataFrame(diffs).to_csv(a.out.replace(".csv", "_disagreements.csv"), index=False)
    print(r.to_string(index=False))
    print(f"\nOverall: mean pct_agree {r.pct_agree.mean():.3f}, median kappa {r.kappa.median():.3f}; "
          f"{(r.status == 'REVIEW').sum()} dimension(s) to review (threshold kappa >= {a.threshold}, agree >= {a.pct_threshold}).")
    print(f"Disagreements listed in {a.out.replace('.csv', '_disagreements.csv')}")

def main():
    ap = argparse.ArgumentParser(description="Blind re-coding check: sample sheet + per-dimension agreement (Cohen's kappa).")
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("sample", help="draw a random sample and write a blank coding sheet")
    s.add_argument("--items", required=True); s.add_argument("--config", required=True); s.add_argument("--out", required=True)
    s.add_argument("--frac", type=float, default=0.10); s.add_argument("--min-n", type=int, default=10)
    s.add_argument("--seed", type=int, default=7); s.add_argument("--keep", nargs="*", default=[], help="extra columns to show the coder (e.g. link)")
    g = sp.add_parser("agree", help="compute per-dimension agreement between first codes and the blind recode")
    g.add_argument("--items", required=True); g.add_argument("--config", required=True); g.add_argument("--recode", required=True)
    g.add_argument("--out", required=True); g.add_argument("--threshold", type=float, default=0.60, help="minimum (weighted) kappa")
    g.add_argument("--pct-threshold", type=float, default=0.80, help="minimum raw agreement")
    a = ap.parse_args()
    cmd_sample(a) if a.cmd == "sample" else cmd_agree(a)

if __name__ == "__main__": main()
