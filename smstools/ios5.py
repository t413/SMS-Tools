import sqlite3, os
import core, sms_exceptions


class IOS5:
    """ iOS 5 sqlite reader and writer """


    def parse(self, filepath):
        """ Parse iOS 5 sqlite file to Text[] """
        db = sqlite3.connect(filepath)
        cursor = db.cursor()
        texts = self.parse_cursor(cursor)
        cursor.close()
        db.close()
        return texts

    def parse_cursor(self, cursor):
        i=0
        texts = []
        contactLookup = {}
        query = cursor.execute(
            'SELECT is_madrid, madrid_handle, address, date, text, madrid_date_read, flags \
            FROM message; ')
        for row in query:
            if row[0]:
                txt = core.Text( num=row[1], date=long((row[3] + 978307200)*1000), incoming=(row[5]==0), body=row[4])
            else:
                from_me = row[6] & 0x01
                txt = core.Text( num=row[2], date=long(row[3]*1000), incoming=(from_me==1), body=row[4])
            if not txt.num:
                txt.num = "unknown"
                core.warning("extracted text without number. row: %s" % str(row))

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
