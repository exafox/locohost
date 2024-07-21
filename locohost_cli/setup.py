import os
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

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
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-assisted project management and development tool for Kubernetes-based applications",
    long_description=open("README.md").read() if os.path.exists("README.md") else "AI-assisted project management and development tool for Kubernetes-based applications",
    long_description_content_type="text/markdown" if os.path.exists("README.md") else "text/plain",
    url="https://github.com/yourusername/locohost-cli",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
