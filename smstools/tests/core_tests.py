# -*- coding: utf-8 -*-
import unittest, sys, os, sqlite3, glob
##include smstools/ directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
import core, ios6

REAL_TEST_FILES_DIR = "/Users/timo/Downloads/testing_smstools/test_files/"

class BaseTests(unittest.TestCase):

    def assertTextsEqual(self, t1, t2):
        warns = core.compareTexts(t1, t2,
                throw_errors=True,
                required_attrs=['num', 'incoming', 'body'])
        self.assertEqual(long(t1.date/1000), long(t2.date/1000))
        if 'date' in warns: warns.remove('date')
        if warns: core.warning("text differ with %s" % (warns))

    def get_test_db_files(self, directory=REAL_TEST_FILES_DIR, for_parser=None):
        files = glob.glob(os.path.join(directory,"*"))
        outfiles = []
        for filename in files:
            try:
                parser = core.getParser(filename)
                if (for_parser==None) or (parser.__class__ == for_parser):
                    outfiles.append(filename)
            except: pass
        return outfiles

    def get_texts_from_dir(self, directory=REAL_TEST_FILES_DIR, for_parser=None):
        files = self.get_test_db_files(directory, for_parser)
        texts = []
        for filename in files:
            parser = core.getParser(filename)
            new_texts = parser.parse(filename)
            print "(%d) from <%s> %s" % (len(new_texts), parser.__class__, os.path.basename(filename))
            texts.extend(new_texts)
        print "sorting all %d texts by date" % len(texts)
        return sorted(texts, key=lambda text: text.date)

    def get_empty_db_in_memory(self, module_parser):
        db = sqlite3.connect(':memory:')
        db.executescript(module_parser.INIT_DB_SQL)
        return db


class CoreTests(BaseTests):
    def test_clean_number(self):
        self.assertEqual(core.cleanNumber("+15105023391"),   "5105023391")
        self.assertEqual(core.cleanNumber("(415) 637-3582"), "4156373582")
        self.assertEqual(core.cleanNumber("guy@email.com"),  "guy@email.com")
        self.assertEqual(core.cleanNumber("89203"),          "89203")

    def test_read_all_test_files(self):
        if os.path.exists(REAL_TEST_FILES_DIR):
            self.get_texts_from_dir(REAL_TEST_FILES_DIR)
        else:
            print "test_parse_all_real_files() can't run, REAL_TEST_FILES_DIR does not exist."

    def test_read_all_ios6(self):
        if not os.path.exists(REAL_TEST_FILES_DIR): return
        self.get_texts_from_dir(REAL_TEST_FILES_DIR, ios6.IOS6)



if __name__ == '__main__':
    unittest.main()
