import json
import core


class JSONer:
    """ Json reader and writer """

    def parse(self, filepath):
        file = open(filepath, 'r')
        try:
            return self.fromJson(file.read())
        finally:
            file.close()

    def fromJson(self, string):
        def asTexts(dct):
            if ('body' in dct) and ('date' in dct) and ('num' in dct):
                return core.Text(**dct)
            return dct
        return json.loads(string, object_hook=asTexts)

    def toJson(self, texts):
        return json.dumps(texts, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def write(self, texts, outfilepath):
        outfile = open(outfilepath, 'w')
        try:
            outfile.write(self.toJson(texts))
        finally:
            outfile.close()

