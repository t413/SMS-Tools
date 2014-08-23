import os, sys, time, sqlite3
import core, sms_exceptions

class Android:
    """ Android sqlite reader and writer """


    def parse(self, filepath):
        """ Parse a sqlite file to Text[] """

        db = sqlite3.connect(filepath)
        cursor = db.cursor()
        texts = self.parse_cursor(cursor)
        cursor.close()
        db.close()
        return texts

    def parse_cursor(self, cursor):
        texts = []
        query = cursor.execute(
            'SELECT address, date, type, body \
             FROM sms \
             ORDER BY _id ASC;')
        for row in query:
            txt = core.Text(num=row[0],date=long(row[1]),incoming=(row[2]==2),body=row[3])
            texts.append(txt)
        return texts

    def write(self, texts, outfilepath):
        """ write a Text[] to sqlite file """
        print "Creating empty Android SQLITE db"
        conn = sqlite3.connect(outfilepath)
        conn.executescript(INIT_DB_SQL)
        cursor = conn.cursor()

        self.write_cursor(texts, cursor)

        cursor.close()
        conn.commit()
        conn.close()
        print "changes saved to %s" % os.path.basename(outfilepath)


    def write_cursor(self, texts, cursor):

        if (cursor.execute("SELECT Count() FROM sms").fetchone()[0] > 0):
            raise sms_exceptions.NonEmptyStartDBError("Output DB has existing messages!")

        #populate fast lookup table:
        contactIdFromNumber = {}
        query = cursor.execute('SELECT _id,address FROM canonical_addresses;')
        for row in query:
            contactIdFromNumber[core.cleanNumber(row[1])] = row[0]

        #start the main loop through each message
        i=0
        lastSpeed=0
        lastCheckedSpeed=0
        starttime = time.time()

        for txt in texts:

            clean_number = core.cleanNumber(txt.num)

            #add a new canonical_addresses lookup entry and thread item if it doesn't exist
            if not clean_number in contactIdFromNumber:
                cursor.execute( "INSERT INTO canonical_addresses (address) VALUES (?)", [txt.num])
                contactIdFromNumber[clean_number] = cursor.lastrowid
                cursor.execute( "INSERT INTO threads (recipient_ids) VALUES (?)", [contactIdFromNumber[clean_number]])
            contact_id = contactIdFromNumber[clean_number]

            ## TODO Only run this query at the END of the loop!
            #now update the conversation thread (happends with each new message)
            cursor.execute( "UPDATE threads SET message_count=message_count + 1,snippet=?,'date'=? WHERE recipient_ids=? ", [txt.body,txt.date,contact_id] )
            cursor.execute( "SELECT _id FROM threads WHERE recipient_ids=? ", [contact_id] )
            thread_id = cursor.fetchone()[0]

            if False: ## TODO move this debug output to better better comments
                print "thread_id = "+ str(thread_id)
                cursor.execute( "SELECT * FROM threads WHERE _id=?", [contact_id] )
                print "updated thread: " + str(cursor.fetchone())
                print "adding entry to message db: " + str([txt.num,txt.date,txt.body,thread_id,txt.incoming+1])

            ## TODO try using cur.execute('BEGIN TRANSACTION') and cur.execute('COMMIT') every 1000 for speedup
            #add message to sms table
            cursor.execute( "INSERT INTO sms (address,'date',body,thread_id,read,type,seen) VALUES (?,?,?,?,1,?,1)", [txt.num,txt.date,txt.body,thread_id,txt.incoming+1])

            #print status (with fancy speed calculation)
            recalculate_every = 100
            if i%recalculate_every == 0:
                lastSpeed = int(recalculate_every/(time.time() - lastCheckedSpeed))
                lastCheckedSpeed = time.time()
            sys.stdout.write( "\rprocessed {0} entries, {1} convos, ({2} entries/sec)".format(i, len(contactIdFromNumber), lastSpeed ))
            sys.stdout.flush()
            i += 1

        print "\nfinished in {0} seconds (average {1}/second)".format((time.time() - starttime), int(i/(time.time() - starttime)))

        if False:
            print "\n\nthreads: "
            for row in cursor.execute('SELECT * FROM threads'):
                print row



INIT_DB_SQL = "\
BEGIN TRANSACTION;\
CREATE TABLE addr (_id INTEGER PRIMARY KEY,msg_id INTEGER,contact_id INTEGER,address TEXT,type INTEGER,charset INTEGER);\
CREATE TABLE android_metadata (locale TEXT);\
INSERT INTO 'android_metadata' VALUES('en_US');\
CREATE TABLE attachments (sms_id INTEGER,content_url TEXT,offset INTEGER);\
CREATE TABLE canonical_addresses (_id INTEGER PRIMARY KEY,address TEXT);\
CREATE TABLE drm (_id INTEGER PRIMARY KEY,_data TEXT);\
CREATE TABLE part (_id INTEGER PRIMARY KEY,mid INTEGER,seq INTEGER DEFAULT 0,ct TEXT,name TEXT,chset INTEGER,cd TEXT,fn TEXT,cid TEXT,cl TEXT,ctt_s INTEGER,ctt_t TEXT,_data TEXT,text TEXT);\
CREATE TABLE pdu (_id INTEGER PRIMARY KEY,thread_id INTEGER,date INTEGER,msg_box INTEGER,read INTEGER DEFAULT 0,m_id TEXT,sub TEXT,sub_cs INTEGER,ct_t TEXT,ct_l TEXT,exp INTEGER,m_cls TEXT,m_type INTEGER,v INTEGER,m_size INTEGER,pri INTEGER,rr INTEGER,rpt_a INTEGER,resp_st INTEGER,st INTEGER,tr_id TEXT,retr_st INTEGER,retr_txt TEXT,retr_txt_cs INTEGER,read_status INTEGER,ct_cls INTEGER,resp_txt TEXT,d_tm INTEGER,d_rpt INTEGER,locked INTEGER DEFAULT 0,seen INTEGER DEFAULT 0);\
CREATE TABLE pending_msgs (_id INTEGER PRIMARY KEY,proto_type INTEGER,msg_id INTEGER,msg_type INTEGER,err_type INTEGER,err_code INTEGER,retry_index INTEGER NOT NULL DEFAULT 0,due_time INTEGER,last_try INTEGER);\
CREATE TABLE rate (sent_time INTEGER);\
CREATE TABLE raw (_id INTEGER PRIMARY KEY,date INTEGER,reference_number INTEGER,count INTEGER,sequence INTEGER,destination_port INTEGER,address TEXT,pdu TEXT);\
CREATE TABLE sms (_id INTEGER PRIMARY KEY,thread_id INTEGER,address TEXT,person INTEGER,date INTEGER,protocol INTEGER,read INTEGER DEFAULT 0,status INTEGER DEFAULT -1,type INTEGER,reply_path_present INTEGER,subject TEXT,body TEXT,service_center TEXT,locked INTEGER DEFAULT 0,error_code INTEGER DEFAULT 0,seen INTEGER DEFAULT 0);\
CREATE TABLE sr_pending (reference_number INTEGER,action TEXT,data TEXT);\
CREATE TABLE threads (_id INTEGER PRIMARY KEY,date INTEGER DEFAULT 0,message_count INTEGER DEFAULT 0,recipient_ids TEXT,snippet TEXT,snippet_cs INTEGER DEFAULT 0,read INTEGER DEFAULT 1,type INTEGER DEFAULT 0,error INTEGER DEFAULT 0,has_attachment INTEGER DEFAULT 0);\
CREATE VIRTUAL TABLE words USING FTS3 (_id INTEGER PRIMARY KEY, index_text TEXT, source_id INTEGER, table_to_use INTEGER);\
CREATE TRIGGER pdu_update_thread_on_insert AFTER INSERT ON pdu   WHEN new.m_type=132    OR new.m_type=130    OR new.m_type=128 BEGIN  UPDATE threads SET    date = (strftime('%s','now') * 1000),     snippet = new.sub,     snippet_cs = new.sub_cs  WHERE threads._id = new.thread_id;   UPDATE threads SET message_count =      (SELECT COUNT(sms._id) FROM sms LEFT JOIN threads       ON threads._id = thread_id      WHERE thread_id = new.thread_id        AND sms.type != 3) +      (SELECT COUNT(pdu._id) FROM pdu LEFT JOIN threads       ON threads._id = thread_id      WHERE thread_id = new.thread_id        AND (m_type=132 OR m_type=130 OR m_type=128)        AND msg_box != 3)   WHERE threads._id = new.thread_id;   UPDATE threads SET read =     CASE (SELECT COUNT(*)          FROM pdu          WHERE read = 0            AND thread_id = threads._id             AND (m_type=132 OR m_type=130 OR m_type=128))       WHEN 0 THEN 1      ELSE 0    END  WHERE threads._id = new.thread_id; END;\
CREATE TRIGGER sms_update_thread_on_insert AFTER INSERT ON sms BEGIN  UPDATE threads SET    date = (strftime('%s','now') * 1000),     snippet = new.body,     snippet_cs = 0  WHERE threads._id = new.thread_id;   UPDATE threads SET message_count =      (SELECT COUNT(sms._id) FROM sms LEFT JOIN threads       ON threads._id = thread_id      WHERE thread_id = new.thread_id        AND sms.type != 3) +      (SELECT COUNT(pdu._id) FROM pdu LEFT JOIN threads       ON threads._id = thread_id      WHERE thread_id = new.thread_id        AND (m_type=132 OR m_type=130 OR m_type=128)        AND msg_box != 3)   WHERE threads._id = new.thread_id;   UPDATE threads SET read =     CASE (SELECT COUNT(*)          FROM sms          WHERE read = 0            AND thread_id = threads._id)      WHEN 0 THEN 1      ELSE 0    END  WHERE threads._id = new.thread_id; END;\
CREATE TRIGGER pdu_update_thread_date_subject_on_update AFTER  UPDATE OF date, sub, msg_box  ON pdu   WHEN new.m_type=132    OR new.m_type=130    OR new.m_type=128 BEGIN  UPDATE threads SET    date = (strftime('%s','now') * 1000),     snippet = new.sub,     snippet_cs = new.sub_cs  WHERE threads._id = new.thread_id;   UPDATE threads SET message_count =      (SELECT COUNT(sms._id) FROM sms LEFT JOIN threads       ON threads._id = thread_id      WHERE thread_id = new.thread_id        AND sms.type != 3) +      (SELECT COUNT(pdu._id) FROM pdu LEFT JOIN threads       ON threads._id = thread_id      WHERE thread_id = new.thread_id        AND (m_type=132 OR m_type=130 OR m_type=128)        AND msg_box != 3)   WHERE threads._id = new.thread_id;   UPDATE threads SET read =     CASE (SELECT COUNT(*)          FROM pdu          WHERE read = 0            AND thread_id = threads._id             AND (m_type=132 OR m_type=130 OR m_type=128))       WHEN 0 THEN 1      ELSE 0    END  WHERE threads._id = new.thread_id; END;\
CREATE TRIGGER sms_update_thread_date_subject_on_update AFTER  UPDATE OF date, body, type  ON sms BEGIN  UPDATE threads SET    date = (strftime('%s','now') * 1000),     snippet = new.body,     snippet_cs = 0  WHERE threads._id = new.thread_id;   UPDATE threads SET message_count =      (SELECT COUNT(sms._id) FROM sms LEFT JOIN threads       ON threads._id = thread_id      WHERE thread_id = new.thread_id        AND sms.type != 3) +      (SELECT COUNT(pdu._id) FROM pdu LEFT JOIN threads       ON threads._id = thread_id      WHERE thread_id = new.thread_id        AND (m_type=132 OR m_type=130 OR m_type=128)        AND msg_box != 3)   WHERE threads._id = new.thread_id;   UPDATE threads SET read =     CASE (SELECT COUNT(*)          FROM sms          WHERE read = 0            AND thread_id = threads._id)      WHEN 0 THEN 1      ELSE 0    END  WHERE threads._id = new.thread_id; END;\
CREATE TRIGGER pdu_update_thread_read_on_update AFTER  UPDATE OF read  ON pdu   WHEN new.m_type=132    OR new.m_type=130    OR new.m_type=128 BEGIN   UPDATE threads SET read =     CASE (SELECT COUNT(*)          FROM pdu          WHERE read = 0            AND thread_id = threads._id             AND (m_type=132 OR m_type=130 OR m_type=128))       WHEN 0 THEN 1      ELSE 0    END  WHERE threads._id = new.thread_id; END;\
CREATE TRIGGER sms_update_thread_read_on_update AFTER  UPDATE OF read  ON sms BEGIN   UPDATE threads SET read =     CASE (SELECT COUNT(*)          FROM sms          WHERE read = 0            AND thread_id = threads._id)      WHEN 0 THEN 1      ELSE 0    END  WHERE threads._id = new.thread_id; END;\
CREATE TRIGGER pdu_update_thread_on_delete AFTER DELETE ON pdu BEGIN   UPDATE threads SET      date = (strftime('%s','now') * 1000)  WHERE threads._id = old.thread_id;   UPDATE threads SET message_count =      (SELECT COUNT(sms._id) FROM sms LEFT JOIN threads       ON threads._id = thread_id      WHERE thread_id = old.thread_id        AND sms.type != 3) +      (SELECT COUNT(pdu._id) FROM pdu LEFT JOIN threads       ON threads._id = thread_id      WHERE thread_id = old.thread_id        AND (m_type=132 OR m_type=130 OR m_type=128)        AND msg_box != 3)   WHERE threads._id = old.thread_id;   UPDATE threads SET snippet =    (SELECT snippet FROM     (SELECT date * 1000 AS date, sub AS snippet, thread_id FROM pdu      UNION SELECT date, body AS snippet, thread_id FROM sms)    WHERE thread_id = OLD.thread_id ORDER BY date DESC LIMIT 1)   WHERE threads._id = OLD.thread_id;   UPDATE threads SET snippet_cs =    (SELECT snippet_cs FROM     (SELECT date * 1000 AS date, sub_cs AS snippet_cs, thread_id FROM pdu      UNION SELECT date, 0 AS snippet_cs, thread_id FROM sms)    WHERE thread_id = OLD.thread_id ORDER BY date DESC LIMIT 1)   WHERE threads._id = OLD.thread_id; END;\
CREATE TRIGGER delete_obsolete_threads_pdu AFTER DELETE ON pdu BEGIN   DELETE FROM threads   WHERE     _id = old.thread_id     AND _id NOT IN     (SELECT thread_id FROM sms      UNION SELECT thread_id from pdu); END;\
CREATE TRIGGER delete_obsolete_threads_when_update_pdu AFTER UPDATE OF thread_id ON pdu WHEN old.thread_id != new.thread_id BEGIN   DELETE FROM threads   WHERE     _id = old.thread_id     AND _id NOT IN     (SELECT thread_id FROM sms      UNION SELECT thread_id from pdu); END;\
CREATE TRIGGER insert_mms_pending_on_insert AFTER INSERT ON pdu WHEN new.m_type=130  OR new.m_type=135 BEGIN   INSERT INTO pending_msgs    (proto_type,     msg_id,     msg_type,     err_type,     err_code,     retry_index,     due_time)   VALUES     (1,      new._id,      new.m_type,0,0,0,0);END;\
CREATE TRIGGER insert_mms_pending_on_update AFTER UPDATE ON pdu WHEN new.m_type=128  AND new.msg_box=4  AND old.msg_box!=4 BEGIN   INSERT INTO pending_msgs    (proto_type,     msg_id,     msg_type,     err_type,     err_code,     retry_index,     due_time)   VALUES     (1,      new._id,      new.m_type,0,0,0,0);END;\
CREATE TRIGGER delete_mms_pending_on_update AFTER UPDATE ON pdu WHEN old.msg_box=4  AND new.msg_box!=4 BEGIN   DELETE FROM pending_msgs  WHERE msg_id=new._id; END;\
CREATE TRIGGER delete_mms_pending_on_delete AFTER DELETE ON pdu BEGIN   DELETE FROM pending_msgs  WHERE msg_id=old._id; END;\
CREATE TRIGGER update_threads_error_on_update_mms   AFTER UPDATE OF err_type ON pending_msgs   WHEN (OLD.err_type < 10 AND NEW.err_type >= 10)    OR (OLD.err_type >= 10 AND NEW.err_type < 10) BEGIN  UPDATE threads SET error =     CASE      WHEN NEW.err_type >= 10 THEN error + 1      ELSE error - 1    END   WHERE _id =   (SELECT DISTINCT thread_id    FROM pdu    WHERE _id = NEW.msg_id); END;\
CREATE TRIGGER update_threads_error_on_delete_mms   BEFORE DELETE ON pdu  WHEN OLD._id IN (SELECT DISTINCT msg_id                   FROM pending_msgs                   WHERE err_type >= 10) BEGIN   UPDATE threads SET error = error - 1  WHERE _id = OLD.thread_id; END;\
CREATE TRIGGER update_threads_error_on_move_mms   BEFORE UPDATE OF msg_box ON pdu   WHEN (OLD.msg_box = 4 AND NEW.msg_box != 4)   AND (OLD._id IN (SELECT DISTINCT msg_id                   FROM pending_msgs                   WHERE err_type >= 10)) BEGIN   UPDATE threads SET error = error - 1  WHERE _id = OLD.thread_id; END;\
CREATE TRIGGER update_threads_error_on_update_sms   AFTER UPDATE OF type ON sms  WHEN (OLD.type != 5 AND NEW.type = 5)    OR (OLD.type = 5 AND NEW.type != 5) BEGIN   UPDATE threads SET error =     CASE      WHEN NEW.type = 5 THEN error + 1      ELSE error - 1    END   WHERE _id = NEW.thread_id; END;\
CREATE TRIGGER part_cleanup DELETE ON pdu BEGIN   DELETE FROM part  WHERE mid=old._id;END;\
CREATE TRIGGER addr_cleanup DELETE ON pdu BEGIN   DELETE FROM addr  WHERE msg_id=old._id;END;\
CREATE TRIGGER cleanup_delivery_and_read_report AFTER DELETE ON pdu WHEN old.m_type=128 BEGIN   DELETE FROM pdu  WHERE (m_type=134    OR m_type=136)    AND m_id=old.m_id; END;\
CREATE TRIGGER update_threads_on_insert_part  AFTER INSERT ON part  WHEN new.ct != 'text/plain' AND new.ct != 'application/smil'  BEGIN   UPDATE threads SET has_attachment=1 WHERE _id IN    (SELECT pdu.thread_id FROM part JOIN pdu ON pdu._id=part.mid      WHERE part._id=new._id LIMIT 1);  END;\
CREATE TRIGGER update_threads_on_update_part  AFTER UPDATE of mid ON part  WHEN new.ct != 'text/plain' AND new.ct != 'application/smil'  BEGIN   UPDATE threads SET has_attachment=1 WHERE _id IN    (SELECT pdu.thread_id FROM part JOIN pdu ON pdu._id=part.mid      WHERE part._id=new._id LIMIT 1);  END;\
CREATE TRIGGER update_threads_on_delete_part  AFTER DELETE ON part  WHEN old.ct != 'text/plain' AND old.ct != 'application/smil'  BEGIN   UPDATE threads SET has_attachment =    CASE     (SELECT COUNT(*) FROM part JOIN pdu      WHERE pdu.thread_id = threads._id      AND part.ct != 'text/plain' AND part.ct != 'application/smil'      AND part.mid = pdu._id)   WHEN 0 THEN 0    ELSE 1    END;  END;\
CREATE TRIGGER update_threads_on_update_pdu  AFTER UPDATE of thread_id ON pdu  BEGIN   UPDATE threads SET has_attachment=1 WHERE _id IN    (SELECT pdu.thread_id FROM part JOIN pdu      WHERE part.ct != 'text/plain' AND part.ct != 'application/smil'      AND part.mid = pdu._id); END;\
CREATE INDEX typeThreadIdIndex ON sms (type, thread_id);\
COMMIT;\
"







