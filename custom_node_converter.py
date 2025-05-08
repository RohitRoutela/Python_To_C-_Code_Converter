import ast
from ast_nodes import *

class CustomNodeConverter(ast.NodeVisitor):
    def visit_Module(self, node):
        return Program([self.visit(stmt) for stmt in node.body])

    def visit_Expr(self, node):
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
        else:
            raise Exception(f"Unsupported constant type: {type(node.value)}")

    def visit_Call(self, node):
        func_name = node.func.id if isinstance(node.func, ast.Name) else "<unknown_func>"
        args = [self.visit(arg) for arg in node.args]
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
        return BinaryOpNode(operator, left, right)

    def visit_If(self, node):
        condition = self.visit(node.test)
        true_branch = [self.visit(stmt) for stmt in node.body]
        false_branch = [self.visit(stmt) for stmt in node.orelse] if node.orelse else None
        return IfNode(condition, true_branch, false_branch)

    def visit_While(self, node):
        condition = self.visit(node.test)
        body = [self.visit(stmt) for stmt in node.body]
        return WhileNode(condition, body)

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
