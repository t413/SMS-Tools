import argparse, sys, time, dateutil.parser, sqlite3, csv

parser = argparse.ArgumentParser(description='Import texts to android sms database file.')
parser.add_argument('infile', type=argparse.FileType('r'), help='input CSV file')
parser.add_argument('outfile', type=str, help='output mmssms.db file use. Must alread exist.')
parser.add_argument('-d', action='store_true', default=False, dest='debug', help='extra info')
args = parser.parse_args()

#open resources
conn = sqlite3.connect(args.outfile)
c = conn.cursor()
inreader = csv.reader( args.infile )

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

#start the main loop through each message
i=2
lastSpeed=0
lastCheckedSpeed=0
starttime = time.time()
convoMap = {}

for row in inreader:
    if args.debug and i > 80:
        break #debug breaks early
    
    #get all needed information from the row
    mdate   = long(float(dateutil.parser.parse(row[dateIndex]).strftime('%s.%f'))*1000)
    pnumber = row[phNumberIndex]
    outtype = 2 if row[typeIndex]=='0' else 1
    body    = row[bodyIndex]
    conctId = row[cidIndex]
    
    #add a new conversation thread entry (and canonical_addresses lookup entry) if it doesn't exist
    if not conctId in convoMap:
        c.execute( "INSERT INTO canonical_addresses (address) VALUES (?)", [pnumber])
        contact_id = c.lastrowid
        c.execute( "INSERT INTO threads (recipient_ids) VALUES (?)", [contact_id])
        convoMap[conctId] = c.lastrowid
    
    #now update conversation thread (assuming it was just created or existed before)
    thread_id = convoMap[conctId]
    c.execute( "UPDATE threads SET message_count=message_count + 1,snippet=?,'date'=? WHERE _id=? ", [body,mdate,thread_id] )
    if args.debug:
        c.execute( "SELECT * FROM threads WHERE _id=?", [thread_id] )
        print "updated thread: " + str(c.fetchone())
    
    if args.debug:
        print "adding entry to message db: " + str([pnumber,mdate,body,thread_id,outtype])
    #add message to sms table
    c.execute( "INSERT INTO sms (address,'date',body,thread_id,read,type,seen) VALUES (?,?,?,?,1,?,1)", [pnumber,mdate,body,thread_id,outtype])
    
    #print status
    if i%100 == 0:
        lastSpeed = int(100/(time.time() - lastCheckedSpeed))
        lastCheckedSpeed = time.time()
    sys.stdout.write( "\rprocessed {0} entries, {1} convos, ({2} entries/sec)".format(i, len(convoMap), lastSpeed ))
    sys.stdout.flush()
    
    i += 1



print "\nfinished in {0} seconds (average {1}/second)".format((time.time() - starttime), int(i/(time.time() - starttime)))

if args.debug:
    print "\n\nthreads: "
    for row in c.execute('SELECT * FROM threads'):
        print row


if not args.debug:
    conn.commit()
    print "changes saved to "+args.outfile

c.close()
conn.close()
