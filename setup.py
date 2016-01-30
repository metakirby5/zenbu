from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='whizkers',
    version='1.1.0',
    description='Mustache + YAML based config templater.',
    long_description=long_description,
    url='https://github.com/metakirby5/whizkers',
    author='Ethan Chan',
    author_email='metakirby5@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    keywords='whizkers config templater mustache yaml',
    py_modules=['whizkers'],
    install_requires=[
        'argcomplete',
        'colorlog',
        'pystache',
        'PyYAML',
        'termcolor',
        'watchdog',
    ],
    entry_points={
        'console_scripts': [
            'whizkers=whizkers:main',
        ],
    },
)

