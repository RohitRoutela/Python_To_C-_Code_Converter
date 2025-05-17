import ast
from ast_nodes import *

class CustomNodeConverter(ast.NodeVisitor):
    def visit_Module(self, node):
        return Program([self.visit(stmt) for stmt in node.body])

    def visit_Expr(self, node):
        # Check if this is a print call
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'print':
            args = node.value.args
            if args:
                return PrintNode(self.visit(args[0]))
            else:
                return PrintNode(StringNode(""))
        return self.visit(node.value)

    def visit_Assign(self, node):
        target = self.visit(node.targets[0])
        value = self.visit(node.value)
        return AssignmentNode(target.name, value)

    def visit_Name(self, node):
        return IdentifierNode(node.id)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            return StringNode(node.value)
        elif isinstance(node.value, (int, float)):
            return NumberNode(node.value)
        elif node.value is None:
            return StringNode("nullptr")
        else:
            raise Exception(f"Unsupported constant type: {type(node.value)}")

    def visit_Call(self, node):
        func_name = node.func.id if isinstance(node.func, ast.Name) else "<unknown_func>"
        args = [self.visit(arg) for arg in node.args]
        
        # Special handling for input() function
        if func_name == 'input':
            # Create a special InputNode to represent getting input from the user
            # If there's a prompt string, we'll use it
            prompt = args[0] if args else StringNode("")
            return InputNode(prompt)
            
        return FunctionCallNode(func_name, args)

    def visit_BinOp(self, node):
        op_map = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
            ast.Mod: '%',
            ast.Pow: '**'
        }
        left = self.visit(node.left)
        right = self.visit(node.right)
        operator = op_map.get(type(node.op), None)
        if operator is None:
            raise Exception(f"Unsupported binary operator: {type(node.op)}")
        # Fix: Correctly pass parameters in the right order: left, operator, right
        return BinaryOpNode(left, operator, right)

    def visit_JoinedStr(self, node):
        # Handle f-strings
        parts = []
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                # Mark formatted variables to avoid unnecessary to_string conversions later
                if isinstance(value.value, ast.Name):
                    # This is a variable inside f-string, we need to remember it's already meant to be a string
                    var_name = value.value.id
                    parts.append(ast.Name(id=var_name, ctx=ast.Load(), _is_string_format=True))
                else:
                    parts.append(self.visit(value.value))
            else:
                parts.append(ast.Constant(value=ast.literal_eval(value)))

        # Create expression for string concatenation
        result = parts[0]
        for part in parts[1:]:
            result = ast.BinOp(left=result, op=ast.Add(), right=part)
        return result
        
    def visit_FormattedValue(self, node):
        # Handle expressions inside f-strings
        value = self.visit(node.value)
        # In C++, we'll need to convert the value to string
        # We'll represent this as a function call to str() for now
        return FunctionCallNode("str", [value])

    def visit_If(self, node):
        condition = self.visit(node.test)
        true_branch = [self.visit(stmt) for stmt in node.body]
        false_branch = [self.visit(stmt) for stmt in node.orelse] if node.orelse else None
        return IfNode(condition, true_branch, false_branch)

    def visit_While(self, node):
        condition = self.visit(node.test)
        body = [self.visit(stmt) for stmt in node.body]
        return WhileNode(condition, body)
        
    def visit_For(self, node):
        # Add support for For loops
        target = self.visit(node.target)
        iter_expr = self.visit(node.iter)
        body = [self.visit(stmt) for stmt in node.body]
        return ForNode(target.name, iter_expr, body)

    def visit_Return(self, node):
        value = self.visit(node.value) if node.value else None
        return ReturnNode(value)

    def visit_FunctionDef(self, node):
        name = node.name
        parameters = [arg.arg for arg in node.args.args]
        body = [self.visit(stmt) for stmt in node.body]
        return FunctionDefNode(name, parameters, body)

    def generic_visit(self, node):
        raise Exception(f"Unsupported AST node: {type(node).__name__}")
