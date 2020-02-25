#!/usr/bin/env python3

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="k8s-backup-restore",
    version="0.0.1",
    author="AWS/WW",
    description="CLI utility to perform k8s backup and restore",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/paulcarlton-ww/k8s-backup-restore",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['boto3',
                      'kubernetes',
                      'click',
                      'k8sdrutils @ git+https://github.com/paulcarlton-ww/k8s-dr-utils@0.0.10#egg=k8sdrutils'
                      ],
    extras_require={
        'dev': ['pylint'],
    },
    packages=setuptools.find_packages()
)
