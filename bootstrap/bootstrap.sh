#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

# Assert pyenv is installed
command -v pyenv >/dev/null 2>&1 || { echo >&2 "pyenv is not installed. Aborting."; exit 1; }

# Load pyenv and pyenv-virtualenv
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Install Python 3.12.4 if not already installed
if ! pyenv versions | grep -q 3.12.4; then
    echo "Installing Python 3.12.4..."
    PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.12.4 || { echo "Failed to install Python 3.12.4. Please check system requirements."; exit 1; }
fi

# Create or update the 'loco' environment
pyenv virtualenv 3.12.4 loco 2>/dev/null || true

# Activate the environment
pyenv activate loco || { echo "Failed to activate 'loco' environment. Aborting."; exit 1; }

# Verify Python version
python_version=$(python --version 2>&1)
if [[ $python_version != *"3.12.4"* ]]; then
    echo "Python is not correctly resolving to version 3.12.4 in the 'loco' environment"
    echo "Current version: $python_version"
    exit 1
else
    echo "Python is correctly resolving to version 3.12.4 in the 'loco' environment"
fi

# Verify pip
if ! command -v pip &> /dev/null; then
    echo "pip is not available in the 'loco' environment"
    exit 1
else
    echo "pip is correctly resolving in the 'loco' environment"
fi

# Print Python and pip versions
python --version
pip --version

# Install requirements
if [ -f dev-requirements.txt ]; then
    pip install -r dev-requirements.txt
else
    echo "dev-requirements.txt not found. Skipping package installation."
fi

command -v aider >/dev/null 2>&1 || { echo >&2 "aider is not installed or not in PATH. Aborting."; exit 1; }