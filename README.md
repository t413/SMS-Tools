SMS Tools
=======================

Multipurpose import / export / merge tool for your text message history. (formally Android-SMS-DB-importer)

Now on [PyPi](https://pypi.python.org/pypi/SMSTools) (the python package index) and available using pip!
`pip install smstools` puts `smstools` in your path, you're ready to roll.

Convert your message history between:
- iOS 5, 6, and 7 databases directly (from backup or from your jailbroken phone directly)
- Android mmssms.db database (directly from phone)
- Android XML from the [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore) app
- CSV files
- JSON files
- google voice data dump (see more details below)

Get all of your old messages onto your android phone.

**Why?**
- Leaving Google Voice?
- Getting a new iPhone or Android phone?
- Want a searchable CSV, JSON, or XML file of your conversations?
- Want to move *all* your messages from your past into a new, date-sorted, database?

-----

##Howto:

Now on [PyPi](https://pypi.python.org/pypi/SMSTools) (the python package index) and available using pip!
`pip install smstools` puts `smstools` in your path, you're ready to roll.

```
usage: smstools [-h] [--type {xml,json,android,csv,ios5,ios7,ios6}]
                    infiles [infiles ...] outfile
```


##Where do I get my files from?

- iPhone:
 * Pull from your iTunes backup: See below!
 * If you're jailbroken: pull down `/private/var/mobile/Library/SMS/sms.db`
- Android:
 * mmssms.db pulled from your phone: See below!
 * [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore) to get an XML file of your messages.
- Google Voice: **Work in progress**


####Getting your iPhone messages from iTunes backup
1. Open the right folder:
 - On Mac OS X open "~/Library/Application Support/MobileSync/Backup/"
 - On Windows 7/Vista open "C:\Users\[USERNAME]\AppData\Roaming\Apple Computer\MobileSync\Backup\"
2. Open the most recent folder (the most recent backup)
3. Get the file named "3d0d7e5fb2ce288813306e4d4636395e047a3d28" and rename it to sms.db


####What is the Android mmssms.db file?
This is the sqlite file where your Android phone stores messages. To read or write it you'll need root. It's located at `/data/data/com.android.providers.telephony/databases/mmssms.db`

It may be possible to read it directly using ADB by running the adb pull command as `com.android.providers.telephony`. Otherwise use [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore) or something similar.

So why use this option?
- It's orders of magnitude faster. Perfect for load testing mms applications with different databases (why I created this)
- Much better database performance. After importing the output.xml file with SMSBackupRestore.apk my Messaging.apk was left completely unusable. SMSBackupRestore is great, but it doesn't handle tens of thousands of messages.


##My results
When I run this tool on my Google Voice data it processes **6675** messages into **149 conversations** in **15 seconds**, which is 435 average entries/second. Not bad!


