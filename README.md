# suby

[![Downloads](https://static.pepy.tech/badge/suby/month)](https://pepy.tech/project/suby)
[![Downloads](https://static.pepy.tech/badge/suby)](https://pepy.tech/project/suby)
[![codecov](https://codecov.io/gh/pomponchik/suby/graph/badge.svg?token=IyYI7IaSet)](https://codecov.io/gh/pomponchik/suby)
[![Lines of code](https://sloc.xyz/github/pomponchik/suby/?category=code)](https://github.com/boyter/scc/)
[![Hits-of-Code](https://hitsofcode.com/github/pomponchik/suby?branch=main)](https://hitsofcode.com/github/pomponchik/suby/view?branch=main)
[![Test-Package](https://github.com/pomponchik/suby/actions/workflows/tests_and_coverage.yml/badge.svg)](https://github.com/pomponchik/suby/actions/workflows/tests_and_coverage.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/suby.svg)](https://pypi.python.org/pypi/suby)
[![PyPI version](https://badge.fury.io/py/suby.svg)](https://badge.fury.io/py/suby)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)


Here is a small wrapper around the [subprocesses](https://docs.python.org/3/library/subprocess.html). You can find many similar wrappers, but this particular one differs from the others in the following parameters:

- Beautiful minimalistic call syntax.
- Ability to specify your callbacks to catch `stdout` and `stderr`.
- Support for [cancellation tokens](https://github.com/pomponchik/cantok).
- You can set timeouts for subprocesses.
- Logging of command execution.


## Table of contents

- [**Quick start**](#quick-start)
- [**Run subprocess and look at the result**](#run-subprocess-and-look-at-the-result)


## Quick start

Install it:

```bash
pip install suby
```

And use:

```python
import suby

suby('python', '-c', 'print("hello, world!")')
# > hello, world!
```


## Run subprocess and look at the result

The `suby` function returns an object of the `SubprocessResult` class. It contains the following required fields:

- `**id**` - a unique string that allows you to distinguish one result of calling the same command from another.
- **stdout** - a string containing the entire buffered output of the command being run.
- **stderr** - a string containing the entire buffered stderr of the command being run.
- **returncode** - an integer indicating the return code of the subprocess.
- **killed_by_token** - a boolean flag indicating whether the subprocess was killed due to token cancellation.

The simplest example of what it might look like:

```python
import suby

result = suby('python', '-c', 'print("hello, world!")')
print(result)
# > SubprocessResult(id='e9f2d29acb4011ee8957320319d7541c', stdout='hello, world!\n', stderr='', returncode=0, killed_by_token=False)
```
