import argparse, os, sys, time, dateutil.parser, sqlite3
sms_debug = False
test_run = False #test = don't save results

def sms_main():
    parser = argparse.ArgumentParser(description='Import texts to android sms database file.')
    parser.add_argument('infiles', nargs='+', type=argparse.FileType('r'), help='input files, may include multiple sources')
    parser.add_argument('outfile', type=str, help='output mmssms.db file use. Must alread exist.')
    parser.add_argument('--verbose', '-v', action='store_true', dest='sms_debug', help='sms_debug run: extra info, limits to 80, no save.')
    parser.add_argument('--test', '-t', action='store_true', dest='test_run', help='Test run, no saving anything')
    parser.add_argument('--limit', '-l', type=int, default=0, help='limit to the most recent n messages')
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
                new_texts = readTextsFromAndroid(file. name)
            else:
                print "unrecognized sqlite format"
        elif extension == ".xml":
            print "Importing texts from backup XML file"
            new_texts = readTextsFromXML( file )
        texts += new_texts
        print "finished in {0} seconds, {1} messages read".format( (time.time()-starttime), len(new_texts) )


    print "sorting all {0} texts by date".format( len(texts) )
    texts = sorted(texts, key=lambda text: text.date)

    if args.limit > 0:
        print "saving only the last {0} messages".format( args.limit )
        texts = texts[ (-args.limit) : ]

    if os.path.splitext(args.outfile)[1] == '.db':
        print "Saving changes into Android DB, "+str(args.outfile)
        exportAndroidSQL(texts, args.outfile)
    elif os.path.splitext(args.outfile)[1] == '.xml':
        print "Saving changes into XML, "+str(args.outfile)
        exportXML(texts, args.outfile)
    else:
        print "unrecognized output file."




if __name__ == '__main__':
    sms_main()
