#!/usr/bin/env python

from setuptools import setup

setup(
    name='capsat_watcher',
    packages=['capsat_watcher'],
    author="Jatin Mathur, Logan Power, Evan Widloski",
    author_email="evan@evanw.org",
    description="capsat watcher and uploader",
    long_description=open('README.md').read(),
    long_description_content_type='text/x-rst',
    license="GPLv3",
    url="https://gitlab.engr.illinois.edu/cubesat/ground-station/moc-website",
    entry_points={
        'console_scripts': ['capsat_watcher = capsat_watcher.capsat_watcher:main']
    },
    install_requires=[
        "requests==2.26.0",
        "watchdog==2.1.5"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
    ]
)
