#!/usr/bin/env python3
"""
ZW Calculator Demo — schema-agnostic, noise-tolerant parsing to prove ZW philosophy.

Usage:
  python tools/zw_calc_demo.py --demo
  python tools/zw_calc_demo.py -f path/to/input.zw.txt
  echo "ZiegelWagga: plus\nalpha:2\nbeta:3" | python tools/zw_calc_demo.py
"""
import sys, re, ast, math, json, argparse
from typing import Any, Dict, List, Tuple

ALLOWED_FUNCS = {k: getattr(math, k) for k in dir(math) if not k.startswith('_')}
ALLOWED_NAMES = {**ALLOWED_FUNCS}

def safe_eval_expr(expr: str) -> float:
    node = ast.parse(expr, mode='eval')
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Load, ast.Add, ast.Sub,
        ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.Mod, ast.FloorDiv,
        ast.Call, ast.Name, ast.Attribute, ast.Tuple, ast.List, ast.Constant, ast.Expr
    )
    for n in ast.walk(node):
        if not isinstance(n, allowed_nodes):
            raise ValueError(f"Disallowed element: {type(n).__name__}")
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Attribute):
                if not (isinstance(n.func.value, ast.Name) and n.func.value.id == 'math'):
                    raise ValueError("Only math.<fn>() allowed")
            elif isinstance(n.func, ast.Name):
                if n.func.id not in ALLOWED_FUNCS:
                    raise ValueError(f"Function {n.func.id} not allowed")
            else:
                raise ValueError("Invalid function call")
        if isinstance(n, ast.Name):
            if n.id not in ALLOWED_NAMES and n.id not in ('math',):
                raise ValueError(f"Name {n.id} not allowed")
    return eval(compile(node, '<expr>', 'eval'), {'__builtins__': {}}, {'math': math, **ALLOWED_FUNCS})

KEY_ALIASES = {
    'op': {'op', 'operation', 'do', 'verb', 'calc', 'function', 'ziegelwagga', 'zw', 'intent', 'combine'},
    'a': {'a', 'x', 'left', 'lhs', 'input1', 'arg1', 'first', 'alpha'},
    'b': {'b', 'y', 'right', 'rhs', 'input2', 'arg2', 'second', 'beta'},
    'list': {'list', 'values', 'items', 'nums', 'numbers', 'set', 'array', 'vector', 'bag'},
    'expr': {'expr', 'expression', 'formula', 'compute', 'math', 'equation', 'line'},
    'redefine': {'define', 'map', 'alias', 'vocab', 'meaning', 'bind', 'schema'},
}

OP_ALIASES = {
    'add': {'add', 'plus', 'sum', 'aggregate'},
    'sub': {'sub', 'minus', 'diff', 'difference', 'subtract'},
    'mul': {'mul', 'times', 'product', 'multiply'},
    'div': {'div', 'divide', 'quotient'},
    'pow': {'pow', 'power', 'exp', 'exponent'},
    'sqrt': {'sqrt', 'root'},
    'mean': {'mean', 'avg', 'average'},
    'min': {'min', 'minimum', 'lowest'},
    'max': {'max', 'maximum', 'highest'},
    'sum': {'sum', 'summation', 'sigma'},
}

def normalize_key(k: str, custom_vocab: Dict[str, str]) -> str:
    lk = k.strip().lower()
    if lk in custom_vocab:
        return custom_vocab[lk]
    for canon, aliases in KEY_ALIASES.items():
        if lk in aliases:
            return canon
    return lk

def detect_op(val: str) -> str:
    lv = val.strip().lower()
    for canon, aliases in OP_ALIASES.items():
        for a in aliases:
            if a in lv:
                return canon
    if lv in OP_ALIASES:
        return lv
    return ''

def parse_numbers_blob(s: str) -> list:
    nums = re.findall(r'-?\d+(?:\.\d+)?', s)
    return [float(n) for n in nums]

def parse_zw_block(block: str) -> Dict[str, Any]:
    custom_vocab: Dict[str, str] = {}
    data: Dict[str, Any] = {}
    lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip() and not ln.strip().startswith('#')]
    for ln in lines:
        if ':' in ln:
            k, v = ln.split(':', 1)
            k_norm = normalize_key(k, custom_vocab)
            v = v.strip()
            if k_norm in ('redefine', 'alias', 'meaning', 'vocab', 'schema'):
                pairs = re.findall(r'([\w\-]+)\s*->\s*([\w\-]+)', v.lower())
                for src, dst in pairs:
                    custom_vocab[src.strip()] = dst.strip()
                continue
            if k_norm == 'expr':
                data['expr'] = v.replace('^', '**')
                continue
            if k_norm == 'list':
                data['list'] = parse_numbers_blob(v)
                continue
            if k_norm == 'op':
                data['op'] = detect_op(v) or v.lower()
                continue
            if k_norm in ('a','b'):
                try:
                    data[k_norm] = float(v)
                except ValueError:
                    nums = parse_numbers_blob(v)
                    data[k_norm] = nums[0] if nums else v
                continue
            nums = parse_numbers_blob(v)
            if nums:
                data.setdefault('extras', {})[k_norm] = nums if len(nums)>1 else nums[0]
            else:
                data.setdefault('extras', {})[k_norm] = v
        else:
            if any(ch in ln for ch in '+-*/()^'):
                data['expr'] = ln.replace('^', '**')
            else:
                nums = parse_numbers_blob(ln)
                if nums:
                    data.setdefault('list', []).extend(nums)
                else:
                    data.setdefault('notes', []).append(ln)
    return data

def compute_from_data(data: Dict[str, Any]):
    if 'expr' in data:
        result = safe_eval_expr(data['expr'])
        return ('expr', result)
    op = data.get('op','')
    a = data.get('a', None)
    b = data.get('b', None)
    lst = data.get('list', None)
    if op in ('add','sub','mul','div','pow') and a is not None and b is not None:
        if op == 'add': return ('add', float(a)+float(b))
        if op == 'sub': return ('sub', float(a)-float(b))
        if op == 'mul': return ('mul', float(a)*float(b))
        if op == 'div': return ('div', float(a)/float(b))
        if op == 'pow': return ('pow', float(a)**float(b))
    if op in ('sqrt',) and a is not None:
        return ('sqrt', math.sqrt(float(a)))
    if op in ('mean','min','max','sum') and lst:
        L = list(map(float, lst))
        if op == 'mean': return ('mean', sum(L)/len(L))
        if op == 'min': return ('min', min(L))
        if op == 'max': return ('max', max(L))
        if op == 'sum': return ('sum', sum(L))
    if lst:
        return ('sum*', sum(map(float, lst)))
    raise ValueError('Insufficient data to compute')

def run_demo():
    demo_blocks = [
        'ZiegelWagga: plus\nalpha: 2\nbeta: 3\n',
        'meaning: left->a, right->b, combine->op\nleft: 10\nright: 4\ncombine: minus\n',
        'compute: (3 + 5) * sqrt(16) - 7\n',
        'values: 1, 2, 3, 4, 5, 100\ndo: average\nextra: ZW ignores this line\n',
        '(12 + 8) / 5\n',
        'recipe: Chocolate Lava\nspice: cinnamon\nlhs: 6\nrhs: 7\noperation: times\n',
        'verb: power\nx: 2\ny: 8\n',
        'purple potato moonbeams\nbag: -1 2 -3 4 5.5\n',
    ]
    for i, block in enumerate(demo_blocks, 1):
        parsed = parse_zw_block(block)
        try:
            op_name, value = compute_from_data(parsed)
            print(f'Case {i}: {op_name} = {value}')
        except Exception as e:
            print(f'Case {i}: error -> {e}')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--demo', action='store_true', help='Run built-in demo cases')
    ap.add_argument('-f', '--file', help='Read ZW block from file')
    args = ap.parse_args()

    if args.demo:
        run_demo()
        return
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as fh:
            block = fh.read()
    else:
        block = sys.stdin.read()
    data = parse_zw_block(block)
    op_name, value = compute_from_data(data)
    print(json.dumps({'operation': op_name, 'result': value, 'parsed': data}, indent=2))

if __name__ == '__main__':
    main()