import time, sqlite3, csv
import core

class GoogleVoice:
    """ Google Voice (in sqlite or format) reader and writer """

    def parse(self, filepath):
        return self.parseSQL(filepath)
        #TODO add direct files parsing?

    def parseSQL(self, filepath):
        """ Parse a GV sqlite file to Text[] """

        conn = sqlite3.connect(filepath)
        c = conn.cursor()
        texts = []
        query = c.execute(
            'SELECT TextMessageID, TimeRecordedUTC, Incoming, Text, PhoneNumber \
            FROM TextMessage \
            INNER JOIN TextConversation ON TextMessage.TextConversationID = TextConversation.TextConversationID \
            INNER JOIN Contact ON TextConversation.ContactID = Contact.ContactID \
            ORDER BY TextMessage.TextMessageID ASC')
        for row in query:
            try:
                ttime = time.mktime(time.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f'))
            except ValueError:
                ttime = time.mktime(time.strptime(row[1], '%Y-%m-%d %H:%M:%S'))
            txt = core.Text(num=row[4], date=long(ttime*1000), incoming=(row[2]==1), body=row[3])
            texts.append(txt)
        return texts

    def write(self, texts, outfilepath):
        raise Exception("Can't output to Google Voice, sorry.")

