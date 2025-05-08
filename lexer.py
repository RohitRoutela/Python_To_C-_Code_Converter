# lexer.py

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"


# Set of Python keywords
KEYWORDS = {'def', 'return', 'if', 'else', 'while', 'for', 'print', 'True', 'False', 'in'}

# Supported data types
DATA_TYPES = {'int', 'float', 'bool', 'str'}

# Supported symbols
SYMBOLS = {'(', ')', ':', ',', '[', ']', '{', '}'}

# Supported operators
OPERATORS = {'+', '-', '*', '/', '%', '=', '<', '>', '!', '&', '|', '^', '~'}


def tokenize(code):
    tokens = []
    i = 0
    length = len(code)

    while i < length:
        c = code[i]

        if c in ' \t':
            i += 1
            continue

        elif c == '\n':
            tokens.append(Token('NEWLINE', '\\n'))
            i += 1

        elif c == '#':
            while i < length and code[i] != '\n':
                i += 1
            continue

        elif c.isalpha() or c == '_':
            start = i
            while i < length and (code[i].isalnum() or code[i] == '_'):
                i += 1
            word = code[start:i]
            if word in KEYWORDS:
                tokens.append(Token('KEYWORD', word))
            elif word in DATA_TYPES:
                tokens.append(Token('DATA_TYPE', word))
            else:
                tokens.append(Token('IDENTIFIER', word))

        elif c.isdigit() or (c == '.' and i + 1 < length and code[i + 1].isdigit()):
            start = i
            has_dot = False
            while i < length and (code[i].isdigit() or (code[i] == '.' and not has_dot)):
                if code[i] == '.':
                    has_dot = True
                i += 1
            number = code[start:i]
            tokens.append(Token('NUMBER', number))

        elif c == '"':
            i += 1
            start = i
            while i < length and code[i] != '"':
                i += 1
            if i >= length:
                raise Exception("Unterminated string literal")
            string = code[start:i]
            i += 1  # skip closing quote
            tokens.append(Token('STRING', string))

        elif c in SYMBOLS:
            tokens.append(Token('SYMBOL', c))
            i += 1

        elif c in OPERATORS:
            tokens.append(Token('OPERATOR', c))
            i += 1

        else:
            raise Exception(f"Unknown character: {c}")

    return tokens
