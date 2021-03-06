# -*- coding: utf-8 -*-
"""
Defines a pytest fixture for creating mock AiiDA codes.
"""

import uuid
import shutil
import inspect
import pathlib
import typing as ty

import pytest

from ._env_keys import EnvKeys
from .._config import get_config

__all__ = ("mock_code_factory", )


@pytest.fixture(scope='function')
def mock_code_factory(aiida_localhost):
    """
    Fixture to create a mock AiiDA Code.
    """
    config = get_config().get('mock_code', {})

    def _get_mock_code(
        label: str,
        entry_point: str,
        data_dir_abspath: ty.Union[str, pathlib.Path],
        ignore_files: ty.Iterable[str] = ('_aiidasubmit.sh', )
    ):
        """
        Creates a mock AiiDA code. If the same inputs have been run previously,
        the results are copied over from the corresponding sub-directory of
        the ``data_dir_abspath``. Otherwise, the code is executed if an
        executable is specified in the configuration, or fails if it is not.

        Parameters
        ----------
        label :
            Label by which the code is identified in the configuration file.
        entry_point :
            The AiiDA calculation entry point for the default calculation
            of the code.
        data_dir_abspath :
            Absolute path of the directory where the code results are
            stored.
        ignore_files :
            A list of files which are not copied to the results directory
            when the code is executed.
        """
        from aiida.orm import Code

        # we want to set a custom prepend_text, which is why the code
        # can not be reused.
        code_label = f'mock-{label}-{uuid.uuid4()}'

        executable_path = shutil.which('aiida-mock-code')
        code = Code(
            input_plugin_name=entry_point, remote_computer_exec=[aiida_localhost, executable_path]
        )
        code.label = code_label
        code.set_prepend_text(
            inspect.cleandoc(
                f"""
                export {EnvKeys.LABEL.value}={label}
                export {EnvKeys.DATA_DIR.value}={data_dir_abspath}
                export {EnvKeys.EXECUTABLE_PATH.value}={config.get(label, '')}
                export {EnvKeys.IGNORE_FILES.value}={':'.join(ignore_files)}
                """
            )
        )

        code.store()
        return code

    return _get_mock_code
