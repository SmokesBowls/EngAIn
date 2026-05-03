"""
lisp_parser_mr.py — Minimal S-Expression Parser

Replaces fragile regex-based structural extraction for GIMP preset files 
(.gtp, .gdyn) with a robust recursive descent parser focusing on nesting.
"""

def parse_sexpr(text: str) -> list:
    """
    Parses a Lisp-like string into nested Python lists.
    - (a b) -> ['a', 'b']
    - Unquoted tokens become strings.
    - Quoted strings are stripped of quotes.
    Ignores comments starting with #
    """
    # First, strip out comments
    lines = []
    for line in text.splitlines():
        if '#' in line:
            line = line.split('#', 1)[0]
        lines.append(line)
    clean_text = " ".join(lines)

    stack = [[]]
    i = 0
    n = len(clean_text)
    
    while i < n:
        c = clean_text[i]
        
        if c == '(':
            new_list = []
            stack[-1].append(new_list)
            stack.append(new_list)
            i += 1
        elif c == ')':
            if len(stack) > 1:
                stack.pop()
            i += 1
        elif c == '"':
            start = i + 1
            i += 1
            while i < n and clean_text[i] != '"':
                i += 1
            stack[-1].append(clean_text[start:i])
            i += 1
        elif c.isspace():
            i += 1
        else:
            start = i
            while i < n and not clean_text[i].isspace() and clean_text[i] not in '()':
                i += 1
            stack[-1].append(clean_text[start:i])
            
    return stack[0]

def find_node(tree: list, key: str) -> list | None:
    """Find the first matching (key ...) subtree."""
    for item in tree:
        if isinstance(item, list) and len(item) > 0 and item[0] == key:
            return item
    return None

def get_value(tree: list, key: str, default=None):
    """Get the second element of a (key value) list."""
    node = find_node(tree, key)
    if node and len(node) > 1:
        return node[1]
    return default
