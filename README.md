Android-SMS-DB-importer
=======================

Multipurpose import / export / merge tool for your text message history.

Import data from:
- iOS 5 databases, iMessages and all
- iOS 6 databases
- Android XML from the [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore) app
- CSV of google voice data, created using [googlevoice-to-sqlite](http://code.google.com/p/googlevoice-to-sqlite/) (see below)

Save to:
- XML format for use with [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore) app
- mmssms.db Android sms database format

Get all of your old messages onto your android phone.

**Why?** Got a google voice account you're leaving behind? An iPhone you're moving away from? 

####Why use mmssms.db format? It requires root!
Yes, getting this file from your android phone requires root access. If you're a developer and have the [android developer tools](http://developer.android.com/tools/help/adb.html) and have `adb root` access (because you're using a userdebug build *like me*) then you're set. [CyanogenMod](http://www.cyanogenmod.com/) is rooted by default and **already supports** adb root.

So why use this option? 
- It's orders of magnitude faster. Perfect for load testing mms applications with different databases (what I'm doing, sortof)
- Much better database performance. After importing the output.xml file with SMSBackupRestore.apk my Messaging.apk was left completely unusable. SMSBackupRestore is great, but it doesn't handle tens of thousands of messages.


##Howto:

Just run `hon sms_db_importer.py  sms-iOS-5.db gv.csv android.xml  out.db`, sit back, and relax.

```
usage: sms_db_importer.py [-h] [-d] [-t] infiles [infiles ...] outfile

Import texts to android sms database file.

positional arguments:
  infiles     input files, may include multiple sources 
               *.csv -> Google Voice csv exported with [googlevoice-to-sqlite](http://code.google.com/p/googlevoice-to-sqlite/)
               *.xml -> [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore)XML format.
               *.db  -> Autodetected iPhone iOS5 or iOS6 format.
  outfile     output mmssms.db file use. Must alread exist.
                *.xml -> [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore)XML format.
                *.db  -> Android mmssms.db sqlite format

optional arguments:
  -h, --help  show this help message and exit
  -d          sms_debug run: extra info, limits to 80, no save.
  -t          Test run, no saving anything
```

####Using iPhone
First you need the sms.db from your phone.
- (It's at `/private/var/mobile/Library/SMS/sms.db` on your phone if you've already have a jailbreak and know what you're doing.)
- Otherwise, this file is in the iTunes backup of your phone (no phone required!)
1. Open the right folder:
 - On Mac OS X open "~/Library/Application Support/MobileSync/Backup/"
 - On Windows 7/Vista open "C:\Users\[USERNAME]\AppData\Roaming\Apple Computer\MobileSync\Backup\"
2. Open the most recent folder.
3. Get the file named "3d0d7e5fb2ce288813306e4d4636395e047a3d28" and rename it to sms.db

Now run `python sms_db_importer.py -iphone sms.db` **mmssms.db** to populate the empty mmssms.db with your iPhone messages.

####Using Google voice
Use Google's Takeout service to migrate to Android! Use [googlevoice-to-sqlite](http://code.google.com/p/googlevoice-to-sqlite/) to create a csv file of your messages. ([direct link to .py file](http://googlevoice-to-sqlite.googlecode.com/svn/trunk/googlevoice_to_sqlite/googlevoice_to_sqlite.py)) 

You'll have to edit that file to make it mac/unix/linux compatable. Perhaps I'll fork that tool it here eventually. Run it, follow the prompts, and choose to export to CSV.

Now run `python sms_db_importer.py -csv textmessages.csv mmssms.db` to populate the empty mmssms.db with your Google Voice Takeout messages.


###Optional: Getting mmssms.db from your phone
I've included an empty mmssms.db one can fill with your new data. If you want to add to an existing mmssms.db:
You're going to need [ADB](http://developer.android.com/tools/help/adb.html) which is in android-sdk/platform-tools/adb and likely already in your path. Just run:
`adb root; adb remount; adb pull /data/data/com.android.providers.telephony/databases/mmssms.db ./;`
To get mmssms.db in your current directory.


###Uploading the results
`adb push mmssms.db /data/data/com.android.providers.telephony/databases/mmssms.db`

##My results
When I run this tool on my Google Voice data it processes **6675** messages into **149 conversations** in **15 seconds**, which is 435 average entries/second. Not bad!


