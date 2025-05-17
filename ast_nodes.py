# ast_nodes.py

class ASTNode:
    # Base class for all nodes in the Abstract Syntax Tree
    pass


class Program(ASTNode):
    def __init__(self, statements):
        # Root node containing all program statements
        self.statements = statements

    def __repr__(self):
        return f"Program({self.statements})"


class AssignmentNode(ASTNode):
    def __init__(self, identifier, expression, comments=None):
        # Represents a variable assignment operation
        self.identifier = identifier
        self.expression = expression
        self.comments = comments

    def __repr__(self):
        return f"AssignmentNode({self.identifier} = {self.expression})"


class IfNode(ASTNode):
    def __init__(self, condition, true_branch, false_branch=None):
        # Represents an if-else conditional structure
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch

    def __repr__(self):
        return f"IfNode(condition={self.condition}, true={self.true_branch}, false={self.false_branch})"


class WhileNode(ASTNode):
    def __init__(self, condition, body):
        # Represents a while loop structure
        self.condition = condition
        self.body = body

    def __repr__(self):
        return f"WhileNode(condition={self.condition}, body={self.body})"


class ForNode(ASTNode):
    def __init__(self, variable, iterable, body):
        # Represents a for loop iterating over a sequence
        self.variable = variable
        self.iterable = iterable
        self.body = body

    def __repr__(self):
        return f"ForNode(variable={self.variable}, iterable={self.iterable}, body={self.body})"


class PrintNode(ASTNode):
    def __init__(self, expression):
        # Represents a print statement
        self.expression = expression

    def __repr__(self):
        return f"PrintNode({self.expression})"


class BinaryOpNode(ASTNode):
    def __init__(self, left, operator, right):
        # Represents a binary operation (e.g., +, -, *, /, etc.)
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"BinaryOpNode({self.left} {self.operator} {self.right})"


class IdentifierNode(ASTNode):
    def __init__(self, name):
        # Represents a variable reference
        self.name = name

    def __repr__(self):
        return f"IdentifierNode({self.name})"


class NumberNode(ASTNode):
    def __init__(self, value):
        # Represents a numeric literal (int or float)
        self.value = value

    def __repr__(self):
        return f"NumberNode({self.value})"


class StringNode(ASTNode):
    def __init__(self, value):
        # Represents a string literal
        self.value = value

    def __repr__(self):
        return f'StringNode("{self.value}")'


class FunctionCallNode(ASTNode):
    def __init__(self, function_name, arguments):
        # Represents a function call with arguments
        self.function_name = function_name
        self.arguments = arguments

    def __repr__(self):
        return f"FunctionCallNode({self.function_name}, {self.arguments})"


class FunctionDefNode(ASTNode):
    def __init__(self, name, parameters, body):
        # Represents a function definition
        self.name = name
        self.parameters = parameters
        self.body = body

    def __repr__(self):
        return f"FunctionDefNode(name={self.name}, params={self.parameters}, body={self.body})"


class ReturnNode(ASTNode):
    def __init__(self, value):
        # Represents a return statement in a function
        self.value = value

    def __repr__(self):
        return f"ReturnNode({self.value})"


class ExpressionNode(ASTNode):
    # Base class for all expression nodes
    pass


class ListNode(ASTNode):
    def __init__(self, elements):
        # Represents a list literal with elements
        self.elements = elements

    def __repr__(self):
        return f"ListNode({self.elements})"


class InputNode(ASTNode):
    def __init__(self, prompt):
        # Represents an input operation with optional prompt
        self.prompt = prompt

    def __repr__(self):
        return f"InputNode(prompt={self.prompt})"
