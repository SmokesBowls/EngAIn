import re

def tokenize(text):
    """Split ZW text into tokens"""
    tokens = []
    # Pattern: braces/brackets, quoted strings, or words (excluding braces/brackets)
    pattern = r'[{}\[\]]|"[^"]*"|[^{}\[\]\s]+'
    
    for match in re.finditer(pattern, text):
        token = match.group()
        # Remove quotes from strings
        if token.startswith('"'):
            token = token[1:-1]
        tokens.append(token)
    
    return tokens

def parse_zw(zw_text):
    """Main entry point: tokenize then parse"""
    tokens = tokenize(zw_text)
    print(f"DEBUG: Tokens = {tokens[:20]}")  # Show first 20 tokens
    return parse_tokens(tokens)

def parse_tokens(tokens):
    tokens = list(tokens)
    pos = [0]
    
    def peek():
        return tokens[pos[0]] if pos[0] < len(tokens) else None
    
    def consume():
        tok = tokens[pos[0]]
        pos[0] += 1
        return tok
    
    def coerce(val):
        if val == "true": return True
        if val == "false": return False
        if re.match(r'^-?\d+$', val): return int(val)
        if re.match(r'^-?\d+\.\d+$', val): return float(val)
        return val
    
    def parse():
        tok = peek()
        
        if tok == '{':
            consume()  # eat {
            key = consume()
            
            # Parse children until }
            children = []
            while peek() and peek() != '}':
                children.append(parse())
            
            consume()  # eat }
            
            # Build result based on children
            if len(children) == 0:
                return {key: None}
            elif len(children) == 1 and not isinstance(children[0], dict):
                return {key: children[0]}
            else:
                # Merge dict children, handling duplicates
                result = {}
                for child in children:
                    if isinstance(child, dict):
                        for k, v in child.items():
                            if k in result:
                                if not isinstance(result[k], list):
                                    result[k] = [result[k]]
                                result[k].append(v)
                            else:
                                result[k] = v
                    else:
                        # Non-dict child in multi-child context
                        if 'values' not in result:
                            result['values'] = []
                        result['values'].append(child)
                return {key: result}
        
        elif tok == '[':  # 👈 ARRAY HANDLING - NOW IN THE RIGHT PLACE
            consume()  # eat [
            arr = []
            while peek() and peek() != ']':
                arr.append(parse())
            consume()  # eat ]
            return arr
        
        else:
            return coerce(consume())
    
    return parse()
