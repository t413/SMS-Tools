import unittest, sys, os, StringIO
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
import core, jsoner

class AndroidTest(unittest.TestCase):


    def test_write_parse(self):
        true_texts = core.getTestTexts()

        file = StringIO.StringIO()
        jsoner.JSONer().write(true_texts, file)
        file.seek(0)
        json_str = file.read().decode('utf-8')

        file.seek(0)
        decoded_objs = jsoner.JSONer().parse(file)
        self.assertEqual(decoded_objs, true_texts)

        for i in range(len(true_texts)):
            self.assertEqual(true_texts[i], decoded_objs[i])


if __name__ == '__main__':
    unittest.main()
