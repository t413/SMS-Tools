# -*- coding: utf-8 -*-
import unittest, sys, os, sqlite3, time
##include smstools/ directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
import core, ios6

class AndroidTest(unittest.TestCase):

    def setUp(self):

        self.db = sqlite3.connect(':memory:')
        self.db.executescript(ios6.INIT_DB_SQL)


    def test_write_parse(self):
        true_texts = core.getTestTexts()
        cursor = self.db.cursor()

        ios6.IOS6().write_cursor(true_texts, cursor)
        parsed_texts = ios6.IOS6().parse_cursor(cursor)

        for i in range(len(true_texts)):
            self.assertTextsEqual(true_texts[i], parsed_texts[i])


    def assertTextsEqual(self, t1, t2):
        warns = core.compareTexts(t1, t2,
                throw_errors=True,
                required_attrs=['num', 'incoming', 'body'])
        self.assertEqual(long(t1.date/1000), long(t2.date/1000))
        if 'date' in warns: warns.remove('date')
        if warns: core.warning("text differ with %s" % (warns))


if __name__ == '__main__':
    unittest.main()
