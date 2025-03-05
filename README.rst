Clyde Package Manager
====================

Clyde is a modern package manager for C and C++ projects, designed to make dependency management and project setup simple and efficient.

Features
--------

- Simple project initialization with templates
- Support for both C and C++ projects
- GitHub-based package registry
- Binary package support
- Easy-to-use command line interface

Installation
------------

.. code-block:: bash

    pip install clydepm

Quick Start
----------

Create a New Project
~~~~~~~~~~~~~~~~~~~

Create a C application:

.. code-block:: bash

    clyde init my-app --type application
    cd my-app
    clyde build
    clyde run

Create a C++ library:

.. code-block:: bash

    clyde init my-lib --type library --lang cpp
    cd my-lib
    clyde build

Create a C library:

.. code-block:: bash

    clyde init my-lib --type library --lang c
    cd my-lib
    clyde build

Project Types
~~~~~~~~~~~~

Clyde supports two types of projects:

- **Applications**: Executable programs (default: C)
- **Libraries**: Reusable code packages (default: C++)

Language Selection
~~~~~~~~~~~~~~~~~

Use the ``--lang`` flag to specify the programming language:

- ``--lang c``: C (C11)
- ``--lang cpp`` (or ``cxx``, ``c++``): C++ (C++17)

Project Structure
~~~~~~~~~~~~~~~

.. code-block:: text

    my-project/
    ├── config.yaml        # Project configuration
    ├── src/              # Source files
    │   └── main.c/cpp    # Main source file
    ├── include/          # Public headers
    │   └── my-project/   # Project-specific headers
    ├── private_include/  # Private headers
    └── deps/            # Dependencies

Configuration (config.yaml)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    name: my-project
    version: 0.1.0
    type: application  # or library
    cflags:
      gcc: -std=c11    # or -std=c++17
    requires: {}       # Dependencies

Dependencies
-----------

Clyde supports both local and remote package dependencies. Dependencies are specified in the ``requires`` section of ``config.yaml``:

.. code-block:: yaml

    requires:
      my-lib: "local:../my-lib"        # Local package
      remote-lib: "^1.2.0"             # Remote package with semver
      specific-lib: "=1.0.0"           # Exact version
      git-lib: "git:main"              # Specific git branch/tag/commit

Local Dependencies
~~~~~~~~~~~~~~~~

Local dependencies are built in their original location and linked directly. The path can be relative to the current package or absolute. For example:

.. code-block:: yaml

    requires:
      my-lib: "local:../my-lib"        # Relative path
      other-lib: "local:/path/to/lib"  # Absolute path

Future versions will support version constraints for local packages using Git tags.

Remote Dependencies
~~~~~~~~~~~~~~~~~

Remote packages are downloaded to the ``deps/`` directory and built there. They support:

- Semantic versioning (e.g., "^1.2.0", "~1.2.0", "=1.0.0")
- Git references (branches, tags, or commit hashes)
- GitHub packages (automatically resolved)

Include Paths
~~~~~~~~~~~~

Each package must organize its headers as follows:

.. code-block:: text

    my-package/
    ├── include/              # Public headers (exposed to dependents)
    │   └── my-package/      # Package namespace directory
    │       ├── api.h
    │       └── types.h
    ├── private_include/     # Private headers (not exposed)
    └── src/                # Implementation files

Public headers are included using the package name as namespace:

.. code-block:: c

    #include <my-package/api.h>

This structure ensures:

- No header name conflicts between packages
- Clear separation of public/private interfaces
- No need to copy headers between packages

Linking
~~~~~~~

Libraries are automatically linked based on dependencies:

- Library names are derived from package names (e.g., ``my-lib`` becomes ``-lmy-lib``)
- Dependencies are built in correct order
- Link paths are automatically configured

Note: Support for circular dependencies and diamond dependency resolution is planned for future versions.

Commands
--------

Initialize a Project
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    clyde init [path] [options]
      --name, -n TEXT          Package name (defaults to directory name)
      --type, -t [application|library]
      --lang, -l [c|cpp|cxx|c++]
      --version, -v TEXT       Initial version

Build a Project
~~~~~~~~~~~~~

.. code-block:: bash

    clyde build [path] [options]
      --trait, -t KEY=VALUE   Build traits

Run an Application
~~~~~~~~~~~~~~~~

.. code-block:: bash

    clyde run [path] [args]

Publish a Package
~~~~~~~~~~~~~~~

.. code-block:: bash

    clyde publish [path] [options]
      --binary/--no-binary    Create and publish binary package

Install a Package
~~~~~~~~~~~~~~~

.. code-block:: bash

    clyde install package-name[==version]
      --path, -p PATH         Installation path

GitHub Integration
------------------ 

To use GitHub features (publish/install), set your GitHub token:

.. code-block:: bash

    export GITHUB_TOKEN=your-token

Contributing
------------

Contributions are welcome! Please feel free to submit a Pull Request.

License
-------

[License details here]