import os
import pathlib
from setuptools import setup


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


def requirements():
    with open(str(pathlib.PurePath(__file__).parent / "requirements.txt"), "r") as req_file:
        out = []
        for line in req_file.readlines():
            out.append(line.replace("\n", ""))
        return out


setup(
    name="sql_extract",
    version="0.3.2",
    python_requires=">=3.6.7",
    packages=[
        "sql_extract",
    ],
    scripts=["bin/sql-extract", "bin/csv2xlsx"],
    url="https://github.com/rowanuniversity/sql-extract",
    license="MIT",
    author="John Reiser, Connor Hornibrook",
    author_email="reiser@rowan.edu, hornibrookc@rowan.edu",
    install_requires=requirements(),
    description="",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
)
