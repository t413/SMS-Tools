'''
googlevoice_to_sqlite.py
This file houses the main execution routine

Created on Sep 9, 2011

@author: Arithmomaniac

'''
import time, sys, os, datetime, argparse
import re, atexit
import xml.etree.ElementTree
from copy import deepcopy
from dateutil import tz
from dateutil.parser import *
import htmlentitydefs
import sqlite3, csv, codecs
import core



#the classes of GVoice objects

#Contacts
class Contact:
    __slots__ = ['name', 'phonenumber']
    def __init__(self):
        self.phonenumber = None
        self.name = None
    def dump(self): #debug info
        return "%s (%s)" % (self.name, self.phonenumber)
    def test(self): #if has values
        return self.phonenumber != None or self.name != None

#Text message
class Text:
    __slots__ = ['contact', 'date', 'text']
    def __init__(self):
        self.contact = Contact()
        self.date = None
        self.text = None
    def dump(self):
        return "%s; %s; \"%s\"" % (self.contact.dump(), self.date, self.text)

#Text "conversation"; the outer container for grouped texts (they are stored in HTML this way, too)
class TextConversation:
    __slots__ = ['contact', 'texts']
    def __init__(self):
        self.contact = Contact()
        self.texts = []
    def dump(self):
        returnstring = self.contact.dump()
        for i in self.texts:
            returnstring += "\n\t%s" % i.dump()
        return returnstring

#A phone call
class Call:
    __slots__ = ['contact', 'date', 'duration', 'calltype']
    def __init__(self):
        self.contact = Contact()
        self.date = None
        self.duration = None
        self.calltype = None #Missed, Placed, Received
    def dump(self):
        return "%s\n%s; %s(%s)" % (self.calltype, self.contact.dump(), self.date, self.duration)

class Audio:
    __slots__ = ['contact', 'audiotype', 'date', 'duration', 'text', 'confidence', 'filename']
    def __init__(self):
        self.contact = Contact()
        self.audiotype = None   #'Voicemail' or 'Recorded'
        self.date = None
        self.duration = None
        self.text = None        #the text of the recording/voicemail
        self.confidence = None  #confidence of prediction
        self.filename = None    #filename of audio file
    def dump(self):
        return "%s\n%s; %s(%s); [%s]%s" % (self.audiotype, self.contact.dump(), self.date, self.duration, self.confidence, self.text)
##---------------------------

#Parsing help functions

#from effbot.org. HTML unescape
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

#Parses a Gvoice-formatted date into a datetime object
def parse_date (datestring):
    returntime = parse(datestring).astimezone(tz.tzutc())
    return returntime.replace(tzinfo = None)


#Parses the "duration" tag into the number of seconds it encodes
def parse_time (timestring):
    #what does real pattern really mean
    timestringmatch = re.search('(\d\d+):(\d\d):(\d\d)', timestring)
    seconds = 0
    seconds += int(timestringmatch.group(3))
    seconds += int(timestringmatch.group(2)) * 60
    seconds += int(timestringmatch.group(1)) * 3600
    return seconds

#As the HTML has an XML namespace, it would need to be specified for every XPATH node. This automates that obnoxious step
def as_xhtml (path):
    return re.sub('/(?=\w)', '/{http://www.w3.org/1999/xhtml}', path)
##------------------------------------


#Gets a category label from the HTNL file
#TO DO: return Inbox, Starred flags
def get_label(node):
    labelNodes = node.findall(as_xhtml('./div[@class="tags"]/a[@rel="tag"]'))
    validtags = ('Placed', 'Received', 'Missed', 'Recorded', 'Voicemail') #Valid categories
    for i in labelNodes:
        label = i.findtext('.')
        if label in validtags:
            return label
    return None

#Finds the first contact contained within a node. Returns it
def find_Contact(node):
    contact_obj = Contact()

    #two places the node could be
    contactnode = node.find(as_xhtml('.//cite[@class="sender vcard"]/a[@class="tel"]'))
    if contactnode is None:
        contactnode = node.find(as_xhtml('.//div[@class="contributor vcard"]/a[@class="tel"]'))

    #name
    contact_obj.name = contactnode.findtext(as_xhtml('./span[@class="fn"]'))
    if contact_obj.name != None and len(contact_obj.name) == 0: #If a blank string. Should be an isinstance
        contact_obj.name = None
    #phone number
    contactphonenumber = re.search('\d+', contactnode.attrib['href'])
    if contactphonenumber != None:
        contact_obj.phonenumber = contactphonenumber.group(0)

    return contact_obj

def process_TextConversation(textnodes, onewayname): #a list of texts, and the title used in special cases
    text_collection = TextConversation()
    text_collection.texts = []
    for i in textnodes:
        textmsg = core.Text()
        textmsg.contact = find_Contact(i)
        if text_collection.contact.test() == False: #if we don't have a contact for this conversation yet
                if textmsg.contact.name != None:    #if contact not self
                    text_collection.contact = deepcopy(textmsg.contact)    #They are other participant
        textmsg.date =parse_date(i.find(as_xhtml('./abbr[@class="dt"]')).attrib["title"])
 #date
        textmsg.text = unescape(i.findtext(as_xhtml('./q'))) #Text. TO DO: html decoder
        text_collection.texts.append(deepcopy(textmsg))
        #newline
    if not text_collection.contact.test():  #Outgoing-only conversations don't contain the recipient's contact info.
        text_collection.contact.name = onewayname #Pull fron title. No phone number, but fixed in other finction
    return text_collection

#process phone calls. Returns Call object
def process_Call(audionode):
    call_obj = Call()
    call_obj.contact = find_Contact(audionode)
    #time
    call_obj.date = parse_date(audionode.find(as_xhtml('./abbr[@class="published"]')).attrib["title"])
    #duration
    duration_node = audionode.findtext(as_xhtml('./abbr[@class="duration"]'))
    if duration_node != None:
        call_obj.duration = parse_time(duration_node)
    #Call type (Missed, Recieved, Placed)
    call_obj.calltype = get_label(audionode)
    return call_obj

#Processes voicemails, recordings
def process_Audio(audionode):
    audio_obj = Audio()
    audio_obj.contact = find_Contact(audionode)
    #time
    #duration
    audio_obj.duration = parse_time(audionode.findtext(as_xhtml('./abbr[@class="duration"]')))
    audio_obj.date = parse_date(audionode.find(as_xhtml('./abbr[@class="published"]')).attrib["title"]) - datetime.timedelta(0, audio_obj.duration)
    #print audio_obj.date
    #print audio_obj.duration
    descriptionNode = audionode.find(as_xhtml('./span[@class="description"]'))
    if descriptionNode != None and len(descriptionNode.findtext(as_xhtml('./span[@class="full-text"]'))) > 0:
        #fullText
        fullText = descriptionNode.findtext(as_xhtml('./span[@class="full-text"]')) #TO DO: html decoder
        if fullText != 'Unable to transcribe this message.':
            audio_obj.text = fullText
        #average confidence - read each confidence node (word) and average out results
        confidence_values = descriptionNode.findall(as_xhtml('./span/span[@class="confidence"]'))
        totalconfid = 0
        for i in confidence_values:
            totalconfid += float(i.findtext('.'))
        audio_obj.confidence = totalconfid / len(confidence_values)
    #location of audio file
    audio_obj.filename = audionode.find(as_xhtml('./audio')).attrib["src"]
    #label
    audio_obj.audiotype = get_label(audionode)
    return audio_obj

##-------------------

#The main function. Takes in the file name and an ElementTree
def process_file(tree, filename = None):
    #texts
    textNodes = tree.findall(as_xhtml('.//div[@class="hChatLog hfeed"]/div[@class="message"]'))
    if len(textNodes) > 0: #is actually a text file
        #process the text files
        obj = process_TextConversation(textNodes, re.match('(.*?)(?=_-_\d\d\d\d-\d\d-\d\dT\d\d-\d\d-\d\dZ)', filename).group(0))
    else:
        #look for call/audio
        audioNode = tree.find(as_xhtml('.//div[@class="haudio"]'))
        if audioNode.find(as_xhtml('./audio')) is None: #no audio enclosure. Just the call record
            obj = process_Call(audioNode)
        else: #audio
            obj = process_Audio(audioNode)
    return obj

###--------------------

class gvoiceconn(sqlite3.Connection):
    def __init__(self, path):
        open(path, 'w').close() #wipes file in same path, since old records cannot be relied upon (name changes, etc.)
        sqlite3.Connection.__init__(self, path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        #self = sqlite3.connect() #connect
        with open('googlevoice_to_sqlite_initdb.sql', 'r') as initdb:
            self.executescript(initdb.read()) #create data structures needed, ad defined in external file\
        #dictonoary to keep track of rowcount in each table
        self.rowcount = dict.fromkeys(('Contact', 'Audio', 'TextConversation', 'TextMessage', 'PhoneCall', 'Voicemail'), 0)
        self.unmatched_recordings = [] #recordings not matched to audio file

    #Returns the maximum primary key from a table
    #TO DO: handle locally as a dictionary instead
    def getmaxid(self, tablename):
        self.rowcount[tablename] += 1
        return self.rowcount[tablename]

    #imports a Contact object into the database
    def import_Contact(self, contact):
        if contact.name != None:
            contact.name = contact.name.replace('_', ' ') #zap underscores in names
        #sees if contact id for contact already exists
        contactid = self.execute('SELECT ContactID FROM Contact \
            WHERE (Name = ? OR COALESCE(Name,?) is NULL) \
            AND  (PhoneNumber = ? OR COALESCE(PhoneNumber,?) is NULL)',
            (contact.name, contact.name, contact.phonenumber, contact.phonenumber)).fetchone()
        if contactid != None: #if contact exists, that's all we need
            return contactid[0]
        else: #Contact ID will be new row we create
            contactid = self.getmaxid('Contact')
            self.execute('INSERT INTO Contact (ContactID, Name, PhoneNumber) VALUES (?, ?, ?)', (contactid, contact.name, contact.phonenumber))
            return contactid

    #Import text messages in a TextConversation into the database
    def import_TextConversation(self, text_conversation):
        contactid = self.import_Contact(text_conversation.contact) #get contact of conversation
        conversationid = self.getmaxid('TextConversation') #get ID of conversation... and insert it
        self.execute('INSERT INTO TextConversation (TextConversationID, ContactID) VALUES (?, ?)', (conversationid, contactid))
        for textmsg in text_conversation.texts:
            #insert each text Message into the TextMessage database
            self.execute ('INSERT INTO TextMessage (TextMessageID, TextConversationID, TimeRecordedUTC, Incoming, Text) VALUES (?, ?, ?, ?, ?)', (
                          self.getmaxid('TextMessage'),
                          conversationid,
                          textmsg.date,
                          0 if textmsg.contact.name == None else 1, #if None, means self
                          textmsg.text
                          ))

    #Import a Call object into the database
    def import_Call(self, callrecord):
        try:
            contactid = self.import_Contact(callrecord.contact)
            self.execute('INSERT INTO PhoneCall (PhoneCallID, ContactID, PhoneCallTypeID, TimeStartedUTC, Duration) VALUES (?, ?, ?, ?, ?)', (
                            self.getmaxid('PhoneCall'),
                            contactid,
                                #Proper type as defined in PhoneCallTypeID
                            self.execute('SELECT PhoneCallTypeID FROM PhoneCallType WHERE PhoneCallType = "%s"' % callrecord.calltype).fetchone()[0],
                            callrecord.date,
                            callrecord.duration
                        ))
        except:
            if callrecord.contact.name == 'Google Voice': #Intro go Google Voice - voicemail with no audio
                pass
            else:
                raise

    #imports Audio object into database
    def import_Audio(self, audiorecord, insert_unmatched_audio = True):
        contactid = self.import_Contact(audiorecord.contact)
        #only one of these foreign keys are ever used, but both are inserted. So init to null now
        voicemailid = None
        callid = None
        if(audiorecord.audiotype == 'Voicemail'): #if voicemail, update Voicemailt table and grab resulting ID
            voicemailid = self.getmaxid('Voicemail')
            self.execute('INSERT INTO Voicemail (VoicemailID, ContactID) VALUES (?, ?)', (voicemailid, contactid))
        else: #Guess what Call the recording is associated with. If exists, insert
            callidrow = self.execute(
                'select PhoneCallID from PhoneCall WHERE ContactID = ? and strftime("%s", ?) - strftime("%s", TimeStartedUTC) between 0 and Duration',
                (contactid, audiorecord.date)
                )
            if callidrow == None:
                self.unmatched_recordings += audiorecord
                if not insert_unmatched_audio:
                    return 1
            else:
                callid = callidrow.fetchone()[0]
        #Now that have foreign keys, insert audio into db
        self.execute(
            'INSERT INTO Audio (AudioID, PhoneCallID, VoicemailID, TimeStartedUTC, Duration, Text, Confidence, FileName) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (
             self.getmaxid('Audio'),
             callid,
             voicemailid,
             audiorecord.date,
             audiorecord.duration,
             audiorecord.text,
             audiorecord.confidence,
             audiorecord.filename
            ))
        return 0

    #Outgoing-only text conversations only display the name, but not the number. This tries to locate the right number
    #For a name from different correspondence
    #TO DO: Work on my-text basis instead of by-contact basis for better precision
    def fixnullrecords(self):
        #Get a list of null-phone-number contacts and the contacts with real phone numbers they match
        execstring = '''SELECT NullContacts.ContactID, CompleteContacts.ContactID FROM (
        SELECT DISTINCT Contact.ContactId, Name, PhoneNumber
        FROM Contact INNER JOIN %s ON Contact.ContactId = %s.ContactId WHERE PhoneNumber IS NOT NULL) AS CompleteContacts
        INNER JOIN ( SELECT ContactId, Name FROM Contact WHERE PhoneNumber IS NULL ) AS NullContacts
        ON NullContacts.Name = CompleteContacts.Name'''
        #Update text conversation with good contact, then throw away dud number
        for table in ('TextConversation', 'PhoneCall'): #First match to texts, then if no incoming texts, try calls
            for row in self.execute(execstring % (table, table)):
                self.executescript(
                    'UPDATE TextConversation SET ContactId = %d WHERE ContactId = %d; DELETE FROM Contact WHERE ContactId = %d;' \
                    % (row[1], row[0], row[0])
                )

    def exportcsv(self, outdir):
        views = [('contacts.csv', 'Contact')]
        views += ((str.lower(name) + 's.csv', 'flat' + name) for name in ('PhoneCall', 'TextMessage', 'Voicemail', 'Recording'))
        for view in views:
            query = self.execute('SELECT * FROM %s' % view[1])
            with open(outdir + view[0], 'wb') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow([i[0] for i in query.description])
                fetch = [[unicode( r ).encode("utf-8") for r in st] for st in query.fetchall()]
                csvwriter.writerows(fetch)


####-----------------

# a generator that returns the gvoice_parse object found in a file
def getobjs(path, encoding, force):
    files = os.listdir(path)
    for fl in files:
        if fl.endswith('.html'): #no mp3 files
            errorHandle = 'strict' if not force else 'replace'
            try:
                with codecs.open(os.path.join(path, fl), 'r', encoding, errors=errorHandle) as f: #read the file
                    tree = xml.etree.ElementTree.fromstring(f.read().replace('<br>', "\r\n<br />").encode("utf-8")) #read properly-formatted html
            except xml.etree.ElementTree.ParseError:
                print "\nproblem parsing " + str(fl)
                if not force: quit()
            except ValueError:
                print "\nproblem reading file {0} with encoding {1}".format(fl, encoding)
                print "Try using a different encoding or use --force"
                if not force: quit()
            record = None #reset the variable
            record = process_file(tree, fl) #do the loading
            if record != None:
                yield (fl, record) #return record and name


#a line-overwriting suite.
class LineWriter(object):
    def __init__(self, outfile=sys.stdout, flush=True):
        self.flush = flush
        self.lastlen = None #the length of the last line
        self.outfile = outfile

    def __del__(self):
        self.newline() #make sure that on new line when done

    def write(self, command): #overwrite contents on current line
        currlen = len(command)
        if currlen < self.lastlen: #if we're not going to completely overwrite the last line
            self.wipe() #wipe it
        self.outfile.write('\r%s' % command) #go back to beginning of line and write
        self.lastlen = currlen #then save new value of lastlen
        if self.flush:
            self.outfile.flush()

    def wipe(self):
        self.write(''.rjust(self.lastlen)) #overwrite with blank values
        self.lastlen = None #no content on line anymore

    def newline(self):
        self.lastlen = None #new line, so no need to care about overwriting
        self.write('\r\n') #write the line

#main execution routine
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Google Voice to sqlite and csv')
    parser.add_argument('indir', help='input directory (ends with Voice/Calls/)')
    parser.add_argument('outfile', nargs='?', default="gvoice.sqlite")
    parser.add_argument('--csv', default=False, help="directory to save csvs of messages")
    parser.add_argument('--encoding', default="latin_1", help="spesify input file encoding")
    parser.add_argument('--force', action='store_true', help="force skip errors")
    args = parser.parse_args()

    #grab location. Allow quoted paths. Default to "brother" conversation directory
    conversationlocation = args.indir
    if not conversationlocation:
        conversationlocation = '../conversations'
    gvconn = gvoiceconn( args.outfile ) #connect to sql database
    atexit.register( gvconn.commit )  #save it exited early by user
    unmatched_audio = []
    listline = LineWriter()
    try:
        for i in getobjs(conversationlocation, args.encoding, args.force): #load each file into db, depending on type
            listline.write(i[0]) #write filename to console
            record = i[1]
            if isinstance(record, TextConversation): #set of text messages
                gvconn.import_TextConversation(record)
            elif isinstance(record, Call): #call
                gvconn.import_Call(record)
            elif isinstance(record, Audio): #voicemail/recording
                if gvconn.import_Audio(record, False) == 1: #no contact for audio. Can happen if files have been renamed
                    unmatched_audio += record #save second pass for later
        del listline
        for i in unmatched_audio: #not make second pass on unmatched audio
            gvconn.import_Audio(i)
            i = None
        gvconn.fixnullrecords() #fixed bad contacts - see there for description
        gvconn.commit()
    except:
        gvconn.commit()
        raise
    if args.csv :
        path = (args.csv) if args.csv[-1] == os.sep else (args.csv + os.sep)
        if not os.path.exists( path ):
            os.mkdir( path )
        gvconn.exportcsv( path )
        print 'CSVs created.'

