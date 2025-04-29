KEYWORDS = {"if", "else", "while", "for", "print", "input", "True", "False", "in"}
OPERATORS = {"=", "+", "-", "*", "/", "==", "!=", "<", ">", "<=", ">="}

class Token:
    def __init__(self, type_, value, line_number):
        self.type = type_
        self.value = value
        self.line_number = line_number

    def __repr__(self):
        return f"Token({self.type}, {self.value}, Line {self.line_number})"


def tokenize(code):
    tokens = []
    i = 0
    line_number = 1  # Start with line 1
    while i < len(code):
        ch = code[i]

        # Handle whitespace
        if ch in ' \t':
            i += 1
            continue

        # Handle newlines (for line tracking)
        elif ch == '\n':
            tokens.append(Token("NEWLINE", ch, line_number))
            line_number += 1
            i += 1
            continue

        # Handle comments (skip everything after # until the end of the line)
        elif ch == '#':
            while i < len(code) and code[i] != '\n':
                i += 1
            continue  # Skip the entire comment line

        # Identifiers and Keywords
        elif ch.isalpha() or ch == '_':
            start = i
            while i < len(code) and (code[i].isalnum() or code[i] == '_'):
                i += 1
            word = code[start:i]
            if word in KEYWORDS:
                tokens.append(Token("KEYWORD", word, line_number))
            else:
                tokens.append(Token("IDENTIFIER", word, line_number))

        # Numbers (integers and floats)
        elif ch.isdigit() or ch == ".":
            start = i
            if ch == ".":  # For handling floating-point numbers starting with a dot
                i += 1
            while i < len(code) and (code[i].isdigit() or code[i] == "."):
                i += 1
            number_str = code[start:i]
            # Ensure it's a valid float if it contains a decimal point
            if '.' in number_str:
                tokens.append(Token("NUMBER", number_str, line_number))
            else:
                tokens.append(Token("NUMBER", number_str, line_number))