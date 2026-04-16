from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).parent


setup(
    name="autodev",
    version="0.1.0",
    description="Automated development workflow orchestrator (plan-dev-review-arbitration loop)",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    packages=find_packages(include=["autodev", "autodev.*"]),
    include_package_data=True,
    install_requires=[
        "click>=8.1.0",
        "loguru>=0.7.0",
    ],
    entry_points={
        "console_scripts": [
            "autodev=autodev.cli:main",
        ]
    },
)
