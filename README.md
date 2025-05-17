# Python to C++ Code Converter

A GUI application that converts Python code to C++ code with a modern and user-friendly interface.

## Features

- Modern, intuitive user interface
- Line numbers for both input and output
- Syntax highlighting
- File upload and download support
- Copy to clipboard functionality
- Recent files history
- Detailed error reporting
- Status bar for feedback

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd Python_To_C++_Code_Converter
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. The application window will open with two main areas:
   - Left panel: Python code input
   - Right panel: C++ code output

3. You can:
   - Type Python code directly in the left panel
   - Load a Python file using the "Load Python File" button
   - Convert the code using the "Convert to C++" button
   - Save the generated C++ code using the "Save C++ File" button
   - Copy the C++ code to clipboard using the "Copy C++ to Clipboard" button
   - Clear both panels using the "Clear All" button

4. The status bar at the bottom shows the current status and any error messages.

## Error Handling

The application provides detailed error messages for:
- Syntax errors in Python code
- Conversion errors
- File operations
- Unsupported Python features

## Contributing

Feel free to submit issues and enhancement requests!
