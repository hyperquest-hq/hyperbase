# Installation

hyperbase requires Python >=3.10.

## Install with pip

```
$ pip install hyperbase
```

It is advisable to work with virtual environments. This avoids conflicts with the system-wide installed packages and creates a nice self-contained environment for you to work on. It is particularly important with hyperbase because we maintain dependencies to specific versions of downstream machine learning tools, as to keep results consistent.

To create a virtual environment in the current directory you can do this:

```
$ virtualenv -p <path to python3> venv
```

Common locations for python3:

* /usr/local/bin/python3
* /usr/bin/python3

If you are on macOS, do this instead (for the reason [explained here](http://matplotlib.org/faq/osx_framework.html#osxframework-faq)):

```
$ python3 -m venv venv
```

Then to switch to the virtual environment and install hyperbase:

```
$ source venv/bin/activate
$ pip install hyperbase
```

### Choose language model

It is still necessary to download a spaCy language model. hyperbase supports both the transformer model (modern, GPU optimized) and a CPU optimized model. The transformer model can be installed in the following way:

```
$ python -m spacy download en_core_web_trf
```

Or, to install the CPU optimized model (a faster option if your computer does not have a GPU):

```
$ python -m spacy download en_core_web_lg
```

In case both models are present, hyperbase will use the transformer model. A spaCy language model can be uninstalled as a regular pip package, for example:

```
$ pip uninstall en_core_web_trf
```

## Install from the code repository (GitHub)

Another way to install hyperbase is to build it from the GitHub repository source. You should use this method if you wish to make changes to the code base.

Start by cloning the source code to your current local directory.

```
$ git clone https://github.com/hyperbase/hyperbase.git
$ cd hyperbase
```

It is advisable to work with virtual environments, for reasons that are explained in the previous section. Please refer to it for details.

Now you can build and install hyperbase:

```
$ pip install .
```

If you are working on hyperbase development or wish to modify the code for your own purposes, it is advisable to install the project in editable mode, using the `-e` flag:

```
$ pip install -e .
```

This way, hyperbase will be added to your environment by linking to the local project directory, which means that any change in the code will reflect directly in the environment. Another important consequence of this is that you will be able to import hyperbase from the project directory and run development tools such as `pytest`, otherwise there could be conflicts caused by the `hyperbase` package in the current path not containing the compiled cython modules.

It is then necessary to download a spaCy language model, as detailed above.

### For developers

If you want to help develop hyperbase, you should also install the development dependencies:

```
$ pip install '.[dev]'
```

### Run tests

From the project's root directory:

```
$ pytest
```

## Prerequisites

Naturally, you can ignore the prerequisites that are already installed in your machine.

### Linux

Linux distributions are diverse in terms of package managers. Please use the appropriate package manager for your distribution to install the prerequisites.

* gcc
* Python 3
* pip (Python package manager)
* virtualenv (Virtual Python Environment builder)

### macOS

* XCode and the "Command Line Tools":

```
$ xcode-select --install
```

* The [Homebrew package manager](http://brew.sh/).

* Python 3

If python 3 is not already included with your current version of macOS:

```
$ brew install python3
```

* pip (Python package manager):

```
$ sudo easy_install pip
```

* virtualenv (Virtual Python Environment builder):

```
$ sudo -H pip install virtualenv
```
