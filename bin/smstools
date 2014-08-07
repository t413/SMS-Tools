# -*- coding: utf-8 -*-
import argparse, os, time
import core.android, core.googlevoice, core.tabular, core.jsoner
import core.ios5, core.ios6, core.ios7, core.xmlmms

OUT_TYPE_CHOICES = {
    'android': core.android.Android, 'xml': core.xmlmms.XMLmms,
    'csv': core.tabular.Tabular, 'ios5': core.ios5.IOS5,
    'ios6': core.ios6.IOS6, 'ios7': core.ios7.IOS7,
    'json': core.jsoner.JSONer,
}
EXT_TYPE_DEFAULTS = { '.db': 'android', '.json': 'json', '.xml': 'xml', '.csv': 'csv' }


def sms_main(infiles, outfile, outtype):

    if outtype:
        outtype = OUT_TYPE_CHOICES[outtype]
    else:
        extension = os.path.splitext(outfile.name)[1]
        if extension in EXT_TYPE_DEFAULTS:
            outtype = OUT_TYPE_CHOICES[EXT_TYPE_DEFAULTS[extension]]
        else:
            raise Exception("unknown output format (use --type argument)")

    #get the texts into memory
    texts = []
    for file in infiles:
        texts.extend(readTextsFromFile(file))

    print "sorting all {0} texts by date".format( len(texts) )
    texts = sorted(texts, key=lambda text: text.date)

    outtype().write(texts, outfile)


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
        return core.csv.CSV()
    elif extension == ".db" or extension == ".sqlite":
        file.close()
        tableNames = core.core.getDbTableNames( file.name )
        if "handle" in tableNames:
            return core.ios6.IOS6()
        elif "group_member" in tableNames:
            return core.ios5.IOS5()
        elif "TextMessage" in tableNames:
            return core.googlevoice.GoogleVoice()
        elif "sms" in tableNames:
            return core.android.Android()
        else:
            raise Exception("unrecognized sqlite format")
    elif extension == ".xml":
        return core.xmlmms.XMLmms()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import texts to android sms database file.')
    parser.add_argument('infiles', nargs='+', type=argparse.FileType('r'), help='input files, may include multiple sources')
    parser.add_argument('outfile', type=argparse.FileType('w'), help='output file to write to.')
    parser.add_argument('--type', type=str, help='output type', choices=OUT_TYPE_CHOICES.keys())
    try:
        args = parser.parse_args()
    except IOError:
        print "Problem opening file."
        quit()

    sms_main(args.infiles, args.outfile, args.type)
