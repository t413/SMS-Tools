Android-SMS-DB-importer
=======================

Import messages from Google Voice to your Android mmssms.db (requires adb root)

Get your old messages onto your android phone.

**Why?** Got a google voice account you're leaving behind? An iPhone you're moving away from? 

**Why this tool?** Other (still cool) backup tools like [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore)
run on the handset, they are terribly slow and fail to setup conversation threads correctly (in my experience). Use this from your laptop and push the new messages in seconds. 

Just run `python gv_to_android_sms.py textmessages.csv mmssms.db`, sit back, and relax.

##Howto:
First get your contacts. 
####Using Google voice
Use [googlevoice-to-sqlite](http://code.google.com/p/googlevoice-to-sqlite/) to create a csv file of your messages. ([direct link to .py file](http://googlevoice-to-sqlite.googlecode.com/svn/trunk/googlevoice_to_sqlite/googlevoice_to_sqlite.py)) 
You'll have to edit that file to make it mac/unix/linux compatable. Perhaps I'll fork that tool it here eventually. Run it, follow the prompts, and choose to export to CSV.

####Using iPhone / other
If the CSV formate is the same then you're good to go. 
A tool to make this from iPhone's sms.db is in the works.

###Getting mmssms.db from your phone
You're going to need [ADB](http://developer.android.com/tools/help/adb.html) which is in android-sdk/platform-tools/adb and likely already in your path. Just run:
`adb root; adb remount; adb pull /data/data/com.android.providers.telephony/databases/mmssms.db ./;`
To get mmssms.db in your current directory.

###Running
Given that textmessages.csv was produced by the `googlevoice-to-sqlite` tool and mmssms.db is from your phone, 
Run `python gv_to_android_sms.py textmessages.csv mmssms.db` and it will add all messages to mmssms.db.

###Uploading the results
`adb push mmssms.db /data/data/com.android.providers.telephony/databases/mmssms.db`

##My results
When I run this tool on my Google Voice data it processes 6675 entries into 149 convos in 15 seconds, which is 435 average entries/second. Not bad!



