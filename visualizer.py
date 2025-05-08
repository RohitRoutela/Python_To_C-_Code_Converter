import tkinter as tk
from tkinter import filedialog, messagebox
import ast  # Python's built-in abstract syntax tree module
from ir_generator import IRGenerator
from code_generator import CodeGenerator
from custom_node_converter import CustomNodeConverter  # <-- ADD THIS

class VisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python to C++ Converter")

        # Create GUI components (Text box, buttons, etc.)
        self.code_input = tk.Text(self.root, height=15, width=80)
        self.code_input.pack()

        self.convert_button = tk.Button(self.root, text="Convert", command=self.convert_code)
        self.convert_button.pack()

        self.load_button = tk.Button(self.root, text="Load .py File", command=self.load_file)
        self.load_button.pack()

        self.save_button = tk.Button(self.root, text="Save as .cpp", command=self.save_cpp_file)  # <-- ADD BUTTON
        self.save_button.pack()

        self.output_text = tk.Text(self.root, height=15, width=80)
        self.output_text.pack()

        # Initialize IR and Code Generators
        self.ir_generator = IRGenerator()
        self.code_generator = CodeGenerator()
        self.last_cpp_code = ""  # to hold last generated C++ code for saving

    def convert_code(self):
        """Convert Python code to C++ and display the result."""
        code = self.code_input.get(1.0, tk.END).strip()
        if not code:
            messagebox.showerror("Error", "Please enter or load Python code first.")
            return

        try:
            # Step 1: Parse to Python AST
            python_ast = ast.parse(code)

            # Step 2: Convert to your custom AST
            custom_ast = CustomNodeConverter().visit(python_ast)

            # Step 3: Generate IR
            self.ir_generator.generate(custom_ast)
            ir = self.ir_generator.get_instructions()


            # Step 4: Generate C++ code
            cplusplus_code = self.code_generator.generate(ir)

            # Step 5: Display
            self.display_cpp_code(cplusplus_code)
            self.last_cpp_code = cplusplus_code  # store for saving

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def display_cpp_code(self, cplusplus_code):
        """Display the generated C++ code in the output text box."""
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, cplusplus_code)

    def load_file(self):
        """Load Python code from a file and display in the input text box."""
        file_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
        if file_path:
            with open(file_path, 'r') as file:
                code = file.read()
                self.code_input.delete(1.0, tk.END)
                self.code_input.insert(tk.END, code)

    def save_cpp_file(self):
        """Save the generated C++ code to a file."""
        if not self.last_cpp_code.strip():
            messagebox.showerror("Error", "No C++ code to save. Please convert Python code first.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".cpp", filetypes=[("C++ Files", "*.cpp")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.last_cpp_code)
            messagebox.showinfo("Success", "C++ code saved successfully.")
