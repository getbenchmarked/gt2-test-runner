from io import StringIO
import sys
import unittest

from gt2_test_runner import GT2Runner


class TestTestCase(unittest.TestCase):
    def test_succeeding(self):
        """A succeeding test
        """

        self.assertTrue(True)

    def test_failing(self):
        """A failing test
        """

        self.assertTrue(False)

    def test_erroring(self):
        """A test that raises an exception
        """

        raise Exception()

    @unittest.skip('Just skip')
    def test_skipped(self):
        """A test that is skipped
        """

        self.assertTrue(False)

    @unittest.expectedFailure
    def test_expected_failure(self):
        """A test that is expected to fail
        """

        self.assertTrue(False)

    @unittest.expectedFailure
    def test_unexected_success(self):
        """A test that is expected to fail, but is not
        """

        self.assertTrue(True)


class RunnerTestCase(unittest.TestCase):
    def setUp(self):
        self.runner_stream = StringIO()
        self.runner = GT2Runner(verbosity=2, stream=self.runner_stream)
        loader = unittest.TestLoader()
        self.suite = loader.loadTestsFromTestCase(TestTestCase)

    def test_runner(self):
        result = self.runner.run(self.suite)

        self.assertFalse(result.wasSuccessful())
        self.assertEqual(1, len(result.failures))
        self.assertEqual(1, len(result.errors))
        self.assertEqual(1, len(result.skipped))
        self.assertEqual(1, len(result.expectedFailures))
        self.assertEqual(1, len(result.unexpectedSuccesses))


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(loader.loadTestsFromTestCase(RunnerTestCase))

    result = runner.run(suite)

    sys.exit(int(not result.wasSuccessful()))
