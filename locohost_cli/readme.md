# Locohost CLI

Locohost CLI is an AI-assisted project management and development tool for Kubernetes-based applications.

## Installation

To install Locohost CLI, run:

```
pip install -e .
```

## Running Tests

To run the tests for Locohost CLI, follow these steps:

1. Ensure you have pytest installed. If not, install it using:
   ```
   pip install pytest
   ```

2. Navigate to the root directory of the project.

3. Run the tests using pytest:
   ```
   pytest locohost_cli/test_cot_operations.py
   ```

This will run all the tests in the `test_cot_operations.py` file.

## Usage

To use Locohost CLI, run the following command:

```
python -m locohost_cli <action> [options]
```

For a list of available actions and options, run:

```
python -m locohost_cli --help
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
