import sys
from time import sleep
from threading import Thread
from subprocess import Popen, PIPE
from typing import List, Callable, Union, Optional, Any
from functools import partial

from emptylog import EmptyLogger, LoggerProtocol
from cantok import AbstractToken, SimpleToken, TimeoutToken, CancellationError

from suby.errors import RunningCommandError
from suby.subprocess_result import SubprocessResult


class ProxyModule(sys.modules[__name__].__class__):  # type: ignore[misc]
    def __call__(self, *arguments: str, catch_output: bool = False, logger: LoggerProtocol = EmptyLogger(), stdout_callback: Callable[[str], Any] = partial(print, end=''), stderr_callback: Callable[[str], Any] = sys.stderr.write, timeout: Optional[Union[int, float]] = None, token: Optional[AbstractToken] = None) -> SubprocessResult:
        """
        About reading from strout and stderr: https://stackoverflow.com/a/28319191/14522393
        """
        if timeout is not None and token is None:
            token = TimeoutToken(timeout)
        elif timeout is not None:
            token += TimeoutToken(timeout)  # type: ignore[operator]

        arguments_string_representation = ' '.join([argument if ' ' not in argument else f'"{argument}"' for argument in arguments])

        stdout_buffer: List[str] = []
        stderr_buffer: List[str] = []
        result = SubprocessResult()

        logger.info(f'The beginning of the execution of the command "{arguments_string_representation}".')

        with Popen(list(arguments), stdout=PIPE, stderr=PIPE, bufsize=1, universal_newlines=True) as process:
            stderr_reading_thread = self.run_stderr_thread(process, stderr_buffer, result, catch_output, stderr_callback)
            if token is not None:
                killing_thread = self.run_killing_thread(process, token, result)

            for line in process.stdout:  # type: ignore[union-attr]
                stdout_buffer.append(line)
                if not catch_output:
                    stdout_callback(line)

            stderr_reading_thread.join()
            if token is not None:
                killing_thread.join()

        self.fill_result(stdout_buffer, stderr_buffer, process.returncode, result)

        if process.returncode != 0:
            if result.killed_by_token:
                try:
                    token.check()  # type: ignore[union-attr]
                except CancellationError as e:
                    e.result = result  # type: ignore[attr-defined]
                    raise e
            else:
                message = f'Error when executing the command "{arguments_string_representation}".'
                logger.error(message)
                exception = RunningCommandError(message, result)
                raise exception

        else:
            logger.info(f'The command "{arguments_string_representation}" has been successfully executed.')

        return result

    def run_killing_thread(self, process: Popen, token: AbstractToken, result: SubprocessResult) -> Thread:  # type: ignore[type-arg]
        thread = Thread(target=self.killing_loop, args=(process, token, result))
        thread.start()
        return thread

    def run_stderr_thread(self, process: Popen, stderr_buffer: List[str], result: SubprocessResult, catch_output: bool, stderr_callback: Callable[[str], Any]) -> Thread:  # type: ignore[type-arg]
        thread = Thread(target=self.read_stderr, args=(process, stderr_buffer, result, catch_output, stderr_callback))
        thread.start()
        return thread

    @staticmethod
    def killing_loop(process: Popen, token: AbstractToken, result: SubprocessResult) -> None:  # type: ignore[type-arg]
        while True:
            if not token:
                process.kill()
                result.killed_by_token = True
                break
            if process.poll() is not None:
                break
            sleep(0.0001)

    @staticmethod
    def read_stderr(process: Popen, stderr_buffer: List[str], result: SubprocessResult, catch_output: bool, stderr_callback: Callable[[str], Any]) -> None:  # type: ignore[type-arg]
        for line in process.stderr:  # type: ignore[union-attr]
            stderr_buffer.append(line)
            if not catch_output:
                stderr_callback(line)

    @staticmethod
    def fill_result(stdout_buffer: List[str], stderr_buffer: List[str], returncode: int, result: SubprocessResult) -> None:
        result.stdout = ''.join(stdout_buffer)
        result.stderr = ''.join(stderr_buffer)
        result.returncode = returncode
