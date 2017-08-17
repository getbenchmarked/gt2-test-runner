"""GT2 Test Runner
===============

Python unittest test runner with coverage and colourised output support.

Based heavily on `Django Juno test runner <https://github.com/yunojuno/django-juno-testrunner>`_

For per-test coverage result, the `coverage` module must be available.

If the `colorama` module is available, test output will be colourised.
"""

import logging
import os
import time
import unittest
import warnings

try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False


def collect_sources(directories):
    """Collect all source files under `directory`

    The result can be fed to `GT2Runner`’s `coverage_sources` parameter,
    so it starts measuring coverage data.

    :param directories: a directory name, or a list of directories
    :type directories: str, list(str)
    :returns: a list of source file names
    :rtype: list(str)
    """

    def _collect_from_dir(base_dir, ignore_list=None):
        files = []
        ignore_list = ignore_list or []

        for (dirpath, dirnames, filenames) in os.walk(base_dir):
            ignore = False

            for ign in ignore_list:
                ign = os.path.join(base_dir, ign)

                while ign.endswith(os.sep):
                    ign = ign[:-len(os.sep)]

                if dirpath == ign or dirpath.startswith(ign):
                    ignore = True

                    break

            if ignore:
                continue

            files.extend([os.path.join(dirpath, name)
                          for name in filenames
                          if name.endswith('.py')])

        return files

    if isinstance(directories, str):
        directories = [directories]

    file_list = []

    for directory in directories:
        file_list += _collect_from_dir(directory)

    return file_list


def test_list_gen(suite):
    """Generator to iterate over a TestSuite recursively

    This generator function recursively iterates over a TestSuite
    object, effectively collecting all test functions.
    """

    for test in suite:
        if unittest.suite._isnotsuite(test):
            yield test
        else:
            for test_case in test_list_gen(test):
                yield test_case


def filter_tests(suite_or_dir, selector=None):
    """Filter test cases based on their name

    :param suite_or_dir: a test suite to filter, or a directory name where
        tests should be discovered in
    :type suite_or_dir: unittest.TestSuite, str
    :param selector: a list of fully qualified Python function names
        (i.e. test_module.TestClass.test_method).
    :type selector: list(str)
    :returns: a new test suite with the filtered results, or `None` if the
        selector didn’t match any tests
    :rtype: unittest.TestSuite, None
    """

    selector = selector or []

    # If `suite_or_dir` is a string, interpret it as a directory name, and
    # do test discovery
    if isinstance(suite_or_dir, str):
        tests_discovered = unittest.TestLoader().discover(suite_or_dir)
    else:
        tests_discovered = suite_or_dir

    # If selector is empty, we simply return the full test suite
    if not selector:
        return tests_discovered

    filtered_suite = unittest.TestSuite()
    all_selectors = set(selector)
    selector = [test_name.split('.') for test_name in all_selectors]
    matched_selectors = set()

    for test_case in test_list_gen(tests_discovered):
        # For comparison, we convert the test names in the discovered suite
        # to the same format as we did for the command line parameters.
        #
        # The reason for joining /and/ splitting is that `test.__module__`
        # may already be in dotted notation. Maybe splitting only
        # `test.__module__` would be more effective, but even if we get
        # over 10000 tests, discovery itself will take significantly more
        # time than this.
        #
        # The reason to compare this way instead of joining all the parts
        # and using `str.startswith` is a design decision; I haven’t tested
        # it for performance.
        test_fqn = '.'.join((test_case.__module__,
                             test_case.__class__.__name__,
                             test_case._testMethodName)).split('.')

        # Iterate over the test names in `selector`
        for test_method in selector:
            # Calculate how many parts we should compare.  TBH I can’t tell
            # a use case when the one specified on the command line has more
            # parts other than a typo, but it’s better to be safe than sorry.
            common_length = min(len(test_fqn), len(test_method))

            # If the two match, add it to our filtered suite
            if test_fqn[0:common_length] == test_method[0:common_length]:
                filtered_suite.addTest(test_case)
                matched_selectors.add('.'.join(test_method))

    if not filtered_suite.countTestCases():
        logging.error('No tests were matched.')

        return None

    # If there were any selectors that didn’t match a tests case, issue
    # a warning
    if matched_selectors != all_selectors:
        warnings.warn('The following selectors did not match any tests: {}'
                      .format(', '.join(all_selectors.difference(matched_selectors))),
                      UserWarning)

    return filtered_suite

class AutoDict(dict):
    """dict subclass that automatically adds elements upon access
    """

    def __init__(self, default_value=None, *args, **kwargs):
        self.default_value = default_value

        super(AutoDict, self).__init__(*args, **kwargs)

    def __getitem__(self, item):
        if item not in self:
            self[item] = self.default_value

        return super(AutoDict, self).__getitem__(item)


class ColorizedTextTestResult(unittest.result.TestResult):
    """Class to colorize test result output
    """

    def __init__(self,
                 stream=None, descriptions=None, verbosity=None,
                 coverage_sources=None,
                 rerun_log=None):
        super(ColorizedTextTestResult, self).__init__()

        self.separator1 = '=' * 70
        self.separator2 = '-' * 70
        self.in_subtest = False
        self.verbosity = verbosity
        self.dots = verbosity == 1
        self.show_all = verbosity > 1
        self.success_char = '.'
        self.fail_char = 'F'
        self.error_char = 'E'
        self.skip_char = 's'
        self.expected_fail_char = 'x'
        self.unexpected_success_char = 'u'
        self.subtest_char = ':'
        self.stream = stream
        self.descriptions = descriptions
        self.coverage_sources = coverage_sources
        self.coverage = None
        self.rerun_log_name = rerun_log
        self.rerun_log = None

        if COVERAGE_AVAILABLE and coverage_sources:
            self.coverage = coverage.coverage(
                branch=True,
                include=coverage_sources)

        # Colours will only be applied if the colorama library is available
        try:
            from colorama import init, Fore, Back, Style

            init()

            self.success_color = Fore.BLACK + Back.GREEN
            self.fail_color = Fore.YELLOW + Back.RED
            self.error_color = Fore.WHITE + Back.RED + Style.BRIGHT
            self.skip_color = Fore.YELLOW + Back.BLACK
            self.expected_fail_color = Fore.RED + Back.BLACK
            self.unexpected_success_color = Fore.RED + Back.BLACK
            self.reset_color = Style.RESET_ALL
        except ImportError:
            self.success_color = ''  # pylint: disable=redefined-variable-type
            self.fail_color = ''  # pylint: disable=redefined-variable-type
            self.error_color = ''  # pylint: disable=redefined-variable-type
            self.skip_color = ''  # pylint: disable=redefined-variable-type
            self.expected_fail_color = ''  # pylint: disable=redefined-variable-type
            self.unexpected_success_color = ''  # pylint: disable=redefined-variable-type
            self.reset_color = ''  # pylint: disable=redefined-variable-type

        # Timing information
        self.test_data = AutoDict(default_value={})

        self.coverage_calculated = False
        if self.rerun_log_name:
            self.rerun_log = open(self.rerun_log_name, 'w+')

    @property
    def coverage_data(self):
        """The overall coverage data
        """

        if not self.coverage_calculated:
            print('Calculating overall coverage data')

            for test_data in self.test_data.values():
                self.coverage.data.update(test_data['cov'])

            self.coverage_calculated = True

        return self.coverage

    @staticmethod
    def _get_test_fqn(test):
        """Get the fully qualified name of a test

        It is in the `format module.Class.method`, where module also can
        be in dotted notation (but we don’t care).
        """

        return '.'.join((test.__module__,
                         test.__class__.__name__,
                         test._testMethodName))

    def add_to_rerun_log(self, test):
        """Add a test to the rerun log
        """

        if not self.rerun_log:
            return

        test_fqn = self._get_test_fqn(test)

        if test_fqn.startswith('unittest.loader._FailedTest'):
            test_fqn = '.'.join(test_fqn.split('.')[3:])

        self.rerun_log.write(test_fqn)
        self.rerun_log.write('\n')

    def stopTestRun(self):
        super(ColorizedTextTestResult, self).stopTestRun()

        test_list = sorted([(test, info['stop'] - info['start'])
                            for test, info in self.test_data.items()],
                           key=lambda x: -x[1])[:5]

        if len(test_list) > 1:
            self.stream.writeln('\n\nThe {} slowest tests:\n'
                                .format(len(test_list)))

            for test, length in test_list[0:5]:
                self.stream.writeln('{test} ({length:.5f}s)'.format(
                    test=test, length=length))

        if self.rerun_log_name:
            self.rerun_log.close()

    def startTest(self, test):
        test_fqn = self._get_test_fqn(test)
        self.test_data[test_fqn]['start'] = time.time()

        if self.coverage:
            self.coverage.start()

        if not self.dots:
            self.stream.write(test_fqn)
            self.stream.flush()

        return super(ColorizedTextTestResult, self).startTest(test)

    def stopTest(self, test):
        test_fqn = self._get_test_fqn(test)
        self.test_data[test_fqn]['stop'] = time.time()

        if self.coverage:
            self.coverage.stop()
            self.test_data[test_fqn]['cov'] = self.coverage.data

            if self.verbosity > 2:
                self.stream.writeln('')
                self.coverage.report()

            self.coverage.data = coverage.CoverageData()

        if self.dots and self.in_subtest:
            self.stream.write(')')
        elif not self.dots:
            self.stream.writeln(' ({:.5f}s)'.format(
                self.test_data[test_fqn]['stop'] -
                self.test_data[test_fqn]['start']))

        self.in_subtest = False

        return super(ColorizedTextTestResult, self).stopTest(test)

    def addSuccess(self, test):
        super(ColorizedTextTestResult, self).addSuccess(test)

        if self.dots:
            self.stream.write(self.success_color +
                              self.success_char +
                              self.reset_color)
        else:
            if self.in_subtest:
                self.stream.write('Final outcome:')

            self.stream.write(' [' + self.success_color +
                              'OK' + self.reset_color + ']')

        self.stream.flush()

    def addError(self, test, err):
        super(ColorizedTextTestResult, self).addError(test, err)

        if self.dots:
            self.stream.write(self.error_color +
                              self.error_char +
                              self.reset_color)
        else:
            if self.in_subtest:
                self.stream.write('Final outcome:')

            self.stream.write(' [' + self.error_color +
                              'ERROR' + self.reset_color + ']')

        self.stream.flush()
        self.add_to_rerun_log(test)

    def addFailure(self, test, err):
        super(ColorizedTextTestResult, self).addFailure(test, err)

        if self.dots:
            self.stream.write(self.fail_color +
                              self.fail_char +
                              self.reset_color)
        else:
            if self.in_subtest:
                self.stream.write('Final outcome:')

            self.stream.write(' [' + self.fail_color +
                              'FAILED' + self.reset_color + ']')

        self.stream.flush()
        self.add_to_rerun_log(test)

    def addSkip(self, test, reason):
        super(ColorizedTextTestResult, self).addSkip(test, reason)

        if self.dots:
            self.stream.write(self.skip_color +
                              self.skip_char +
                              self.reset_color)
        else:
            if self.in_subtest:
                self.stream.write('Final outcome:')

            self.stream.write(' [' + self.skip_color +
                              'skipped' + self.reset_color +
                              '] (' + (reason or 'No reason') + ')')

        self.stream.flush()

    def addExpectedFailure(self, test, err):
        super(ColorizedTextTestResult, self).addExpectedFailure(test, err)

        if self.dots:
            self.stream.write(self.expected_fail_color +
                              self.expected_fail_char +
                              self.reset_color)
        else:
            if self.in_subtest:
                self.stream.write('Final outcome:')

            self.stream.write(' [' + self.expected_fail_color +
                              'expected failure' + self.reset_color + ']')

        self.stream.flush()

    def addUnexpectedSuccess(self, test):
        super(ColorizedTextTestResult, self).addUnexpectedSuccess(test)

        if self.dots:
            self.stream.write(self.unexpected_success_color +
                              self.unexpected_success_char +
                              self.reset_color)
        else:
            if self.in_subtest:
                self.stream.write('Final outcome:')

            self.stream.write(' [' + self.unexpected_success_color +
                              'unexpected success' + self.reset_color + ']')

        self.stream.flush()

    def addSubTest(self, test, subtest, err):
        super(ColorizedTextTestResult, self).addSubTest(test, subtest, err)

        if self.dots:
            if not self.in_subtest:
                self.stream.write('(')

            if err:
                self.stream.write(self.fail_color)
            else:
                self.stream.write(self.success_color)

            self.stream.write(self.subtest_char + self.reset_color)
        else:
            if not self.in_subtest:
                self.stream.write('\n')
            self.stream.write('    Subtest ' + subtest._subDescription())

            if err:
                self.stream.write(' [' + self.fail_color +
                                  'failed' + self.reset_color + ']')
            else:
                self.stream.write(' [' + self.success_color +
                                  'OK' + self.reset_color + ']')

            self.stream.write('\n')

        self.stream.flush()

        if not self.in_subtest:
            self.in_subtest = True

    def get_description(self, test):
        """Get the short description of a test case
        """

        doc_first_line = test.shortDescription()

        if self.descriptions and doc_first_line:
            return '\n'.join((str(test), doc_first_line))

        return str(test)

    def printErrors(self):
        if self.dots or self.show_all:
            self.stream.writeln()

        self.print_error_list('ERROR', self.errors)
        self.print_error_list('FAIL', self.failures)

    def print_error_list(self, flavour, errors):
        """Print the list of errors
        """

        for test, err in errors:
            self.print_single_error(flavour, test, err)

    def print_single_error(self, flavour, test, err):
        """Print a single error to the output stream
        """

        self.stream.writeln(self.separator1)
        self.stream.writeln('{flavour}: {test}'
                            .format(flavour=flavour,
                                    test=self.get_description(test)))
        self.stream.writeln(self.separator2)
        self.stream.writeln(str("{}".format(err)))

    def coverage_report(self, save_data=False, html_dir=None, to_stream=True):
        """Report coverage data

        :param save_data: if `True`, save coverage data to the .coverage file
        :type save_data: bool
        :param html_dir: If not `None`, write HTML formatted coverage data
            to this directory
        :type html_dir: None, str
        :param to_stream: if `True`, write coverage data to the output stream
        :type to_stream: bool
        """

        # Return silently if the Coverage package is not available, or
        # coverage measurement is not requested
        if not COVERAGE_AVAILABLE or not self.coverage_sources:
            return

        if self.verbosity > 2 and to_stream:
            print('Sorry, overall coverage data does not work '
                  'when per-test reporting is turned on.')

            return

        cov = self.coverage_data

        if to_stream:
            print('\nOverall coverage report', file=self.stream)
            print('=======================\n', file=self.stream)
            cov.report(file=self.stream)

        if save_data:
            cov.save()

        if html_dir:
            cov.html_report(directory=html_dir)

            print('\nHTML coverage data is saved as file://{}/index.html'.format(html_dir),
                  file=self.stream)


class GT2Runner(unittest.TextTestRunner):
    """Test runner with colourised output and per-test coverage support
    """

    resultclass = ColorizedTextTestResult

    def __init__(self, coverage_sources=None, rerun_log=None, *args, **kwargs):
        self.coverage_sources = coverage_sources
        self.rerun_log = rerun_log

        super(GT2Runner, self).__init__(*args, **kwargs)

    def _makeResult(self):
        return self.resultclass(stream=self.stream,
                                descriptions=self.descriptions,
                                verbosity=self.verbosity,
                                coverage_sources=self.coverage_sources,
                                rerun_log=self.rerun_log)
