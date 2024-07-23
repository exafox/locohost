# Locohost CLI

Locohost CLI is an AI-assisted project management and development tool for Kubernetes-based applications.

## Installation

To install Locohost CLI, run:

```
pip install -r requirements.txt
pip install -e .
```

## Running Tests

To run the tests for Locohost CLI, follow these steps:

1. Ensure you have pytest installed. If not, install it using:
   ```
   pip install pytest pytest-html
   ```

2. Navigate to the root directory of the project.

3. Run the tests using pytest:
   ```
   pytest locohost_cli/test_cot_operations.py locohost_cli/test_performance.py --html=report.html --self-contained-html
   ```

This will run all the tests in both `test_cot_operations.py` and `test_performance.py` files and generate an HTML report.

## Usage

To use Locohost CLI, run the following command:

```
python -m locohost_cli <action> [options]
```

For a list of available actions and options, run:

```
python -m locohost_cli --help
```

## Features

- Chain of Thought (CoT) journaling
- Project initialization and management
- Code editing with AI assistance
- Test generation and execution
- Performance testing
- Search functionality within project files

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
