import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter.font import Font
import ast
from ir_generator import IRGenerator
from code_generator import CodeGenerator
from custom_node_converter import CustomNodeConverter
import pyperclip
import os

class LineNumberedText(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        
        # Create a frame for line numbers
        self.line_numbers = tk.Text(self, width=4, padx=4, takefocus=0, border=0,background='lightgray', state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Create the main text widget
        self.text = scrolledtext.ScrolledText(self, **kwargs)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Link scrollbars between text and line numbers
        self.text.vbar = self.text.vbar  # Get the scrollbar from ScrolledText
        
        # Bind events
        self.text.bind('<KeyRelease>', self._on_key_release)
        self.text.bind('<MouseWheel>', self._on_mousewheel)
        
        # Initial line numbers
        self.update_line_numbers()
        
    def _on_key_release(self, event=None):
        self.update_line_numbers()
        
    def _on_mousewheel(self, event=None):
        self.update_line_numbers()
        
    def update_line_numbers(self):
        try:
            # Get the text content safely
            text_content = self.text.get('1.0', tk.END)
            lines = text_content.count('\n') + 1
            if lines < 3:
                lines = 3
                
            # Create the line numbers text
            numbers = '\n'.join(str(i) for i in range(1, lines + 1))
            
            # Update line numbers text widget
            self.line_numbers.config(state='normal')
            self.line_numbers.delete('1.0', tk.END)
            self.line_numbers.insert('1.0', numbers)
            self.line_numbers.config(state='disabled')
        except Exception as e:
            print(f"Error updating line numbers: {e}")
        
    # Delegate methods to text widget
    def get(self, *args, **kwargs):
        try:
            return self.text.get(*args, **kwargs)
        except Exception as e:
            print(f"Error in get: {e}")
            return ""
        
    def insert(self, index, chars, *tags):
        try:
            return self.text.insert(index, chars, *tags)
        except Exception as e:
            print(f"Error in insert: {e}")
        
    def delete(self, *args, **kwargs):
        try:
            return self.text.delete(*args, **kwargs)
        except Exception as e:
            print(f"Error in delete: {e}")
        
    def bind(self, *args, **kwargs):
        try:
            return self.text.bind(*args, **kwargs)
        except Exception as e:
            print(f"Error in bind: {e}")
        
    def focus_set(self):
        try:
            return self.text.focus_set()
        except Exception as e:
            print(f"Error in focus_set: {e}")
            
    def see(self, *args, **kwargs):
        try:
            return self.text.see(*args, **kwargs)
        except Exception as e:
            print(f"Error in see: {e}")
            
    def tag_add(self, *args, **kwargs):
        try:
            return self.text.tag_add(*args, **kwargs)
        except Exception as e:
            print(f"Error in tag_add: {e}")
            
    def tag_config(self, *args, **kwargs):
        try:
            return self.text.tag_config(*args, **kwargs)
        except Exception as e:
            print(f"Error in tag_config: {e}")
            
    def config(self, *args, **kwargs):
        try:
            return self.text.config(*args, **kwargs)
        except Exception as e:
            print(f"Error in config: {e}")
            
    def configure(self, *args, **kwargs):
        try:
            return self.text.configure(*args, **kwargs)
        except Exception as e:
            print(f"Error in configure: {e}")
            
    # Forward any other attribute access to the text widget
    def __getattr__(self, name):
        try:
            return getattr(self.text, name)
        except AttributeError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

class VisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python to C++ Converter")
        self.root.geometry("1200x800")
        
        # Configure styles
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TFrame', padding=5)
        
        # Create main container
        main_container = ttk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create top frame for buttons
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons
        self.load_button = ttk.Button(button_frame, text="Load Python File", command=self.load_file)
        self.load_button.pack(side=tk.LEFT, padx=5)
        
        self.convert_button = ttk.Button(button_frame, text="Convert to C++", command=self.convert_code)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = ttk.Button(button_frame, text="Save C++ File", command=self.save_cpp_file)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.copy_button = ttk.Button(button_frame, text="Copy C++ to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(button_frame, text="Clear All", command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Create code container with Panedwindow
        code_container = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        code_container.pack(fill=tk.BOTH, expand=True)
        
        # Input frame
        input_frame = ttk.LabelFrame(code_container, text="Python Code")
        code_container.add(input_frame, weight=1)
        
        # Output frame
        output_frame = ttk.LabelFrame(code_container, text="C++ Code")
        code_container.add(output_frame, weight=1)
        
        # Create text widgets with line numbers
        self.code_input = LineNumberedText(input_frame, wrap=tk.NONE, font=('Consolas', 10))
        self.code_input.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = LineNumberedText(output_frame, wrap=tk.NONE, font=('Consolas', 10))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(main_container, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        self.status_var.set("Ready")
        
        # Initialize components
        self.ir_generator = IRGenerator()
        self.code_generator = CodeGenerator()
        self.last_cpp_code = ""
        
        # Recent files list
        self.recent_files = []
        self.load_recent_files()
        self.create_recent_files_menu()

    def load_recent_files(self):
        try:
            if os.path.exists('.recent_files'):
                with open('.recent_files', 'r') as f:
                    self.recent_files = [line.strip() for line in f.readlines()]
        except:
            self.recent_files = []

    def save_recent_files(self):
        try:
            with open('.recent_files', 'w') as f:
                for file in self.recent_files[-10:]:  # Keep only last 10 files
                    f.write(f"{file}\n")
        except:
            pass

    def create_recent_files_menu(self):
        self.recent_menu = tk.Menu(self.root, tearoff=0)
        for file in self.recent_files:
            self.recent_menu.add_command(label=file, command=lambda f=file: self.load_specific_file(f))

    def add_to_recent_files(self, filepath):
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.append(filepath)
        self.save_recent_files()
        self.create_recent_files_menu()

    def load_specific_file(self, filepath):
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                code = file.read()
                self.code_input.delete('1.0', tk.END)
                self.code_input.insert(tk.END, code)
                self.code_input.update_line_numbers()
                self.add_to_recent_files(filepath)
                self.status_var.set(f"Loaded: {filepath}")
        else:
            messagebox.showerror("Error", f"File not found: {filepath}")

    def convert_code(self):
        """Convert Python code to C++ and display the result."""
        code = self.code_input.get('1.0', tk.END).strip()
        if not code:
            messagebox.showerror("Error", "Please enter or load Python code first.")
            return

        try:
            self.status_var.set("Converting...")
            self.root.update()

            # Step 1: Parse to Python AST
            python_ast = ast.parse(code)

            # Step 2: Convert to custom AST
            custom_ast = CustomNodeConverter().visit(python_ast)

            # Step 3: Generate IR
            self.ir_generator.generate(custom_ast)
            ir = self.ir_generator.get_instructions()

            # Step 4: Generate C++ code
            cplusplus_code = self.code_generator.generate(ir)
            
            # Ensure we got a valid string
            if cplusplus_code is None:
                cplusplus_code = "// Error: Code generation returned None"
            self.last_cpp_code = self.code_generator.get_cpp_code()
            if self.last_cpp_code is None:
                self.last_cpp_code = "// Error: No C++ code generated"

            # Step 5: Display with syntax highlighting
            self.display_cpp_code(self.last_cpp_code)

            self.status_var.set("Conversion completed successfully")

        except SyntaxError as e:
            self.status_var.set(f"Syntax Error: {str(e)}")
            messagebox.showerror("Syntax Error", f"Line {e.lineno if hasattr(e, 'lineno') else '?'}: {e.msg if hasattr(e, 'msg') else str(e)}")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {e}")
            import traceback
            traceback.print_exc()

    def display_cpp_code(self, cplusplus_code):
        """Display the generated C++ code with syntax highlighting."""
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert(tk.END, cplusplus_code)
        self.output_text.update_line_numbers()

    def load_file(self):
        """Load Python code from a file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    code = file.read()
                    self.code_input.delete('1.0', tk.END)
                    self.code_input.insert(tk.END, code)
                    self.code_input.update_line_numbers()
                    self.add_to_recent_files(file_path)
                    self.status_var.set(f"Loaded: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def save_cpp_file(self):
        """Save the generated C++ code to a file."""
        if not self.last_cpp_code.strip():
            messagebox.showerror("Error", "No C++ code to save. Please convert Python code first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".cpp",
            filetypes=[("C++ Files", "*.cpp"), ("All files", "*.*")])
        
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(self.last_cpp_code)
                self.status_var.set(f"Saved: {file_path}")
                messagebox.showinfo("Success", "C++ code saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def copy_to_clipboard(self):
        """Copy the generated C++ code to clipboard."""
        if not self.last_cpp_code or not self.last_cpp_code.strip():
            messagebox.showerror("Error", "No C++ code to copy. Please convert Python code first.")
            return
        
        pyperclip.copy(self.last_cpp_code)
        self.status_var.set("C++ code copied to clipboard")

    def clear_all(self):
        """Clear both input and output text areas."""
        self.code_input.delete('1.0', tk.END)
        self.output_text.delete('1.0', tk.END)
        # Reinitialize code generators to clear any stored state
        self.ir_generator = IRGenerator()
        self.code_generator = CodeGenerator()
        self.last_cpp_code = ""
        self.status_var.set("Cleared all text areas")

if __name__ == "__main__":
    root = tk.Tk()
    app = VisualizerApp(root)
    root.mainloop() 
