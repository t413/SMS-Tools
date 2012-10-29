import argparse, os, sys, time, dateutil.parser, sqlite3, csv, xml.dom.minidom
sms_debug = False
test_run = False #test = don't save results

def sms_main():
    parser = argparse.ArgumentParser(description='Import texts to android sms database file.')
    parser.add_argument('infiles', nargs='+', type=argparse.FileType('r'), help='input files, may include multiple sources')
    parser.add_argument('outfile', type=str, help='output mmssms.db file use. Must alread exist.')
    parser.add_argument('-d', action='store_true', dest='sms_debug', help='sms_debug run: extra info, limits to 80, no save.')
    parser.add_argument('-t', action='store_true', dest='test_run', help='Test run, no saving anything')
    try:
        args = parser.parse_args()#"-iphone ../sms.db mmssms.db".split())
    except IOError:
        print "Problem opening file."
        quit()
    
    #allow use of either the -d option or sms_debug=False
    global sms_debug, test_run
    sms_debug = args.sms_debug if args.sms_debug else sms_debug
    test_run = args.test_run if args.test_run else test_run
    
    #get the texts into memory
    texts = []
    for file in args.infiles:
        starttime = time.time() #meause execution time
        extension = os.path.splitext(file.name)[1]
        if extension == ".csv":
            print "Importing texts from Google Voice CSV file:"
            new_texts = readTextsFromCSV( file )
        elif extension == ".db" or extension == ".sqlite":
            file.close()
            tableNames = getDbTableNames( file.name )
            if "handle" in tableNames:
                print "Importing texts from iOS 6 database"
                new_texts = readTextsFromIOS6( file.name )
            elif "group_member" in tableNames:
                print "Importing texts from iOS 4/5 database"
                new_texts = readTextsFromIOS5( file.name )
            elif "TextMessage" in tableNames:
                print "Importing texts from Google Voice database"
                new_texts = readTextsFromGV( file.name )
            elif "sms" in tableNames:
                print "is Android"
            else:
                print "unrecognized sqlite format"
        elif extension == ".xml":
            print "Importing texts from backup XML file"
            new_texts = readTextsFromXML( file )
        texts += new_texts
        print "finished in {0} seconds, {1} messages read".format( (time.time()-starttime), len(new_texts) )
    

    print "sorting all {0} texts by date".format( len(texts) )
    texts = sorted(texts, key=lambda text: text.date)
    
    if os.path.splitext(args.outfile)[1] == '.db':
        print "Saving changes into Android DB, "+str(args.outfile)
        exportAndroidSQL(texts, args.outfile)
    elif os.path.splitext(args.outfile)[1] == '.xml':
        print "Saving changes into XML, "+str(args.outfile)
        exportXML(texts, args.outfile)
    else:
        print "unrecognized output file."

class Text:
    def __init__( self, num, date, type, body):
        self.num  = num
        self.date = date
        self.type = type
        self.body = body
    def __str__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

def cleanNumber(numb):
    if not numb:
        return False
    stripped = ''.join(ch for ch in numb if ch.isalnum())
    if not stripped.isdigit():
        return False
    return stripped[-10:]

## Import functions ##

def readTextsFromIOS6(file):
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
        if sms_debug and i > 80:
            return
        i+=1
        txt = Text(row[0],long((row[1] + 978307200)*1000),(row[2]+1),row[3])
        texts.append(txt)
        if sms_debug:
            print txt
    return texts
    
def readTextsFromGV(file):
    conn = sqlite3.connect(file)
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
        txt = Text(row[4],long(ttime*1000),(row[2]+1),row[3])
        texts.append(txt)
    return texts

def readTextsFromIOS5(file):
    conn = sqlite3.connect(file)
    c = conn.cursor()
    i=0
    texts = []
    contactLookup = {}
    query = c.execute(
        'SELECT is_madrid, madrid_handle, address, date, text, madrid_date_read, flags FROM message;')
    for row in query:
        if row[0]:
            txt = Text( row[1], long((row[3] + 978307200)*1000), (row[5]==0)+1, row[4])
        else:
            from_me = row[6] & 0x01
            txt = Text( row[2], long(row[3]*1000), from_me+1, row[4])

        lookup_num = str(txt.num)[-10:]
        if not lookup_num in contactLookup:
            contactLookup[lookup_num] = i
        txt.cid = contactLookup[lookup_num]
        texts.append(txt)
        
        i+=1
    return texts

def readTextsFromXML(file):
    texts = []
    dom = xml.dom.minidom.parse(file)
    i = 0
    for sms in dom.getElementsByTagName("sms"):
        txt = Text( sms.attributes['address'].value, sms.attributes['date'].value,
                sms.attributes['type'].value, sms.attributes['body'].value)
        texts.append(txt)
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
        txt = Text(
                row[phNumberIndex], #number
                long(float(dateutil.parser.parse(row[dateIndex]).strftime('%s.%f'))*1000), #date
                (2 if row[typeIndex]=='0' else 1), #type
                row[bodyIndex] ) #body
        texts.append(txt)
        i += 1
    return texts
    
def getDbTableNames(file):
    cur = sqlite3.connect(file).cursor()
    names = cur.execute("SELECT name FROM sqlite_master WHERE type='table'; ")
    names = [name[0] for name in names]
    cur.close()
    return names

## Export functions ##

def exportAndroidSQL(texts, outfile):
    #open resources
    conn = sqlite3.connect(outfile)
    c = conn.cursor()

    #populate fast lookup table:
    contactIdFromNumber = {}
    query = c.execute('SELECT _id,address FROM canonical_addresses;')
    for row in query:
        contactIdFromNumber[cleanNumber(row[1])] = row[0]

    #start the main loop through each message
    i=0
    lastSpeed=0
    lastCheckedSpeed=0
    starttime = time.time()
    
    for txt in texts:
        if sms_debug and i > 80:
            break #sms_debug breaks early
        
        clean_number = cleanNumber(txt.num)
    
        #add a new canonical_addresses lookup entry and thread item if it doesn't exist
        if not clean_number in contactIdFromNumber:
            c.execute( "INSERT INTO canonical_addresses (address) VALUES (?)", [txt.num])
            contactIdFromNumber[clean_number] = c.lastrowid
            c.execute( "INSERT INTO threads (recipient_ids) VALUES (?)", [contactIdFromNumber[clean_number]])
        contact_id = contactIdFromNumber[clean_number]

        #now update the conversation thread (happends with each new message)
        c.execute( "UPDATE threads SET message_count=message_count + 1,snippet=?,'date'=? WHERE recipient_ids=? ", [txt.body,txt.date,contact_id] )
        c.execute( "SELECT _id FROM threads WHERE recipient_ids=? ", [contact_id] )
        thread_id = c.fetchone()[0]
        
        if sms_debug:
            print "thread_id = "+ str(thread_id)
            c.execute( "SELECT * FROM threads WHERE _id=?", [contact_id] )
            print "updated thread: " + str(c.fetchone())
            print "adding entry to message db: " + str([txt.num,txt.date,txt.body,thread_id,txt.type])
        
        #add message to sms table
        c.execute( "INSERT INTO sms (address,'date',body,thread_id,read,type,seen) VALUES (?,?,?,?,1,?,1)", [txt.num,txt.date,txt.body,thread_id,txt.type])
    
        #print status (with fancy speed calculation)
        recalculate_every = 100
        if i%recalculate_every == 0:
            lastSpeed = int(recalculate_every/(time.time() - lastCheckedSpeed))
            lastCheckedSpeed = time.time()
        sys.stdout.write( "\rprocessed {0} entries, {1} convos, ({2} entries/sec)".format(i, len(contactIdFromNumber), lastSpeed ))
        sys.stdout.flush()
        i += 1

    print "\nfinished in {0} seconds (average {1}/second)".format((time.time() - starttime), int(i/(time.time() - starttime)))

    if sms_debug:
        print "\n\nthreads: "
        for row in c.execute('SELECT * FROM threads'):
            print row

    if not test_run and not sms_debug:
        conn.commit()
        print "changes saved to "+outfile

    c.close()
    conn.close()

def exportXML(texts, outfile):
    doc = xml.dom.minidom.Document()
    doc.encoding = "UTF-8"
    smses = doc.createElement("smses")
    smses.setAttribute("count", str(len(texts)))
    doc.appendChild(smses)
    i=0
    for txt in texts:
        sms = doc.createElement("sms")
        #toa="null" sc_toa="null" service_center="null" read="1" status="-1" locked="0" date_sent="0" readable_date="Sep 27, 2012 10:57:55 AM" contact_name="Kevin Donlon"
        sms.setAttribute("address", str(txt.num))
        sms.setAttribute("date", str(txt.date))
        sms.setAttribute("type", str(txt.type))
        sms.setAttribute("body", txt.body)
        #useless things:
        sms.setAttribute("read", "1")
        sms.setAttribute("protocol", "0")
        sms.setAttribute("status", "-1")
        sms.setAttribute("locked", "0")
        smses.appendChild(sms)
        if (test_run or sms_debug) and i > 50:
            break
        i += 1
    if (test_run or sms_debug):
        print "xml output: (cut short to 50 items and not written)"
        print doc.toprettyxml(indent="  ", encoding="UTF-8")
    else:
        open(outfile, 'w').write(doc.toprettyxml(indent="  ", encoding="UTF-8"))
    

if __name__ == '__main__':
    sms_main()