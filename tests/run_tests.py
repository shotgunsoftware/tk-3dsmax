# Copyright (c) 2019 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys

__file__ = os.path.abspath(__file__)

tests_folder = os.path.abspath(os.path.dirname(__file__))
repo_root = os.path.dirname(tests_folder)

# Activate the virtual environment required to run test tests in 3dsmax.
sys.prefix = os.path.join(tests_folder, "venv")
sys.path.insert(0, os.path.join(tests_folder, "venv", "Lib", "site-packages"))

import pytest
import mock

# We need to patch a couple of things to make pytest and argparse happy.
# argparse doesn't like it when argv is empty, which is what happens when
# running a script in Max, so create a believable argv and set it.
argv = [
    "pytest",
    "tests/test_publisher_hooks.py",
    "--capture",
    "no",
    "--cov",
    "--cov-config",
    os.path.join(repo_root, ".coveragerc"),
    "--cov-report=html",
    "--verbose",
]


# Patch argv
@mock.patch.object(sys, "argv", argv, create=True)
# The sys.stdout and sys.stderr in Max are some mocked
# object, which is missing isatty and fileno, so we'll implement them.
# and return True, since we're not a terminal.
@mock.patch.object(sys.stdout, "isatty", create=True, return_value=False)
@mock.patch.object(sys.stderr, "fileno", create=True, return_value=2)
def run_tests(_mock1, _mock2):
    current_dir = os.getcwd()
    # It appears the path specified inside coveragerc is relative
    # to the current working directly and not the test root,
    # so we're going to change the current directory and restore it.
    os.chdir(repo_root)
    try:
        # pytest expects the arguments and not the name of the executable
        # to be passed in.
        pytest.main(argv[1:])
    finally:
        if "test_publisher_hooks" in sys.modules:
            sys.modules.pop("test_publisher_hooks")
        os.chdir(current_dir)


run_tests()
