GT2 Test Runner
===============

Alternative unittest test runner with colourised output and per-test coverage support, from the
devs of getbenchmarked.io.

It extends the standard :code:`unittest.TextTestRunner` class, with a bunch of tweaks:

- with no verbosity set, it will print only one character for each test.  With a verbosity of 1,
  one line for each test is printed
- if the `colorama` library is installed, the dot or the test outcome text is printed in colours
- if the `coverage` package is installed, and the `coverage_sources` parameter is set on the
  runner, it will measure test coverage, both for each test, and overall
- if verbosity is above 1, it will print coverage data for each test
- if requested with the `rerun_log` parameter, tests that fail or raise an exception are collected
  in the specified file, so they can be re-run later

Planned features
----------------

- display a countdown in verbose mode, so you can see how many tests are remaining
- collect the output of failing/errored tests to a file to be analysed later

Known problems
--------------

When verbosity is above one (thus, per-test coverage report is printed), it can’t print the
overall coverage data.  We are working on it.

Right now, the library only supports Python 3, and probably won’t run in Python 2 without a lot of
tweaks.  As we use only Python 3 at getbenchmarked.io, we didn’t have the intention to support
Python 2; if you need it and do the tweaks, please send us a PR!

Installation
------------

1. Recommended installation is via **pip**, inside a **virtualenv**

   To get it from **PyPI**::

     $ pip install gt2_test_runner

   If you want a bleeding-edge version from GitHub::

     $ pip install -e git+https://github.com/GT2-io/gt2-test-runner#egg=gt2-test-runner

   Downloading the package source and installing it yourself is also an option.  To do so::

     $ python setup.py

Dependencies
------------

There are no hard dependencies for this pacakage.

- if you want colourised output, you need to install the `colorama` package
- if you need coverage reports, you need to install the `coverage` package

Usage
-----

Collecting tests
''''''''''''''''

To collect tests programatically, we provide the `filter_tests` helper function:

.. code-block:: python

   # Collect all tests from the 'tests' directory
   test_suite = filter_tests('tests')

   # Filter an existing TestSuite
   test_suite = filter_tests(existing_suite, selector=['test_module', 'test_module2.TestCase'])

   # Filter tests from 'tests' directory
   test_suite = filter_tests('tests', selector=['test_module', 'test_module2.TestCase'])

Measuring coverage data
'''''''''''''''''''''''

To measure coverage data, you have to pass the files to be included in the coverage report.  If
you want to collect all your source files automatically, you can use the `collect_sources` helper
function.

.. code-block:: python

   source_files = collect_sources('.')

Running the tests
'''''''''''''''''

To run a test suite with `GT2Runner`, you can use the following example:

.. code-block:: python

   # Collect tests
   tests = filter_tests('tests')

   # Initialise the runner
   runner = GT2Runner(verbosity=1,
                      failfast=False,
                      rerun_log='rerun-log.txt',
                      coverage_sources=collect_sources('.'))

   # Run the tests
   result = runner.run(tests)

   # Report coverage data
   result.coverage_report(save_data=True, html_dir='htmlcov', to_stream=True)
