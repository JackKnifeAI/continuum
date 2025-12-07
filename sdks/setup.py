"""
Setup for CONTINUUM SDK Generator
"""

from setuptools import setup, find_packages

setup(
    name="continuum-sdk-generator",
    version="0.3.0",
    description="SDK generator for CONTINUUM API",
    author="CONTINUUM",
    author_email="support@continuum.ai",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
        "jinja2>=3.1.0",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "pytest>=7.0.0",
            "mypy>=1.0.0",
        ],
        "formatters": [
            "black>=23.0.0",  # Python
            # Other formatters are external tools
        ],
    },
    entry_points={
        "console_scripts": [
            "continuum-sdk=generator.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
