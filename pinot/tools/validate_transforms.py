#!/usr/bin/env python3
import argparse, json, os, re
from datetime import datetime

# Minimal evaluator for a subset of Pinot transform functions used here.
# Supports: jsonPathString($,'path'), jsonPathInt($,'path'), coalesce(a,b,...), fromDateTime(expr, pattern)

FUNC_RE = re.compile(r"^(?P<name>[a-zA-Z0-9_]+)\((?P<args>.*)\)$")

def parse_args():
    ap = argparse.ArgumentParser(description="Validate Pinot transformConfigs against a sample JSON event")
    ap.add_argument('--table', required=True, help='Path to table config JSON')
    ap.add_argument('--sample', required=True, help='Path to sample event JSON')
    return ap.parse_args()

def split_top_level_args(s: str):
    args=[]; depth=0; cur=''
    i=0
    while i < len(s):
        ch = s[i]
        if ch == '(':
            depth += 1
            cur += ch
        elif ch == ')':
            depth -= 1
            cur += ch
        elif ch == ',' and depth == 0:
            args.append(cur.strip())
            cur=''
        else:
            cur += ch
        i += 1
    if cur.strip():
        args.append(cur.strip())
    return args

def strip_quotes(s: str):
    s = s.strip()
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        return s[1:-1]
    return s

def eval_expr(expr: str, payload: dict):
    expr = expr.strip()
    m = FUNC_RE.match(expr)
    if not m:
        # literal string/number
        if expr.startswith("'") or expr.startswith('"'):
            return strip_quotes(expr)
        try:
            return int(expr)
        except Exception:
            return expr
    name = m.group('name')
    args = split_top_level_args(m.group('args'))
    
    if name == 'jsonPathString' or name == 'jsonPathInt':
        # Expect jsonPathString($, 'a.b.c')
        if len(args) != 2:
            return None
        # first arg is '$' ignored
        path = strip_quotes(args[1])
        return json_path_lookup(payload, path)
    if name == 'coalesce':
        for a in args:
            v = eval_expr(a, payload)
            if v not in (None, '', []):
                return v
        return None
    if name == 'fromDateTime':
        # fromDateTime(expr, 'pattern') -> epoch ms
        if len(args) < 1:
            return None
        v = eval_expr(args[0], payload)
        if not isinstance(v, str):
            return None
        iso = v
        # Normalize 'Z' to +00:00 for fromisoformat
        if iso.endswith('Z'):
            iso = iso[:-1] + '+00:00'
        try:
            dt = datetime.fromisoformat(iso)
            return int(dt.timestamp() * 1000)
        except Exception:
            return None
    # Fallback: unknown
    return None

def json_path_lookup(obj, path: str):
    # Supports simple paths like $.a.b.c and keys with dashes/underscores
    if not path.startswith('$.'):
        return None
    parts = path[2:].split('.')
    cur = obj
    for p in parts:
        # strip quotes in bracket notation if present (not fully implemented)
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur

def main():
    args = parse_args()
    with open(args.table, 'r') as f:
        table = json.load(f)
    with open(args.sample, 'r') as f:
        sample = json.load(f)
    tcfgs = (((table.get('ingestionConfig') or {}).get('transformConfigs')) or [])
    if not tcfgs:
        print('No transformConfigs found.')
        return
    print(f"Validating transforms for table: {table.get('tableName')}")
    ok = True
    for t in tcfgs:
        col = t.get('columnName')
        expr = t.get('transformFunction')
        val = eval_expr(expr, sample)
        print(f"- {col} <= {expr}\n  -> {val}")
        if val is None:
            ok = False
    if not ok:
        print('\nOne or more transforms returned None. Please adjust paths or sample payload.')
    else:
        print('\nAll transforms produced values (or empty strings).')

if __name__ == '__main__':
    main()

