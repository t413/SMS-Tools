import argparse, sys, time, dateutil.parser, sqlite3, csv
debug = False
do_save = True #save the results?

def main():
    parser = argparse.ArgumentParser(description='Import texts to android sms database file.')
    inputgroup = parser.add_mutually_exclusive_group()
    inputgroup.add_argument( "-csv", type=argparse.FileType('r'), help='input CSV file' )
    inputgroup.add_argument( "-iphone", type=str, help='input iPhone sms.db file' )
    parser.add_argument('outfile', type=str, help='output mmssms.db file use. Must alread exist.')
    parser.add_argument('-d', action='store_true', dest='debug', help='extra info')
    args = parser.parse_args()#"-iphone ../sms.db mmssms.db".split())
    global debug
    debug = args.debug if args.debug else debug
    
    if args.csv:
        starttime = time.time()
        texts = readTextsFromCSV( args.csv )
        print "got all texts in {0} seconds, {1} items read".format( (time.time()-starttime), len(texts) )
    elif args.iphone:
        starttime = time.time()
        texts = readTextsFromIPhone( args.iphone )
        print "got all texts in {0} seconds, {1} items read".format( (time.time()-starttime), len(texts) )
        
    exportAndroidSQL(texts, args.outfile)

class Text:
    def __init__( self, num, date, type, body, cid):
        self.num  = num
        self.date = date
        self.type = type
        self.body = body
        self.cid  = cid
    def __str__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

def readTextsFromIPhone(file):
    conn = sqlite3.connect(file)
    c = conn.cursor()
    i=0
    texts = []
    query = c.execute(
        'SELECT handle.id, message.date, message.is_from_me, message.text, message.handle_id \
         FROM message \
         INNER JOIN handle ON message.handle_id = handle.ROWID \
         ORDER BY message.ROWID ASC;')
    for row in query:
        if debug and i > 80:
            return
        i+=1
        txt = Text(row[0],long((row[1] + 978307200)*1000),(row[2]+1),row[3],row[4])
        texts.append(txt)
        if debug:
            print txt
    return texts

def readTextsFromCSV(file):
    inreader = csv.reader( file )

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
        if debug and i > 80:
            break #debug breaks early
        
        txt = Text(
                row[phNumberIndex], #number
                long(float(dateutil.parser.parse(row[dateIndex]).strftime('%s.%f'))*1000), #date
                (2 if row[typeIndex]=='0' else 1), #type
                row[bodyIndex], #body
                row[cidIndex] ) #contact ID
        texts.append(txt)
        i += 1
    return texts
    
def exportAndroidSQL(texts, outfile):
    #open resources
    conn = sqlite3.connect(outfile)
    c = conn.cursor()

    #start the main loop through each message
    i=0
    lastSpeed=0
    lastCheckedSpeed=0
    starttime = time.time()
    convoMap = {}

    for txt in texts:
        if debug and i > 80:
            break #debug breaks early
    
    
        #add a new conversation thread entry (and canonical_addresses lookup entry) if it doesn't exist
        if not txt.cid in convoMap:
            c.execute( "INSERT INTO canonical_addresses (address) VALUES (?)", [txt.num])
            contact_id = c.lastrowid
            c.execute( "INSERT INTO threads (recipient_ids) VALUES (?)", [contact_id])
            convoMap[txt.cid] = c.lastrowid
    
        #now update conversation thread (assuming it was just created or existed before)
        thread_id = convoMap[txt.cid]
        c.execute( "UPDATE threads SET message_count=message_count + 1,snippet=?,'date'=? WHERE _id=? ", [txt.body,txt.date,thread_id] )
        
        if debug:
            c.execute( "SELECT * FROM threads WHERE _id=?", [thread_id] )
            print "updated thread: " + str(c.fetchone())
            print "adding entry to message db: " + str([txt.num,txt.date,txt.body,thread_id,txt.type])
        
        #add message to sms table
        c.execute( "INSERT INTO sms (address,'date',body,thread_id,read,type,seen) VALUES (?,?,?,?,1,?,1)", [txt.num,txt.date,txt.body,thread_id,txt.type])
    
        #print status
        if i%100 == 0:
            lastSpeed = int(100/(time.time() - lastCheckedSpeed))
            lastCheckedSpeed = time.time()
        sys.stdout.write( "\rprocessed {0} entries, {1} convos, ({2} entries/sec)".format(i, len(convoMap), lastSpeed ))
        sys.stdout.flush()
    
        i += 1



    print "\nfinished in {0} seconds (average {1}/second)".format((time.time() - starttime), int(i/(time.time() - starttime)))

    if debug:
        print "\n\nthreads: "
        for row in c.execute('SELECT * FROM threads'):
            print row


    if do_save and not debug:
        conn.commit()
        print "changes saved to "+outfile

    c.close()
    conn.close()


if __name__ == '__main__':
    main()