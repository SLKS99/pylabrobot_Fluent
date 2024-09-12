from setuptools import setup, find_packages

# You might want to create a __version__.py file in your package
from pylabrobot_fluent.__version__ import __version__

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# Define your package's dependencies
install_requires = [
    "pylabrobot",
    "sila2==2.0.5",  # Adjust the version as needed
    "typing_extensions"
]

# Define extra dependencies
extras_sila2 = [
    # Add any extra SiLA2-specific dependencies here
]

extras_dev = extras_sila2 + [
    "pytest",
    "pytest-timeout",
    "pylint",
    "mypy"
]

setup(
    name="pylabrobot_fluent",
    version=__version__,
    packages=find_packages(exclude=["tests", "docs"]),
    description="A PyLabRobot backend for Tecan Fluent using SiLA2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    url="https://github.com/SLKS99/pylabrobot_Fluent",
    package_data={"pylabrobot_fluent": ["sila2_connector/*"]},  # Include SiLA2 connector files if needed
    extras_require={
        "sila2": extras_sila2,
        "dev": extras_dev,
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
)