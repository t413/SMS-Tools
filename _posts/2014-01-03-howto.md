---
title: "howto"
bg: turquoise
color: white
fa-icon: laptop
---

### [github project page!]({{ site.source_link }})

-------------------------
{: .border-white}

##Howto:

Now on [PyPi](https://pypi.python.org/pypi/SMSTools) (the python package index) and available using pip!
`pip install smstools` puts `smstools` in your path, you're ready to roll.

```
usage: smstools [-h] [--type {xml,json,android,csv,ios5,ios7,ios6}]
                    infiles [infiles ...] outfile
```


-------------------------
{: .border-white}


##Where do I get my files from?

- iPhone:
  * Pull from your iTunes backup: See below!
  * If you're jailbroken: pull down `/private/var/mobile/Library/SMS/sms.db`
    {: .circle}
- Android:
  * mmssms.db pulled from your phone: See below!
  * [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore) to get an XML file of your messages.
    {: .circle}
- Google Voice: **Work in progress**
{: .square}

#### **Getting your iPhone messages from iTunes backup**
{: .left}

1. Open the right folder:
  - On Mac OS X open "~/Library/Application Support/MobileSync/Backup/"
  - On Windows 7/Vista open "C:\Users\[USERNAME]\AppData\Roaming\Apple Computer\MobileSync\Backup\"
    {: .square}
2. Open the most recent folder (the most recent backup)
3. Get the file named "3d0d7e5fb2ce288813306e4d4636395e047a3d28" and rename it to sms.db


#### **What is the Android mmssms.db file?**
{: .left}

This is the sqlite file where your Android phone stores messages. To read or write it you'll need root. It's located at `/data/data/com.android.providers.telephony/databases/mmssms.db`

It may be possible to read it directly using ADB by running the adb pull command as `com.android.providers.telephony`. Otherwise use [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore) or something similar.

So why use this option?
- It's orders of magnitude faster. Perfect for load testing mms applications with different databases (why I created this)
- Much better database performance. After importing the output.xml file with SMSBackupRestore.apk my Messaging.apk was left completely unusable. SMSBackupRestore is great, but it doesn't handle tens of thousands of messages.

