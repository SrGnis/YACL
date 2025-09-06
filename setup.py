#!/usr/bin/env python3
"""
Setup script for YACL
A cross-platform launcher for Cataclysm
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "A cross-platform launcher for Cataclysm"

# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

setup(
    name="yacl",
    version="0.1.0",
    description="A cross-platform launcher for Cataclysm",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="SrGnis",
    author_email="srgnis@srgnis.xyz",
    url="https://github.com/SrGnis/yacl",
    license="MIT",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    python_requires=">=3.11",
    install_requires=read_requirements(),
    
    entry_points={
        "console_scripts": [
            "yacl=yacl.main:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
        "Topic :: System :: Software Distribution",
    ],
    
    keywords="cataclysm launcher game manager content",
    
    include_package_data=True,
    package_data={
        "yacl": [
            "resources/**/*",
        ],
    },
    
    extras_require={
        "dev": [
            "pytest==8.4.1",
        ],
    },
)
