"""
Setup script for AI Trip Planner
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text(encoding="utf-8").strip().split("\n")
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="ai-trip-planner",
    version="1.0.0",
    description="An intelligent trip planning system powered by multiple AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AI Trip Planner Team",
    author_email="team@aitripplanner.com",
    url="https://github.com/aitripplanner/ai-trip-planner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.12.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "pre-commit>=3.6.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],
        "monitoring": [
            "prometheus-client>=0.19.0",
            "sentry-sdk>=1.38.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "trip-planner=scripts.run_agent:main",
            "trip-monitor=scripts.monitor_trip:main",
            "trip-benchmark=scripts.benchmark_agents:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md"],
    },
    zip_safe=False,
    keywords="ai, trip-planning, agents, multi-agent, travel, planning",
    project_urls={
        "Bug Reports": "https://github.com/aitripplanner/ai-trip-planner/issues",
        "Source": "https://github.com/aitripplanner/ai-trip-planner",
        "Documentation": "https://aitripplanner.readthedocs.io/",
    },
)
