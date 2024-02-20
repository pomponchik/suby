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
- [**Working with exceptions**](#working-with-exceptions)
- [**Output and logging**](#output-and-logging)


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

- **id** - a unique string that allows you to distinguish one result of calling the same command from another.
- **stdout** - a string containing the entire buffered output of the command being run.
- **stderr** - a string containing the entire buffered stderr of the command being run.
- **returncode** - an integer indicating the return code of the subprocess. `0` means that the process was completed successfully, the other options usually indicate something bad.
- **killed_by_token** - a boolean flag indicating whether the subprocess was killed due to [token](https://cantok.readthedocs.io/en/latest/the_pattern/) cancellation.

The simplest example of what it might look like:

```python
import suby

result = suby('python', '-c', 'print("hello, world!")')
print(result)
# > SubprocessResult(id='e9f2d29acb4011ee8957320319d7541c', stdout='hello, world!\n', stderr='', returncode=0, killed_by_token=False)
```


## Working with exceptions

By default, `suby` raises exceptions in three cases:

1. If the command you are calling ended with a return code not equal to `0`. In this case, you will see an exception `suby.errors.RunningCommandError`:

```python
import suby
from suby.errors import RunningCommandError

try:
    suby('python', '-c', '1/0')
except RunningCommandError as e:
    print(e)
    # > Error when executing the command "python -c 1/0".
```

2. If you passed a [cancellation token](https://cantok.readthedocs.io/en/latest/the_pattern/) when calling the command, and the token was canceled, an exception will be raised [corresponding to the type](https://cantok.readthedocs.io/en/latest/what_are_tokens/exceptions/) of canceled token. This part of the functionality is integrated with the [cantok](https://cantok.readthedocs.io/en/latest/) library, so we recommend that you familiarize yourself with it beforehand. Here is a small example of how to pass cancellation tokens and catch exceptions from them:

```python
from random import randint
from cantok import ConditionToken

token = ConditionToken(lambda: randint(1, 1000) == 7)
suby('python', '-c', 'import time; time.sleep(10_000)', token=token)
```

3. You have set a timeout (in seconds) for the operation and it has expired. To count the timeout "under the hood", suby uses [`TimeoutToken`](https://cantok.readthedocs.io/en/latest/types_of_tokens/TimeoutToken/). Therefore, when the timeout expires, `cantok.errors.TimeoutCancellationError` will be raised:

```python
from cantok import TimeoutCancellationError

try:
    suby('python', '-c', 'import time; time.sleep(10_000)', timeout=1)
except TimeoutCancellationError as e:
    print(e)
    # > The timeout of 1 seconds has expired.
```

You can prevent `suby` from raising any exceptions. To do this, set the `catch_exceptions` parameter to `True`:

```python
result = suby('python', '-c', 'import time; time.sleep(10_000)', timeout=1, catch_exceptions=True)
print(result)
# > SubprocessResult(id='c9125b90d03111ee9660320319d7541c', stdout='', stderr='', returncode=-9, killed_by_token=True)
```

Keep in mind that the full result of the subprocess call can also be found through the `result` attribute of any raised exception:

```python
try:
    suby('python', '-c', 'import time; time.sleep(10_000)', timeout=1)
except TimeoutCancellationError as e:
    print(e.result)
    # > SubprocessResult(id='a80dc26cd03211eea347320319d7541c', stdout='', stderr='', returncode=-9, killed_by_token=True)
```


## Output and logging
