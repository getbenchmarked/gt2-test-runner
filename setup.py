import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

setup(name='gt2-test-runner',
      version='1.0',
      description='unittest test runner with colourised output and per-test coverage support',
      long_description=README,
      author='Gergely Polonkai',
      author_email='gergo@gt2.io',
      url='https://github.com/gt2-io/GT2-io/gt2-test-runner',
      license='MIT',
      packages=['gt2_test_runner'],
      extras_require={
          'colors': ['colorama'],
          'coverage': ['coverage']
      },
      classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
      ])
