from setuptools import setup, find_packages

setup(
    name="gpt-localize-ios",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "openai==1.72.0",
        "tqdm==4.66.1",
        "termcolor==2.4.0",
        "tiktoken==0.5.2",
        "argparse",
        "python-dotenv==1.1.0"
    ],
    entry_points={
        "console_scripts": [
            "gpt-localize-ios=gpt_localize_ios.cli:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to automatically translate iOS .xcstrings files using GPT-4",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/GPT-Localize-iOS",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Localization",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
) 