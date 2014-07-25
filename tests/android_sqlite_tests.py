# -*- coding: utf-8 -*-
import unittest, sys, os, sqlite3, random
if (os.path.basename(sys.path[0]) == "tests"):
    sys.path.append(os.path.dirname(sys.path[0]))
import core.android.Android
from core.core import Text

ROOTDIR = os.path.dirname(os.path.dirname(__file__))
DB_SQL_FILE = os.path.join(ROOTDIR, 'initdb', 'android_db.sql')
TEST_DB_FILE = os.path.join(ROOTDIR, 'tests', 'test_android.db')
ENCODING_TEST_STRING = u'Δ, Й, ק, ‎ م, ๗, あ, 叶, 葉, and 말.'

class AndroidTest(unittest.TestCase):

    def setUp(self):

        self.db = sqlite3.connect(':memory:')
        with open(DB_SQL_FILE,'r') as f:
            setupSQL = f.read()
        self.db.executescript(setupSQL)


    def test_write_parse(self):
        true_texts = [ Text("8675309", 1326497882355L, True, "Yo, what's up boo?"), \
            Text("+1(555)565-6565", 1330568484000L, False, "Goodbye cruel testing."),\
            Text("+1(555)565-6565", random.getrandbits(43), False, ENCODING_TEST_STRING)]
        print true_texts
        cursor = self.db.cursor()

        Android().write_cursor(true_texts, cursor)
        parsed_texts = core.android_db.Android().parse_cursor(cursor)
        print parsed_texts

        for i in range(len(true_texts)):
            self.assertEqual(true_texts[i], parsed_texts[i])


if __name__ == '__main__':
    unittest.main()
