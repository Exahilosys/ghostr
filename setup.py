import setuptools
import os

with open('README.rst') as file:
    readme = file.read()

name = 'ghostr'

version = '0.1.0'

author = 'Exahilosys'

url = f'https://github.com/{author}/{name}'

setuptools.setup(
    name = name,
    version = version,
    url = url,
    packages = setuptools.find_packages(),
    license = 'MIT',
    description = 'Strings that ignore part of themselves.',
    long_description = readme,
    extras_require = {
        'docs': [
            'sphinx',
            'sphinx_rtd_theme'
        ]
    }
)
