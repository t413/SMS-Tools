# -*- coding: utf-8 -*-
import unittest, sys, os, sqlite3
##include smstools/ directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
import core

class AndroidTest(unittest.TestCase):

    def test_clean_number(self):
        self.assertEqual(core.cleanNumber("+15105023391"),   "5105023391")
        self.assertEqual(core.cleanNumber("(415) 637-3582"), "4156373582")
        self.assertEqual(core.cleanNumber("guy@email.com"),  "guy@email.com")
        self.assertEqual(core.cleanNumber("89203"),          "89203")


if __name__ == '__main__':
    unittest.main()
