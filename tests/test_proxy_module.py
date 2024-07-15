import re
import sys
from time import perf_counter
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import pytest
import full_match
from cantok import TimeoutCancellationError, ConditionCancellationError, ConditionToken, SimpleToken
from emptylog import MemoryLogger

import suby
from suby import RunningCommandError


def test_normal_way():
    result = suby(sys.executable, '-c', 'print("kek")')

    assert result.stdout == 'kek\n'
    assert result.stderr == ''
    assert result.returncode == 0


def test_normal_way_with_simple_token():
    result = suby(sys.executable, '-c', 'print("kek")', token=SimpleToken())

    assert result.stdout == 'kek\n'
    assert result.stderr == ''
    assert result.returncode == 0


def test_stderr_catching():
    result = suby(sys.executable, '-c', 'import sys; sys.stderr.write("kek")')

    assert result.stdout == ''
    assert result.stderr == 'kek'
    assert result.returncode == 0


def test_catch_exception():
    result = suby(sys.executable, '-c', 'raise ValueError', catch_exceptions=True)

    assert 'ValueError' in result.stderr
    assert result.returncode != 0


def test_timeout():
    sleep_time = 100000
    timeout = 0.001

    start_time = perf_counter()
    result = suby(sys.executable, '-c', f'import time; time.sleep({sleep_time})', timeout=timeout, catch_exceptions=True)
    end_time = perf_counter()

    assert result.returncode != 0
    assert result.stdout == ''
    assert result.stderr == ''

    assert (end_time - start_time) < sleep_time
    assert (end_time - start_time) >= timeout


def test_timeout_without_catching_exception():
    sleep_time = 100000
    timeout = 0.001

    with pytest.raises(TimeoutCancellationError):
        suby(sys.executable, '-c', f'import time; time.sleep({sleep_time})', timeout=timeout)

    start_time = perf_counter()
    try:
        suby(sys.executable, '-c', f'import time; time.sleep({sleep_time})', timeout=timeout)
    except TimeoutCancellationError as e:
        assert e.result.stdout == ''
        assert e.result.stderr == ''
        assert e.result.returncode != 0
    end_time = perf_counter()

    assert (end_time - start_time) < sleep_time
    assert (end_time - start_time) >= timeout


def test_exception_in_subprocess_without_catching():
    with pytest.raises(RunningCommandError, match=re.escape(f'Error when executing the command "{sys.executable} -c "raise ValueError"".')):
        suby(sys.executable, '-c', 'raise ValueError')

    try:
        suby(sys.executable, '-c', 'raise ValueError')
    except RunningCommandError as e:
        assert e.result.stdout == ''
        assert 'ValueError' in e.result.stderr
        assert e.result.returncode != 0


def test_not_catching_output():
    stderr_buffer = StringIO()
    stdout_buffer = StringIO()

    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        result = suby(sys.executable, '-c', 'print("kek1", end=""); import sys; sys.stderr.write("kek2")', catch_output=False)

        stderr = stderr_buffer.getvalue()
        stdout = stdout_buffer.getvalue()

        assert result.returncode == 0
        assert stderr == 'kek2'
        assert stdout == 'kek1'


def test_catching_output():
    stderr_buffer = StringIO()
    stdout_buffer = StringIO()

    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        result = suby(sys.executable, '-c', 'print("kek1", end=""); import sys; sys.stderr.write("kek2")', catch_output=True)

        assert result.returncode == 0
        assert stderr_buffer.getvalue() == ''
        assert stdout_buffer.getvalue() == ''


def test_logging_normal_way():
    logger = MemoryLogger()

    suby(sys.executable, '-c', 'print("kek", end="")', logger=logger, catch_output=True)

    assert len(logger.data.info) == 2
    assert len(logger.data.error) == 0

    assert logger.data.info[0].message == f'The beginning of the execution of the command "{sys.executable} -c "print("kek", end="")"".'
    assert logger.data.info[1].message == f'The command "{sys.executable} -c "print("kek", end="")"" has been successfully executed.'


def test_logging_with_expired_timeout():
    logger = MemoryLogger()

    suby(sys.executable, '-c', f'import time; time.sleep({500_000})', logger=logger, catch_exceptions=True, catch_output=True, timeout=0.0001)

    assert len(logger.data.info) == 1
    assert len(logger.data.error) == 1

    assert logger.data.info[0].message == f'The beginning of the execution of the command "{sys.executable} -c "import time; time.sleep(500000)"".'
    assert logger.data.error[0].message == f'The execution of the "{sys.executable} -c "import time; time.sleep(500000)"" command was canceled using a cancellation token.'


def test_logging_with_exception():
    logger = MemoryLogger()

    suby(sys.executable, '-c', '1/0', logger=logger, catch_exceptions=True, catch_output=True)

    assert len(logger.data.info) == 1
    assert len(logger.data.error) == 1

    assert logger.data.info[0].message == f'The beginning of the execution of the command "{sys.executable} -c 1/0".'
    assert logger.data.error[0].message == f'Error when executing the command "{sys.executable} -c 1/0".'


def test_logging_with_expired_timeout_without_catching_exceptions():
    logger = MemoryLogger()

    with pytest.raises(TimeoutCancellationError):
        suby(sys.executable, '-c', f'import time; time.sleep({500_000})', logger=logger, catch_output=True, timeout=0.0001)

    assert len(logger.data.info) == 1
    assert len(logger.data.error) == 1

    assert logger.data.info[0].message == f'The beginning of the execution of the command "{sys.executable} -c "import time; time.sleep(500000)"".'
    assert logger.data.error[0].message == f'The execution of the "{sys.executable} -c "import time; time.sleep(500000)"" command was canceled using a cancellation token.'


def test_logging_with_exception_without_catching_exceptions():
    logger = MemoryLogger()

    with pytest.raises(RunningCommandError):
        suby(sys.executable, '-c', '1/0', logger=logger, catch_output=True)

    assert len(logger.data.info) == 1
    assert len(logger.data.error) == 1

    assert logger.data.info[0].message == f'The beginning of the execution of the command "{sys.executable} -c 1/0".'
    assert logger.data.error[0].message == f'Error when executing the command "{sys.executable} -c 1/0".'


def test_only_token():
    sleep_time = 100000
    timeout = 0.1

    start_time = perf_counter()
    token = ConditionToken(lambda: perf_counter() - start_time > timeout)

    result = suby(sys.executable, '-c', f'import time; time.sleep({sleep_time})', catch_exceptions=True, token=token)

    end_time = perf_counter()

    assert result.returncode != 0
    assert result.stdout == ''
    assert result.stderr == ''
    assert result.killed_by_token == True

    assert end_time - start_time >= timeout
    assert end_time - start_time < sleep_time


def test_only_token_without_catching():
    sleep_time = 100000
    timeout = 0.1

    start_time = perf_counter()
    token = ConditionToken(lambda: perf_counter() - start_time > timeout)

    try:
        result = suby(sys.executable, '-c', f'import time; time.sleep({sleep_time})', token=token)
    except ConditionCancellationError as e:
        assert e.token is token
        result = e.result

    end_time = perf_counter()

    assert result.returncode != 0
    assert result.stdout == ''
    assert result.stderr == ''
    assert result.killed_by_token == True

    assert end_time - start_time >= timeout
    assert end_time - start_time < sleep_time


def test_token_plus_timeout_but_timeout_is_more_without_catching():
    sleep_time = 100000
    timeout = 0.1

    start_time = perf_counter()
    token = ConditionToken(lambda: perf_counter() - start_time > timeout)

    try:
        result = suby(sys.executable, '-c', f'import time; time.sleep({sleep_time})', token=token, timeout=3)
    except ConditionCancellationError as e:
        assert e.token is token
        result = e.result

    end_time = perf_counter()

    assert result.returncode != 0
    assert result.stdout == ''
    assert result.stderr == ''
    assert result.killed_by_token == True

    assert end_time - start_time >= timeout
    assert end_time - start_time < sleep_time


def test_token_plus_timeout_but_timeout_is_less_without_catching():
    sleep_time = 100000
    timeout = 0.1

    start_time = perf_counter()
    token = ConditionToken(lambda: perf_counter() - start_time > timeout)

    try:
        result = suby(sys.executable, '-c', f'import time; time.sleep({sleep_time})', token=token, timeout=timeout/2)
    except TimeoutCancellationError as e:
        assert e.token is not token
        result = e.result

    end_time = perf_counter()

    assert result.returncode != 0
    assert result.stdout == ''
    assert result.stderr == ''
    assert result.killed_by_token == True

    assert end_time - start_time >= timeout/2
    assert end_time - start_time < sleep_time


def test_replace_stdout_callback():
    accumulator = []

    stderr_buffer = StringIO()
    stdout_buffer = StringIO()

    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        result = suby(sys.executable, '-c', 'print("kek")', stdout_callback=lambda x: accumulator.append(x))

    assert accumulator == ['kek\n']

    assert result.returncode == 0
    assert result.stdout == 'kek\n'
    assert result.stderr == ''

    assert stderr_buffer.getvalue() == ''
    assert stdout_buffer.getvalue() == ''


def test_replace_stderr_callback():
    accumulator = []

    stderr_buffer = StringIO()
    stdout_buffer = StringIO()

    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        result = suby(sys.executable, '-c', 'import sys; sys.stderr.write("kek")', stderr_callback=lambda x: accumulator.append(x))

    assert accumulator == ['kek']

    assert result.returncode == 0
    assert result.stdout == ''
    assert result.stderr == 'kek'

    assert stderr_buffer.getvalue() == ''
    assert stdout_buffer.getvalue() == ''


@pytest.mark.parametrize(
    ['arguments', 'exception_message'],
    (
        ([None], 'Only strings and pathlib.Path objects can be positional arguments when calling the suby function. You passed "None" (NoneType).'),
        ([1], 'Only strings and pathlib.Path objects can be positional arguments when calling the suby function. You passed "1" (int).'),
        (['python', 1], 'Only strings and pathlib.Path objects can be positional arguments when calling the suby function. You passed "1" (int).'),
    ),
)
def test_pass_wrong_positional_argument(arguments, exception_message):
    with pytest.raises(TypeError, match=full_match(exception_message)):
        suby(*arguments)


def test_use_path_object_as_first_positional_argument():
    result = suby(Path(sys.executable), '-c', 'print("kek")')

    assert result.stdout == 'kek\n'
    assert result.stderr == ''
    assert result.returncode == 0
