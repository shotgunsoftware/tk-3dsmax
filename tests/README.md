# Running 3dsmax engine tests

To run these tests, you need to do the following

1. From a terminal, create a virtual environment at `tests/venv`. You need to use `virtualenv` package.
2. Execute `venv/Scripts/activate.bat`.
3. Install all dependencies needed for the test: `pip install -r requirements.txt`
4. Launch 3dsmax.
5. Go to the Scripting menu, select Run Script and browse to `tests/run_tests.py`.

Note that after running the tests about a dozen time or so, the 3dsMax session seems to be getting corrupted and Toolkit's module importer fails at resolving the location of our bundles.
