# Locohost CLI

Locohost CLI is an AI-assisted project management and development tool for Kubernetes-based applications.

## Features

- Create and edit Product Requirements Documents (PRDs)
- Initialize projects with Chain of Thought (CoT) journaling
- Manage git operations with AI-assisted commit messages
- Run and analyze tests
- Deploy and analyze deployment information
- Generate and edit project code
- Generate tests for code changes
- Review and refactor code
- Generate performance tests
- Manage database migrations
- Generate and update project documentation
- Configure local and production deployments

## Installation

To install Locohost CLI, follow these steps:

1. Ensure you have `pyenv` installed on your system.

2. Set your Anthropic API key:
   ```
   export ANTHROPIC_API_KEY=your-key-goes-here
   ```

3. If you're using conda, deactivate any active conda environments:
   ```
   conda deactivate
   ```

4. Run the bootstrap script:
   ```
   ./bootstrap/bootstrap.sh
   ```

   This script will set up the necessary Python environment and install required dependencies.

5. Activate the 'loco' environment:
   ```
   pyenv activate loco
   ```

6. Navigate to the `locohost_cli` directory and install the package:
   ```
   cd locohost_cli
   pip install -e .
   ```

## Usage

To use Locohost CLI, run the following command:

```
python -m locohost_cli <action> [options]
```

For a list of available actions and options, run:

```
python -m locohost_cli --help
```

## Examples

Here are some example commands:

```
python -m locohost_cli create_prd --project-context-file project_context.txt
python -m locohost_cli edit_prd --project-name MyProject --prd-file MyProject_PRD.md
python -m locohost_cli start_project --project-name MyProject
python -m locohost_cli deploy --project-name MyProject
python -m locohost_cli generate_new_project_code --project-name MyProject --language Python
```

## Running Tests

To run the tests for Locohost CLI, use the following command:

```
pytest locohost_cli/test_cot_operations.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.
