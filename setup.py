from setuptools import setup

setup(
    name="passgen",
    version="1.0",
    description="A rules-based tool for generating passwords and wordlists",
    author="@devsaeedz",
    author_email="", 
    url="https://github.com/devsaeedz/passgen",
    py_modules=["passgen"],
    entry_points={
        "console_scripts": [
            "passgen=passgen:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 