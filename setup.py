import setuptools

with open("README", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PastebinDecoder",
    version="1.0.1",
    author="Aaron Gee-Clough",
    author_email="aaron@g-clef.net",
    description="Helper class to decode data in Pastebin Pastes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/g-clef/PastebinDecoder",
    project_urls={
            "Bug Tracker": "https://github.com/g-clef/PastebinDecoder/issues",
        },
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=["python-magic>=0.4.18",]
)
