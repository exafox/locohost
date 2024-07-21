import os
from setuptools import setup, find_packages

# Read requirements from the requirements.txt file
with open(os.path.join(os.path.dirname(__file__), "requirements.txt")) as f:
    requirements = f.read().splitlines()

# Read the contents of README.md
with open(os.path.join(os.path.dirname(__file__), "readme.md"), "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="locohost-cli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "locohost=locohost_cli.locohost:main",
        ],
    },
    author="Stefan Fox",
    author_email="stefan.fox@example.com",
    description="AI-assisted project management and development tool for Kubernetes-based applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stefanfox/locohost-cli",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
