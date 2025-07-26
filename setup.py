from setuptools import setup, find_packages

setup(
    name="programming-bot",
    version="1.0.0",
    description="Ein intelligenter Programmier-Assistent mit Gedächtnis",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "anthropic",
        "tiktoken",
        "fastapi",
        "uvicorn",
        "websockets",
        "jinja2",
        "python-multipart",
        "gitpython",
        "chromadb",
        "sentence-transformers",
        "pydantic",
        "networkx",
        "pyvis",
        "matplotlib",
        "seaborn",
        "pandas",
        "python-dotenv",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "programming-bot=main:main",
        ],
    },
)