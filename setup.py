from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="notion_gametracker",
    version="0.2.beta",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=required,
    entry_points={
        "console_scripts": [
            "notion_gametracker=notion_gametracker.notion_gametracker:main",
        ]
    }
)