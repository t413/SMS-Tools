Android-SMS-DB-importer
=======================

Import messages from Google Voice to your Android mmssms.db (requires adb root)

Get your old messages onto your android phone.

**Why?** Got a google voice account you're leaving behind? An iPhone you're moving away from? 

**Why this tool?** Other (still cool) backup tools like [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore)
run on the handset, they are terribly slow and fail to setup conversation threads correctly (in my experience). Use this from your laptop and push the new messages in seconds. 

Just run `python gv_to_android_sms.py --csv textmessages.csv mmssms.db`, sit back, and relax.

##Howto:

####Using iPhone
First you need the sms.db from your ***iOS 6*** phone. (haven't done iOS 5 and lower yet)
- (It's at `/private/var/mobile/Library/SMS/sms.db` on your phone if you've already have a jailbreak and know what you're doing.)
- Otherwise, this file is in the iTunes backup of your phone (no phone required!)
1. Open the right folder:
 - On Mac OS X open "~/Library/Application Support/MobileSync/Backup/"
 - On Windows 7/Vista open "C:\Users\[USERNAME]\AppData\Roaming\Apple Computer\MobileSync\Backup\"
2. Open the most recent folder.
3. Get the file named "3d0d7e5fb2ce288813306e4d4636395e047a3d28" and rename it to sms.db

Now run `python sms_db_importer.py -iphone sms.db mmssms.db` to populate the empty mmssms.db with your iPhone messages.

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
When I run this tool on my Google Voice data it processes 6675 entries into 149 convos in 15 seconds, which is 435 average entries/second. Not bad!



