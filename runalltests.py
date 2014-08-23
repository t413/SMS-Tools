#!/usr/bin/env python
import os, sys
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE_DIR,'smstools'))
sys.path.insert(0, os.path.join(BASE_DIR,'smstools/tests'))
import unittest

test_modules = [
    'core_tests',
    'ios6_tests',
    'android_tests',
    'jsoner_tests',
    ]

suite = unittest.TestSuite()

for test_module in test_modules:
    suite.addTest(unittest.defaultTestLoader.loadTestsFromName(test_module))

unittest.TextTestRunner().run(suite)

