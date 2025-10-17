"""
Setup configuration for HL-Delta trading bot
"""

from setuptools import setup, find_packages
import os

# Read version from VERSION file
version = "2.0.0"
if os.path.exists("VERSION"):
    with open("VERSION", "r") as f:
        version = f.read().strip()

# Read long description from README
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()

# Read requirements
requirements = []
if os.path.exists("requirements.txt"):
    with open("requirements.txt", "r") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="hl-delta",
    version=version,
    author="HyperVault Team",
    author_email="admin@draxdev.xyz",
    description="Automated delta-neutral trading bot for Hyperliquid exchange",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cgaspart/HL-Delta",
    project_urls={
        "Bug Tracker": "https://github.com/cgaspart/HL-Delta/issues",
        "Documentation": "https://github.com/cgaspart/HL-Delta#readme",
        "Source Code": "https://github.com/cgaspart/HL-Delta",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hl-delta=delta_bot.bot:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
