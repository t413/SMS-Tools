import unittest, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
import core, jsoner, core_tests

class JsonerTests(core_tests.BaseTests):

    def test_write_parse(self):
        true_texts = core.getTestTexts()

        strtxts = jsoner.JSONer().toJson(true_texts)

        decoded_objs = jsoner.JSONer().fromJson(strtxts)

        self.assertEqual(decoded_objs, true_texts)

        for i in range(len(true_texts)):
            self.assertEqual(true_texts[i], decoded_objs[i])


if __name__ == '__main__':
    unittest.main()
