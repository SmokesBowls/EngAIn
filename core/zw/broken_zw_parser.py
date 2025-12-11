import re

def tokenize(text):
    # Split by whitespace and keep brackets/quotes as separate tokens
    return re.findall(r'\{|\}|\[|\]|"(.*?)"|[^\s\{\}\[\]"]+', text)

def parse_tokens(tokens):
    def parse_value():
        tok = tokens.pop(0)
        if tok == '{':
            key = tokens.pop(0)
            obj = {}
            while tokens and tokens[0] != '}':
                k = tokens.pop(0)
                v = parse_value()
                obj[k] = v
            tokens.pop(0)  # pop '}'
            return {key: obj}
        elif tok == '[':
            arr = []
            while tokens and tokens[0] != ']':
                arr.append(parse_value())
            tokens.pop(0)  # pop ']'
            return arr
        elif tok.startswith('"') and tok.endswith('"'):
            return tok[1:-1]
        elif tok.isdigit():
            return int(tok)
        elif tok == 'true':
            return True
        elif tok == 'false':
            return False
        else:
            return tok
def parse_zw(text):
    tokens = tokenize(text)
    print("TOKENS:", tokens)  # 👈 Add this debug line
    return parse_tokens(tokens)
          

    return parse_value()


def parse_zw(text):
    tokens = tokenize(text)
    return parse_tokens(tokens)
