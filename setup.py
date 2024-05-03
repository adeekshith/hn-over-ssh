
### setup.py

```python
from setuptools import setup, find_packages

setup(
    name="hacker_news_over_ssh",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An SSH-based client to browse Hacker News interactively.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/hacker-news-over-ssh",
    packages=find_packages(),
    install_requires=[
        'paramiko>=2.7.2',
        'requests>=2.24.0',
        'datetime',
        'humanize'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

