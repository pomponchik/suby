import sys
from time import perf_counter

import pytest
from cantok import TimeoutCancellationError

import suby


def test_normal_way():
    result = suby(sys.executable, '-c', 'print("kek")')

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
        result = suby(sys.executable, '-c', f'import time; time.sleep({sleep_time})', timeout=timeout)
    except TimeoutCancellationError as e:
        assert e.result.stdout == ''
        assert e.result.stderr == ''
        assert e.result.returncode != 0
    end_time = perf_counter()

    assert (end_time - start_time) < sleep_time
    assert (end_time - start_time) >= timeout
