# lexer.py

class Token:
    def __init__(self, type_, value, line=None):
        # Store token type, value and line number
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        line_info = f", line={self.line}" if self.line is not None else ""
        return f"Token({self.type}, {repr(self.value)}{line_info})"


# Collection of recognized language elements
KEYWORDS = {'def', 'return', 'if', 'else', 'elif', 'while', 'for', 'print', 'True', 'False', 'None', 'in', 'and', 'or', 'not', 'is', 'pass', 'break', 'continue'}

# Supported data types
DATA_TYPES = {'int', 'float', 'bool', 'str', 'list', 'tuple', 'dict', 'set'}

# Supported symbols
SYMBOLS = {'(', ')', ':', ',', '[', ']', '{', '}', '.'}

# Supported operators (single character)
OPERATORS = {'+', '-', '*', '/', '%', '=', '<', '>', '!', '&', '|', '^', '~'}

# Multi-character operators
MULTI_CHAR_OPERATORS = {
    '==', '!=', '<=', '>=', '+=', '-=', '*=', '/=', '%=', '**', '//', '<<', '>>'
}


def tokenize(code):
    # Transform source code into a list of tokens
    tokens = []
    i = 0
    length = len(code)
    
    # Track line numbers for better error reporting
    line_number = 1
    
    # Remove any BOM or special hidden characters that might be present
    if code.startswith("\ufeff"):  # UTF-8 BOM
        code = code[1:]
        length = len(code)
    
    # Track indentation
    indent_stack = [0]
    current_indent = 0

    while i < length:
        if i >= length:
            break
            
        try:
            c = code[i]
        except IndexError:
            print(f"Index error at position {i}, length is {length}")
            break
            
        # Debug non-printable characters
        if not c.isprintable() and c not in ['\n', '\t', ' ']:
            print(f"Non-printable character at position {i}: {repr(c)} (ord: {ord(c)})")

        # New line - check indentation
        if c == '\n':
            i += 1
            line_number += 1
            
            # Skip empty lines
            while i < length and code[i] in ' \t\n':
                if code[i] == '\n':
                    line_number += 1
                i += 1
                
            if i < length:
                # Count spaces at the beginning of line
                start = i
                while i < length and code[i] in ' \t':
                    i += 1
                
                # Calculate indentation level
                indent_level = i - start
                
                # Compare to previous indent level
                if indent_level > indent_stack[-1]:
                    # New block
                    indent_stack.append(indent_level)
                    tokens.append(Token('INDENT', indent_level, line_number))
                elif indent_level < indent_stack[-1]:
                    # End of block(s)
                    while indent_level < indent_stack[-1]:
                        indent_stack.pop()
                        tokens.append(Token('DEDENT', None, line_number))
                    if indent_level != indent_stack[-1]:
                        raise Exception(f"Invalid indentation at line {line_number}")
                
                continue
            
        if c in ' \t':
            i += 1
            continue

        elif c == '#':
            # Comment - skip to end of line
            while i < length and code[i] != '\n':
                i += 1
            continue

        elif c.isalpha() or c == '_':
            # Identifier or keyword
            start = i
            while i < length and (code[i].isalnum() or code[i] == '_'):
                i += 1
            word = code[start:i]
            
            if word in KEYWORDS:
                tokens.append(Token('KEYWORD', word, line_number))
            elif word in DATA_TYPES:
                tokens.append(Token('DATA_TYPE', word, line_number))
            elif word == 'True' or word == 'False':
                tokens.append(Token('BOOL', word == 'True', line_number))
            elif word == 'None':
                tokens.append(Token('NONE', None, line_number))
            else:
                tokens.append(Token('IDENTIFIER', word, line_number))

        elif c.isdigit() or (c == '.' and i + 1 < length and code[i + 1].isdigit()):
            # Number (integer or float)
            start = i
            has_dot = False
            while i < length and (code[i].isdigit() or (code[i] == '.' and not has_dot)):
                if code[i] == '.':
                    has_dot = True
                i += 1
            number = code[start:i]
            
            if has_dot:
                tokens.append(Token('NUMBER', float(number), line_number))
            else:
                tokens.append(Token('NUMBER', int(number), line_number))

        elif c == '"' or c == "'":
            # String literal
            quote = c
            i += 1
            start = i
            while i < length and code[i] != quote:
                if code[i] == '\\' and i + 1 < length:  # Handle escape sequences
                    i += 2
                else:
                    i += 1
            if i >= length:
                raise Exception(f"Unterminated string literal at line {line_number}")
            string = code[start:i]
            i += 1  # skip closing quote
            tokens.append(Token('STRING', string, line_number))

        elif c in SYMBOLS:
            tokens.append(Token('SYMBOL', c, line_number))
            i += 1

        elif c in OPERATORS:
            # Check for multi-character operators
            if i + 1 < length and code[i:i+2] in MULTI_CHAR_OPERATORS:
                tokens.append(Token('OPERATOR', code[i:i+2], line_number))
                i += 2
            elif i + 1 < length and c == '*' and code[i+1] == '*':
                tokens.append(Token('OPERATOR', '**', line_number))  # Power operator
                i += 2
            else:
                tokens.append(Token('OPERATOR', c, line_number))
                i += 1

        else:
            if ord(c) < 32:  # Control characters
                i += 1  # Skip control characters
                continue
            elif ord(c) > 127:  # Non-ASCII
                i += 1  # Skip non-ASCII
                continue
            else:
                char_repr = repr(c).replace("'", "")
                raise Exception(f"Unknown character: {char_repr} (ord={ord(c)}) at line {line_number}, position {i}")

    # Add any remaining DEDENT tokens
    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(Token('DEDENT', None, line_number))

    return tokens
