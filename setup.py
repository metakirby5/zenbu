import codecs

from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs.open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='zenbu',
    version='1.0.2',
    description='Jinja2 + YAML based config templater.',
    long_description=long_description,
    url='https://github.com/metakirby5/zenbu',
    author='Ethan Chan',
    author_email='metakirby5@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    keywords='zenbu config templater jinja2 yaml',
    py_modules=['zenbu'],
    install_requires=[
        'argcomplete',
        'colorlog',
        'Jinja2',
        'PyYAML',
        'termcolor',
        'watchdog',
    ],
    entry_points={
        'console_scripts': [
            'zenbu=zenbu:main',
        ],
    },
)

