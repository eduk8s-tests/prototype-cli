import sys
import os

from setuptools import setup

long_description = open("README.rst").read()

classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
]

setup_kwargs = dict(
    name="eduk8s-cli",
    version="0.1.0",
    description="Command line client for eduk8s.",
    long_description=long_description,
    url="https://github.com/eduk8s/eduk8s-cli",
    author="Graham Dumpleton",
    author_email="Graham.Dumpleton@gmail.com",
    license="Apache License, Version 2.0",
    python_requires=">=3.7.0",
    classifiers=classifiers,
    keywords="eduk8s kubernetes",
    packages=["eduk8s", "eduk8s.cli", "eduk8s.kube",],
    package_dir={"eduk8s": "src/eduk8s"},
    package_data={"eduks.crds": ["session.yaml", "workshop.yaml"],},
    entry_points={
        "console_scripts": ["eduk8s = eduk8s.cli:main"],
        "eduk8s_cli_plugins": [
            "workshop = eduk8s.cli.workshop",
            "session = eduk8s.cli.session",
            "install = eduk8s.cli.install",
        ],
    },
    install_requires=[
        "click",
        "requests",
        "rstr",
        "PyYaml",
        "kopf==0.23.2",
        "openshift==0.10.1",
    ],
)

setup(**setup_kwargs)
