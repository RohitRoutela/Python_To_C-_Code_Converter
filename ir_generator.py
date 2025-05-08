from ast_nodes import *

class IRGenerator:
    def __init__(self):
        self.instructions = []
        self.label_count = 0

    def new_label(self):
        self.label_count += 1
        return f"label_{self.label_count}"

    def generate(self, node):
        if isinstance(node, list):
            for stmt in node:
                self.generate(stmt)

        elif isinstance(node, Program):
            for stmt in node.statements:
                self.generate(stmt)

        elif isinstance(node, AssignmentNode):
            expr = self.generate(node.expression)
            self.instructions.append(('assign', node.identifier, expr))

        elif isinstance(node, PrintNode):
            expr = self.generate(node.expression)
            self.instructions.append(('print', expr))

        elif isinstance(node, IfNode):
            condition_ir = self.generate(node.condition)

            true_branch_ir = self._generate_block(node.true_branch)
            false_branch_ir = self._generate_block(node.false_branch) if node.false_branch else None

            self.instructions.append(('if', condition_ir, true_branch_ir, false_branch_ir))

        elif isinstance(node, WhileNode):
            condition_ir = self.generate(node.condition)
            body_ir = self._generate_block(node.body)
            self.instructions.append(('while', condition_ir, body_ir))

        elif isinstance(node, ForNode):
            iterable_ir = self.generate(node.iterable)
            body_ir = self._generate_block(node.body)
            self.instructions.append(('for', node.variable, iterable_ir, body_ir))

        elif isinstance(node, FunctionCallNode):
            args = [self.generate(arg) for arg in node.arguments]
            return ('function_call', node.function_name, args)

        elif isinstance(node, FunctionDefNode):
            body_ir = self._generate_block(node.body)
            self.instructions.append(('function_def', node.name, node.parameters, body_ir))

        elif isinstance(node, ReturnNode):
            value_ir = self.generate(node.value) if node.value is not None else None
            self.instructions.append(('return', value_ir))

        elif isinstance(node, BinaryOpNode):
            left = self.generate(node.left)
            right = self.generate(node.right)
            return ('binop', node.operator, left, right)

        elif isinstance(node, IdentifierNode):
            return ('var', node.name)

        elif isinstance(node, NumberNode) or isinstance(node, StringNode):
            return ('const', node.value)

        else:
            raise Exception(f"Unknown node type: {type(node).__name__}")

    def _generate_block(self, statements):
        """Generate a list of instructions for a block of statements."""
        sub_generator = IRGenerator()
        sub_generator.label_count = self.label_count  # Maintain label continuity
        sub_generator.generate(statements)
        self.label_count = sub_generator.label_count  # Update label count back
        return sub_generator.get_instructions()

    def get_instructions(self):
        return self.instructions
