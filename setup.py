#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = []

setup_requirements = ["pytest-runner", "credstash", "everett", "josepy", "flask_pyoidc"]

test_requirements = ["pytest", "pytest-watch", "pytest-cov", "faker"]

setup(
    name="dashboard",
    version="0.0.1",
    author="Andrew Krug",
    author_email="akrug@mozilla.com",
    description="A single signon dashboard for mozilla-iam.",
    long_description=long_description,
    url="https://github.com/mozilla-iam/sso-dashboard",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Mozilla Public License",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
    license="Mozilla Public License 2.0",
    include_package_data=True,
    packages=find_packages(),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    zip_safe=False,
)
