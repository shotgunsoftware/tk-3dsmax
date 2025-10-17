# Running 3dsmax engine tests

The 3dsmax tests need to run inside 3dsMax as a script. So to run these tests,
you must be on Windows with 3dsMax installed.

To run these tests, you need to do the following

 1. From a PowerShell terminal, in the tk-3dsmax git clone folder:
     1. Make sure the **following** tk repositories are cloned in the same base
        folder as this one:
         * tk-core
         * tk-multi-publish2
         * tk-framework-shotgunutils
         * tk-framework-qtwidgets

        > **Note**
        >
        > In general, anything defined in `tests/fixtures/config/env/test.yml`

        Also make sure those repositories are up-to-date.

        One way to do all this is to run the
        [prepare-test-repos.ps1](tests/prepare-test-repos.ps1) script:

        ```ps1
        tests\prepare-test-repos.ps1
        ```

     1. Set the `$max_version` variable to the tested version of Max:
        ```ps1
        $max_version="2025"
        ```

    1. From a PowerShell terminal, create a virtual environment at `tests/venv`
        ```ps1
        & "C:\Program Files\Autodesk\3ds Max $($max_version)\Python\python.exe" -m venv --clear tests/venv
        ```

    1. Install the `wheel`package:
        ```ps1
        tests\venv\Scripts\pip install -U wheel
        ```

    1. Install all dependencies needed for the test:
        ```ps1
        tests\venv\Scripts\pip install -U -r tests\requirements.txt
        ```

1. Launch 3dsmax from the Windows shortcut (not from FPTR Desktop)
    1. Go to the "**Scripting**" menu → select "**Scripting Listener**"
    2. "**File**" → "**Run Script**"
    3. Browse to `tests/run_tests.py`

> [!NOTE]
> After running the tests about a dozen time or so, the 3dsMax session seems to
> be getting corrupted and Toolkit's module importer fails at resolving the
> location of our bundles.
