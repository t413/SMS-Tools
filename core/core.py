import sqlite3

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




def getDbTableNames(file):
    cur = sqlite3.connect(file).cursor()
    names = cur.execute("SELECT name FROM sqlite_master WHERE type='table'; ")
    names = [name[0] for name in names]
    cur.close()
    return names
