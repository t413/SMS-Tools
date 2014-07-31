import unittest, sys, os, StringIO
if (os.path.basename(sys.path[0]) == "tests"):
    sys.path.append(os.path.dirname(sys.path[0]))
from core.core import Text
import core.jsoner

class AndroidTest(unittest.TestCase):


    def test_write_parse(self):
        true_texts = core.core.getTestTexts()

        file = StringIO.StringIO()
        core.jsoner.JSONer().write(true_texts, file)
        file.seek(0)
        json_str = file.read().decode('utf-8')

        file.seek(0)
        decoded_objs = core.jsoner.JSONer().parse(file)
        self.assertEqual(decoded_objs, true_texts)

        for i in range(len(true_texts)):
            self.assertEqual(true_texts[i], decoded_objs[i])


if __name__ == '__main__':
    unittest.main()
