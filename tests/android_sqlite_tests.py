# -*- coding: utf-8 -*-
import unittest, sys, os, sqlite3
if (os.path.basename(sys.path[0]) == "tests"):
    sys.path.append(os.path.dirname(sys.path[0]))
import core.android
from core.core import Text

ROOTDIR = os.path.dirname(os.path.dirname(__file__))
DB_SQL_FILE = os.path.join(ROOTDIR, 'initdb', 'init_android_db.sql')
TEST_DB_FILE = os.path.join(ROOTDIR, 'tests', 'test_android.db')

class AndroidTest(unittest.TestCase):

    def setUp(self):

        self.db = sqlite3.connect(':memory:')
        with open(DB_SQL_FILE,'r') as f:
            setupSQL = f.read()
        self.db.executescript(setupSQL)


    def test_write_parse(self):
        true_texts = core.core.getTestTexts()
        cursor = self.db.cursor()

        core.android.Android().write_cursor(true_texts, cursor)
        parsed_texts = core.android.Android().parse_cursor(cursor)

        for i in range(len(true_texts)):
            self.assertEqual(true_texts[i], parsed_texts[i])


if __name__ == '__main__':
    unittest.main()
