import sqlite3
import core, sms_exceptions


class IOS5:
    """ iOS 5 sqlite reader and writer """


    def parse(self, file):
        """ Parse iOS 5 sqlite file to Text[] """

        conn = sqlite3.connect(file)
        c = conn.cursor()
        i=0
        texts = []
        contactLookup = {}
        query = c.execute(
            'SELECT is_madrid, madrid_handle, address, date, text, madrid_date_read, flags FROM message;')
        for row in query:
            if row[0]:
                txt = core.Text( row[1], long((row[3] + 978307200)*1000), (row[5]==0), row[4])
            else:
                from_me = row[6] & 0x01
                txt = core.Text( row[2], long(row[3]*1000), (from_me==1), row[4])

            lookup_num = str(txt.num)[-10:]
            if not lookup_num in contactLookup:
                contactLookup[lookup_num] = i
            txt.cid = contactLookup[lookup_num]
            texts.append(txt)

            i+=1
        return texts

    def write(self, texts, outfile):
        raise sms_exceptions.UnfinishedError("iOS output not yet implemented :/ (email me to help test!)")
        #TODO !!!
