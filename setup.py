from setuptools import setup, find_packages

def readme():
    with open('README.rst') as f:
        return f.read()

options = {
    'name': 'clydepm',
    'description': 'Clyde C/C++ Package Manager',
    'long_description': readme(),
    'url': 'https://github.com/igutekunst/clydepm',
    'author': 'Isaac Gutekunst',
    'author_email': 'isaac@isac.cc',
    'license': 'MIT',
    'packages': find_packages(where='src'),
    'package_dir': {'': 'src'},
    'python_requires': '>=3.8',
    'install_requires': [
        'gitpython>=3.1.0',
        'pyyaml>=6.0.1',
        'colorama>=0.4.6',
        'termcolor>=2.4.0',
        'configparser>=6.0.0',
        'unidecode>=1.3.7',
        'graphviz>=0.20.1',
        'pygments>=2.17.2',
        'semantic_version>=2.10.0',
        'Jinja2>=3.1.0',
        'ninja>=1.11.1',
        'PyGithub>=2.1.1',
        'rich>=13.7.0',
        'typer>=0.9.0',
        'pydantic>=2.5.0',
    ],
    'extras_require': {
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'black>=23.12.0',
            'mypy>=1.8.0',
            'isort>=5.13.0',
        ],
    },
    'zip_safe': False,
    'package_data': {
        'clydepm': ['templates/*.*', 'py.typed'],
    },
    'version': '0.3.0',
    'test_suite': 'tests',
    'entry_points': {
        'console_scripts': [
            'clyde=clydepm.cli:main',
            'clyde2=clydepm.cli:main_v2',
        ]
    },
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Build Tools',
    ],
}

setup(**options)
