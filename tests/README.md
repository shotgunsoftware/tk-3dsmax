# Running 3dsmax engine tests

The 3dsmax tests need to run inside 3dsMax as a script. So to run these tests,
you must be on Windows with 3dsMax installed.

To run these tests, you need to do the following

 1. Make sure the following tk repositories are clone in the same base folder as
    this one:
      * tk-core
      * tk-multi-publish2
      * tk-framework-shotgunutils
      * tk-framework-qtwidgets

    In general, anything defined in `tests/fixtures/config/env/test.yml`

1. From a terminal, create a virtual environment at `tests/venv`
   ```ps1
   & "C:\Program Files\Autodesk\3ds Max {version}\Python\python.exe" -m venv tests/venv
   ```

1. Install all dependencies needed for the test:
   ```ps1
    tests\venv\Scripts\pip install -U -r tests\requirements.txt
    ```

1. Launch 3dsmax
    1. Go to the "**Scripting**" menu → select "**Scripting Listener**"
    1. "**File**" → "**Run Script**"
    1. Browse to `tests/run_tests.py`

Note that after running the tests about a dozen time or so, the 3dsMax session seems to be getting corrupted and Toolkit's module importer fails at resolving the location of our bundles.
