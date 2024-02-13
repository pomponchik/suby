from suby.errors import RunningCommandError
from suby.subprocess_result import SubprocessResult


def test_init_exception_and_raise():
    try:
        raise RunningCommandError('kek', SubprocessResult())
    except RunningCommandError as e:
        assert str(e) == 'kek'
        assert isinstance(e.result, SubprocessResult)
