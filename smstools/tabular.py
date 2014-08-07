# -*- coding: utf-8 -*-
import unicodecsv
import core


class Tabular:
    """ Google Voice (in sqlite or format) reader and writer """


    def parse(self, file):
        """ Parse a GV CSV file to Text[] """
        inreader = unicodecsv.reader(file, encoding='utf-8')

        #gather needed column indexes from the csv file
        firstrow = inreader.next() #skip the first line (column names)
        phNumberIndex = firstrow.index("PhoneNumber") if "PhoneNumber" in firstrow else -1
        dateIndex     = firstrow.index("TimeRecordedUTC") if "TimeRecordedUTC" in firstrow else -1
        typeIndex     = firstrow.index("Incoming") if "Incoming" in firstrow else -1
        bodyIndex     = firstrow.index("Text") if "Text" in firstrow else -1
        cidIndex      = firstrow.index("ContactID") if "ContactID" in firstrow else -1

        #check to be sure they all exist
        if (-1) in [phNumberIndex, dateIndex, typeIndex, bodyIndex, cidIndex]:
            print "CSV file missing needed columns. has: "+ str(firstrow)
            quit()

        texts = []
        i=0
        for row in inreader:
            txt = core.Text(
                    row[phNumberIndex], #number
                    long(float(dateutil.parser.parse(row[dateIndex]).strftime('%s.%f'))*1000), #date
                    row[typeIndex]=='0', #type
                    row[bodyIndex] ) #body
            texts.append(txt)
            i += 1
        return texts

    def write(self, texts, outfile):
        writer = unicodecsv.writer(outfile, quoting=unicodecsv.QUOTE_NONNUMERIC, encoding='utf-8')
        writer.writerow(texts[0].__dict__.keys())
        writer.writerows( [text.__dict__.values() for text in texts] )





if __name__ == '__main__':
    import os, random, StringIO
    ENCODING_TEST_STRING = u'Δ, Й, ק, ‎ م, ๗, あ, 叶, 葉, and 말.'
    true_texts = [ core.Text("8675309", 1326497882355L, True, 'Yo, what\'s up boo? you so "cray"'), \
        core.Text("+1(555)565-6565", 1330568484000L, False, "Goodbye cruel testing."),\
        core.Text("+1(555)565-6565", random.getrandbits(43), False, ENCODING_TEST_STRING)]
    # file = open(os.path.join(os.path.dirname(__file__),'test.csv'), 'w')
    file = StringIO.StringIO()
    Tabular().write(true_texts, file)
    file.seek(0)
    print file.read().decode('utf-8')

