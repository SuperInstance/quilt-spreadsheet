"""quilt-spreadsheet — the Quilt IDE as spreadsheet substrate."""
from setuptools import setup, find_packages

setup(
    name="quilt-spreadsheet",
    version="0.1.0",
    description="The Quilt IDE as spreadsheet substrate — cells are programs with hooks, double-entry bookkeeping, per-cell color namespaces, backend porting, distributed clocks.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Casey / SuperInstance",
    packages=find_packages(exclude=["tests", "demos"]),
    python_requires=">=3.8",
    install_requires=[],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
