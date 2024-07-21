from setuptools import setup, find_packages

setup(
    name="locohost-cli",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "anthropic",
        "pydantic",
        "instructor",
    ],
    entry_points={
        "console_scripts": [
            "locohost=locohost_cli.locohost:main",
        ],
    },
)
