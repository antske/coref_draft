# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='coref_draft',
    version='0.1.0',
    description='Basic coreference resolution module, based on multi-seive',
    long_description=readme,
    author='Antske Fokkens',
    author_email='antske.fokkens@vu.nl',
    url='https://github.com/antske/coref_draft/',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

