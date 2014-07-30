import sys, time, sqlite3
from core import Text


class Android:
    """ Android sqlite reader and writer """


    def parse(self, file):
        """ Parse a sqlite file to Text[] """

        db = sqlite3.connect(file)
        cursor = db.cursor()
        texts = self.parse_cursor(cursor)
        cursor.close()
        db.close()
        return texts

    def parse_cursor(self, cursor):
        texts = []
        query = cursor.execute(
            'SELECT address, date, type, body \
             FROM sms \
             ORDER BY _id ASC;')
        for row in query:
            txt = Text(row[0],long(row[1]),(row[2]==2),row[3])
            texts.append(txt)
        return texts

    def write(self, texts, outfile):
        """ write a Text[] to sqlite file """
        #open resources
        conn = sqlite3.connect(outfile)
        cursor = conn.cursor()

        self.write_cursor(texts, cursor)

        conn.commit()
        cursor.close()
        conn.close()
        print "changes saved to", outfile


    def write_cursor(self, texts, cursor):

        #populate fast lookup table:
        contactIdFromNumber = {}
        query = cursor.execute('SELECT _id,address FROM canonical_addresses;')
        for row in query:
            contactIdFromNumber[self.cleanNumber(row[1])] = row[0]

        #start the main loop through each message
        i=0
        lastSpeed=0
        lastCheckedSpeed=0
        starttime = time.time()

        for txt in texts:

            clean_number = self.cleanNumber(txt.num)

            #add a new canonical_addresses lookup entry and thread item if it doesn't exist
            if not clean_number in contactIdFromNumber:
                cursor.execute( "INSERT INTO canonical_addresses (address) VALUES (?)", [txt.num])
                contactIdFromNumber[clean_number] = cursor.lastrowid
                cursor.execute( "INSERT INTO threads (recipient_ids) VALUES (?)", [contactIdFromNumber[clean_number]])
            contact_id = contactIdFromNumber[clean_number]

            #now update the conversation thread (happends with each new message)
            cursor.execute( "UPDATE threads SET message_count=message_count + 1,snippet=?,'date'=? WHERE recipient_ids=? ", [txt.body,txt.date,contact_id] )
            cursor.execute( "SELECT _id FROM threads WHERE recipient_ids=? ", [contact_id] )
            thread_id = cursor.fetchone()[0]

            if False:
                print "thread_id = "+ str(thread_id)
                cursor.execute( "SELECT * FROM threads WHERE _id=?", [contact_id] )
                print "updated thread: " + str(cursor.fetchone())
                print "adding entry to message db: " + str([txt.num,txt.date,txt.body,thread_id,txt.incoming+1])

            #add message to sms table
            cursor.execute( "INSERT INTO sms (address,'date',body,thread_id,read,type,seen) VALUES (?,?,?,?,1,?,1)", [txt.num,txt.date,txt.body,thread_id,txt.incoming+1])

            #print status (with fancy speed calculation)
            recalculate_every = 100
            if i%recalculate_every == 0:
                lastSpeed = int(recalculate_every/(time.time() - lastCheckedSpeed))
                lastCheckedSpeed = time.time()
            sys.stdout.write( "\rprocessed {0} entries, {1} convos, ({2} entries/sec)".format(i, len(contactIdFromNumber), lastSpeed ))
            sys.stdout.flush()
            i += 1

        print "\nfinished in {0} seconds (average {1}/second)".format((time.time() - starttime), int(i/(time.time() - starttime)))

        if False:
            print "\n\nthreads: "
            for row in cursor.execute('SELECT * FROM threads'):
                print row


    def cleanNumber(self, numb):
        if not numb:
            return False
        stripped = ''.join(ch for ch in numb if ch.isalnum())
        if not stripped.isdigit():
            return False
        return stripped[-10:]



if __name__ == '__main__':
    import sys, os
    # DBFILE = os.path.join(os.path.dirname(__file__), "../tests/test_files/ethans-working-mmssms.db")
    # parsed = AndroidDB().parse(DBFILE)
    # print parsed[0]

    ROOTDIR = os.path.dirname(os.path.dirname(__file__))
    DB_SQL_FILE = os.path.join(ROOTDIR, 'initdb', 'android_db.sql')

    db = sqlite3.connect(':memory:')
    with open(DB_SQL_FILE,'r') as f:
        setupSQL = f.read()
    db.executescript(setupSQL)

    print parsed_texts




