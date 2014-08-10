# -*- coding: utf-8 -*-
import sqlite3, random, os, sys, time
import core, android, xmlmms, tabular, ios5, ios6, ios7, jsoner, googlevoice
from sms_exceptions import *

OUTPUT_TYPE_CHOICES = {
    'android': android.Android,
    'xml': xmlmms.XMLmms,
    'csv': tabular.Tabular,
    'ios5': ios5.IOS5,
    'ios6': ios6.IOS6,
    'ios7': ios7.IOS7,
    'json': jsoner.JSONer,
}

EXTENTION_TYPE_DEFAULTS = {
    '.db': 'android',
    '.json': 'json',
    '.xml': 'xml',
    '.csv': 'csv',
}

class Text:
    def __init__( self, num, date, incoming, body):
        self.num  = num
        self.date = date
        self.incoming = incoming
        self.body = body
    def __str__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

def readTextsFromFile(file):
    starttime = time.time() #meause execution time
    parser = getParser(file)
    if os.path.splitext(file.name)[1] == ".db":
        file.close()
    new_texts = parser.parse(file.name)
    print "{0} messages read in {1} seconds from {2}".format(len(new_texts), (time.time()-starttime), file.name)
    return new_texts


def getParser(file):
    extension = os.path.splitext(file.name)[1]
    if extension == ".csv":
        return csv.CSV()
    elif extension == ".db" or extension == ".sqlite":
        file.close()
        tableNames = core.getDbTableNames( file.name )
        if "handle" in tableNames:
            return ios6.IOS6()
        elif "group_member" in tableNames:
            return ios5.IOS5()
        elif "TextMessage" in tableNames:
            return googlevoice.GoogleVoice()
        elif "sms" in tableNames:
            return android.Android()
    elif extension == ".xml":
        return xmlmms.XMLmms()
    raise UnrecognizedDBError()


def getTestTexts():
    ENCODING_TEST_STRING = u'Δ, Й, ק, ‎ م, ๗, あ, 叶, 葉, and 말.'
    return [ Text("8675309", 1326497882355L, True, "Yo, what's up boo?"), \
        Text("+1(555)565-6565", 1330568484000L, False, "Goodbye cruel testing."),\
        Text("+1(555)565-6565", random.getrandbits(43), False, ENCODING_TEST_STRING)]



def getDbTableNames(file):
    cur = sqlite3.connect(file).cursor()
    names = cur.execute("SELECT name FROM sqlite_master WHERE type='table'; ")
    names = [name[0] for name in names]
    cur.close()
    return names
