import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nocopy",
    version="0.1.0",
    author="72nd",
    author_email="msg@frg72.com",
    description="Very simple REST-API for the NocoDB service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/72nd/nocopy",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    packages=["nocopy"],
    install_requires=[
        "requests==2.27.0",
        "pydantic==1.8.2",
    ]
)
