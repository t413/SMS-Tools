import xml.dom.minidom
from core import Text


class XMLmms:
    """ Android XML reader and writer """


    def parse(self, file):
        """ Parse XML file to Text[] """
        texts = []
        dom = xml.dom.minidom.parse(file)
        i = 0
        for sms in dom.getElementsByTagName("sms"):
            txt = Text( sms.attributes['address'].value, sms.attributes['date'].value,
                    (sms.attributes['type'].value==2), sms.attributes['body'].value)
            texts.append(txt)
        return texts

    def write(self, texts, outfile):
        """ write a Text[] to XML file """
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
            sms.setAttribute("type", str(txt.incoming+1))
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
