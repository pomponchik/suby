import sys
import suby


def test_normal_way():
    result = suby(sys.executable, '-c', 'print("kek")')

    assert result.stdout == 'kek\n'
    assert result.stderr == ''
    assert result.returncode == 0
