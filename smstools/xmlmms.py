import xml.dom.minidom
import core

class XMLmms:
    """ Android XML reader and writer """


    def parse(self, filepath):
        """ Parse XML file to Text[] """
        texts = []
        with open(filepath, 'r') as file:
            dom = xml.dom.minidom.parse(file)
            i = 0
            for sms in dom.getElementsByTagName("sms"):
                txt = core.Text( num=sms.attributes['address'].value, date=sms.attributes['date'].value,
                        incoming=(sms.attributes['type'].value==2), body=sms.attributes['body'].value)
                texts.append(txt)
            return texts

    def write(self, texts, outfilepath):
        """ write a Text[] to XML file """
        doc = xml.dom.minidom.Document()
        doc.encoding = "UTF-8"
        smses = doc.createElement("smses")
        smses.setAttribute("count", str(len(texts)))
        doc.appendChild(smses)
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
            # print doc.toprettyxml(indent="  ", encoding="UTF-8")
        print "generating xml output"
        xmlout = doc.toprettyxml(indent="  ", encoding="UTF-8")
        with open(outfilepath, 'w') as outfile:
            outfile.write(xmlout)
