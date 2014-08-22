# -*- coding: utf-8 -*-
import sqlite3, random, os, sys, time
import core, android, xmlmms, tabular, ios5, ios6, jsoner, googlevoice
from sms_exceptions import *

OUTPUT_TYPE_CHOICES = {
    'android': android.Android,
    'xml': xmlmms.XMLmms,
    'csv': tabular.Tabular,
    'ios5': ios5.IOS5,
    'ios6': ios6.IOS6,
    'json': jsoner.JSONer,
}

EXTENTION_TYPE_DEFAULTS = {
    '.db': 'android',
    '.json': 'json',
    '.xml': 'xml',
    '.csv': 'csv',
}

class Text:
    def __init__( self, **kwargs):
        requiredArgs = ['num', 'date', 'incoming', 'body']
        noneDefaultArgs = ['chatroom', 'members']

        for arg in requiredArgs:
            if not arg in kwargs: raise Exception("Required argument '%s' missing" % arg)
        vars(self).update(kwargs)
        for arg in noneDefaultArgs:
            if not arg in vars(self): vars(self)[arg] = None
    def localStringTime(self):
        return time.strftime("%Y-%m-%d %I:%M:%S %p %Z", time.localtime(long(self.date)/1000))
    def __str__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.__dict__ == other.__dict__


def getParser(filepath):
    extension = os.path.splitext(filepath)[1]
    if extension == ".csv":
        return csv.CSV()
    if extension == ".json":
        return jsoner.JSONer()
    elif extension == ".db" or extension == ".sqlite":
        try:
            tableNames = core.getDbTableNames( filepath )
        except:
            raise UnrecognizedDBError("Error reading from %s" % filepath)
        if "handle" in tableNames:
            return ios6.IOS6()
        elif "group_member" in tableNames:
            return ios5.IOS5()
        elif "TextMessage" in tableNames:
            return googlevoice.GoogleVoice()
        elif "sms" in tableNames:
            return android.Android()
        print term.red_on_black("unrecognized database details and structure:")
        print getDbInfo( file.name )
        raise UnrecognizedDBError("Unknown sqlite database: [%s]" % os.path.basename(filepath))
    elif extension == ".xml":
        return xmlmms.XMLmms()
    raise UnrecognizedDBError("Unknown extension %s" % extension)


def cleanNumber(numb):
    if not numb: return False
    if '@' in numb: return numb #allow email addresses
    stripped = ''.join(ch for ch in numb if ch.isalnum())
    if not stripped.isdigit():
        return False
    return stripped[-10:]


def getDbTableNames(file):
    cur = sqlite3.connect(file).cursor()
    names = [name[0] for name in cur.execute("SELECT name FROM sqlite_master WHERE type='table'; ")]
    cur.close()
    return names





####  Tools and utilities  ####

def getVersion():
    try:
        import pkg_resources
        return pkg_resources.get_distribution("smstools").version
    except:
        return "unknown version"

def truncate(text, leng=75):
    return (text[:leng] + ' ..') if len(text) > 75 else text

def getColorLibrary():
    try:
        import blessings
        return blessings.Terminal() # nice terminal color library
    except:
        print "install 'blessings' module for great terminal output color"
        class CatchAllPassthrough:
            def __getattr__(self, name): return str
        return CatchAllPassthrough()

term = getColorLibrary()

def warning(string):
    print core.term.magenta_on_black("WARNING: ") + string


####  Common Testing functions  ####

def getTestTexts():
    ENCODING_TEST_STRING = u'Δ, Й, ק, ‎ م, ๗, あ, 叶, 葉, and 말.'
    return [ Text(num="8675309", date=1326497882355L, incoming=True, body="Yo, what's up boo?"), \
        Text(num="+1(555)565-6565", date=1330568484000L, incoming=False, body="Goodbye cruel testing."),\
        Text(num="+1(555)565-6565", date=random.getrandbits(43), incoming=False, body=ENCODING_TEST_STRING)]


def compareTexts(t1, t2,
        throw_errors=True,
        required_attrs=['num', 'incoming', 'body', 'date']):
    mismatched = []
    for att in required_attrs:
        if t1.__dict__[att] != t2.__dict__[att]:
            if throw_errors:
                raise Exception("Text[%s] vals <%s =! %s> in <%s> and <%s>"
                    % (att, t1.__dict__[att], t2.__dict__[att], t1, t2))
            mismatched.append(att)
    warn_attrs = list((set(t1.__dict__.keys()) | set(t2.__dict__.keys())) - set(required_attrs))
    for att in warn_attrs:
        if (not att in t1.__dict__) or (not att in t2.__dict__):
            mismatched.append(att)
        elif t1.__dict__[att] != t2.__dict__[att]:
            mismatched.append(att)
    return mismatched

def getDbInfo(file):
    outs = ""
    try:
        cur = sqlite3.connect(file).cursor()
        names = [name[0] for name in cur.execute("SELECT name FROM sqlite_master WHERE type='table'; ")]
    except:
        outs += "file %s not sqlite\n" % file
        return
    tab_count = [(table, cur.execute("SELECT Count() FROM %s" % table).fetchone()[0]) for table in names]

    if len(names): outs += " tables in %s:\n" % os.path.basename(file)
    for table in sorted(tab_count, key=lambda tup: -tup[1]):
        colnames = [x[1] for x in cur.execute("PRAGMA table_info(%s)" % table[0]).fetchall()]
        outs += " - %s (%i items): (%s)\n" % (table[0], table[1], colnames)
    cur.close()
    return outs

