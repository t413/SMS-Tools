import os, sys, time, sqlite3
import core, sms_exceptions

class Bugle:
    """ New android (bugle_db) sqlite reader and writer """


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
            'select\
            ppl.normalized_destination as num,\
            p.timestamp as date,\
            case when m.sender_id in (select _id from participants where contact_id=-1) then 2 else 1 end incoming,\
            p.text as body\
            from messages m, conversations c, parts p, participants ppl, conversation_participants cp\
            where (m.conversation_id = c._id) and (m._id = p.message_id) and (cp.conversation_id = c._id) and (cp.participant_id = ppl._id);\
            ')
        for row in query:
            txt = core.Text(num=row[0],date=long(row[1]),incoming=(row[2]==2),body=row[3])
            texts.append(txt)
        return texts

    def write(self, texts, outfilepath):
        """ write a Text[] to sqlite file """
        print "Bungle database creation not supported (yet?). Use SMSBackupRestore format instead"

INIT_DB_SQL = "\
BEGIN TRANSACTION;\
CREATE TABLE android_metadata (locale TEXT);\
CREATE TABLE conversation_participants(_id INTEGER PRIMARY KEY AUTOINCREMENT,conversation_id INT,participant_id INT,UNIQUE (conversation_id,participant_id) ON CONFLICT FAIL, FOREIGN KEY (conversation_id) REFERENCES conversations(_id) ON DELETE CASCADE FOREIGN KEY (participant_id) REFERENCES participants(_id));\
CREATE TABLE conversations(_id INTEGER PRIMARY KEY AUTOINCREMENT, sms_thread_id INT DEFAULT(0), name TEXT, latest_message_id INT, snippet_text TEXT, subject_text TEXT, preview_uri TEXT, preview_content_type TEXT, show_draft INT DEFAULT(0), draft_snippet_text TEXT, draft_subject_text TEXT, draft_preview_uri TEXT, draft_preview_content_type TEXT, archive_status INT DEFAULT(0), sort_timestamp INT DEFAULT(0), last_read_timestamp INT DEFAULT(0), icon TEXT, participant_contact_id INT DEFAULT ( -1), participant_lookup_key TEXT, participant_normalized_destination TEXT, current_self_id TEXT, participant_count INT DEFAULT(0), notification_enabled INT DEFAULT(-1), notification_sound_uri TEXT, notification_vibration INT DEFAULT(-1), include_email_addr INT DEFAULT(0), sms_service_center TEXT ,IS_ENTERPRISE INT DEFAULT(0));\
CREATE TABLE messages (_id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INT, sender_id INT, sent_timestamp INT DEFAULT(0), received_timestamp INT DEFAULT(0), message_protocol INT DEFAULT(0), message_status INT DEFAULT(0), seen INT DEFAULT(0), read INT DEFAULT(0), sms_message_uri TEXT, sms_priority INT DEFAULT(0), sms_message_size INT DEFAULT(0), mms_subject TEXT, mms_transaction_id TEXT, mms_content_location TEXT, mms_expiry INT DEFAULT(0), raw_status INT DEFAULT(0), self_id INT, retry_start_timestamp INT DEFAULT(0), FOREIGN KEY (conversation_id) REFERENCES conversations(_id) ON DELETE CASCADE FOREIGN KEY (sender_id) REFERENCES participants(_id) ON DELETE SET NULL FOREIGN KEY (self_id) REFERENCES participants(_id) ON DELETE SET NULL );\
CREATE TABLE participants(_id INTEGER PRIMARY KEY AUTOINCREMENT,sub_id INT DEFAULT(-2),sim_slot_id INT DEFAULT(-1),normalized_destination TEXT,send_destination TEXT,display_destination TEXT,full_name TEXT,first_name TEXT,profile_photo_uri TEXT, contact_id INT DEFAULT( -1), lookup_key STRING, blocked INT DEFAULT(0), subscription_name TEXT, subscription_color INT DEFAULT(0), contact_destination TEXT, UNIQUE (normalized_destination, sub_id) ON CONFLICT FAIL);\
CREATE TABLE parts(_id INTEGER PRIMARY KEY AUTOINCREMENT,message_id INT,text TEXT,uri TEXT,content_type TEXT,width INT DEFAULT(-1),height INT DEFAULT(-1),timestamp INT, conversation_id INT NOT NULL,FOREIGN KEY (message_id) REFERENCES messages(_id) ON DELETE CASCADE FOREIGN KEY (conversation_id) REFERENCES conversations(_id) ON DELETE CASCADE );\
CREATE VIEW conversation_image_parts_view AS SELECT messages.conversation_id as conversation_id, parts.uri as uri, participants.full_name as _display_name, parts.uri as contentUri,  NULL as thumbnailUri, parts.content_type as contentType, participants.display_destination as display_destination, messages.received_timestamp as received_timestamp, messages.message_status as message_status  FROM messages LEFT JOIN parts ON (messages._id=parts.message_id)  LEFT JOIN participants ON (messages.sender_id=participants._id) WHERE parts.content_type like 'image/%' ORDER BY messages.received_timestamp ASC, parts._id ASC;\
CREATE VIEW conversation_list_view AS SELECT conversations._id as _id, conversations.name as name, conversations.current_self_id as current_self_id, conversations.archive_status as archive_status, messages.read as read, conversations.icon as icon, conversations.participant_contact_id as participant_contact_id, conversations.participant_lookup_key as participant_lookup_key, conversations.participant_normalized_destination as participant_normalized_destination, conversations.sort_timestamp as sort_timestamp, conversations.show_draft as show_draft, conversations.draft_snippet_text as draft_snippet_text, conversations.draft_preview_uri as draft_preview_uri, conversations.draft_subject_text as draft_subject_text, conversations.draft_preview_content_type as draft_preview_content_type, conversations.preview_uri as preview_uri, conversations.preview_content_type as preview_content_type, conversations.participant_count as participant_count, conversations.notification_enabled as notification_enabled, conversations.notification_sound_uri as notification_sound_uri, conversations.notification_vibration as notification_vibration, conversations.include_email_addr as include_email_addr, messages.message_status as message_status, messages.raw_status as raw_status, messages._id as message_id, participants.first_name as snippet_sender_first_name, participants.display_destination as snippet_sender_display_destination, conversations.IS_ENTERPRISE as IS_ENTERPRISE, conversations.snippet_text as snippet_text, conversations.subject_text as subject_text  FROM conversations LEFT JOIN messages ON (conversations.latest_message_id=messages._id)  LEFT JOIN participants ON (messages.sender_id=participants._id) ORDER BY conversations.sort_timestamp DESC;\
CREATE VIEW draft_parts_view AS SELECT parts._id as _id, parts.message_id as message_id, parts.text as text, parts.uri as uri, parts.content_type as content_type, parts.width as width, parts.height as height, messages.conversation_id as conversation_id  FROM messages LEFT JOIN parts ON (messages._id=parts.message_id) WHERE messages.message_status = 3;\
CREATE TRIGGER messages_TRIGGER AFTER UPDATE OF received_timestamp ON messages FOR EACH ROW BEGIN UPDATE parts SET timestamp = NEW.received_timestamp WHERE parts.message_id = NEW._id; END;\
CREATE TRIGGER parts_TRIGGER AFTER INSERT ON parts FOR EACH ROW  BEGIN UPDATE parts SET timestamp= (SELECT received_timestamp FROM messages WHERE messages._id=NEW.message_id) WHERE parts._id=NEW._id; END;\
CREATE INDEX index_conversation_participants_conversation_id ON conversation_participants(conversation_id);\
CREATE INDEX index_conversations_archive_status ON conversations(archive_status);\
CREATE INDEX index_conversations_sms_thread_id ON conversations(sms_thread_id);\
CREATE INDEX index_conversations_sort_timestamp ON conversations(sort_timestamp);\
CREATE INDEX index_messages_sort ON messages(conversation_id, message_status, received_timestamp);\
CREATE INDEX index_messages_status_seen ON messages(message_status, seen);\
CREATE INDEX index_parts_message_id ON parts(message_id);\
COMMIT;\
"
