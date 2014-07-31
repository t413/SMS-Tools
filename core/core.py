# -*- coding: utf-8 -*-
import sqlite3, random

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
