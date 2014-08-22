import sqlite3, uuid, os
import core, sms_exceptions


class IOS6:
    """ iOS 6 sqlite reader and writer """

    def parse(self, filepath):
        """ Parse iOS 6 sqlite file to Text[] """
        db = sqlite3.connect(filepath)
        cursor = db.cursor()
        texts = self.parse_cursor(cursor)
        cursor.close()
        db.commit()
        db.close()
        return texts

    def parse_cursor(self, cursor):

        handles = {}
        query = cursor.execute(
            'SELECT ROWID, id, country FROM handle')
        for row in query:
            handles[row[0]] = (row[1], row[2], core.cleanNumber(row[1]))

        chats = {} # room_name -> [members]
        #query = cursor.execute('SELECT room_name, ROWID FROM chat WHERE room_name <> "" ')
        query = cursor.execute(
            'SELECT chat.room_name, handle.id FROM chat \
             LEFT OUTER JOIN chat_handle_join ON chat_handle_join.chat_id = chat.ROWID \
             JOIN handle ON chat_handle_join.handle_id = handle.ROWID \
             WHERE chat.room_name <> "" ')
        for row in query:
            if (not row[0] in chats): chats[row[0]] = []
            chats[row[0]].append(row[1])

        texts = []
        query = cursor.execute(
            'SELECT message.handle_id, message.date, message.is_from_me, message.text, chat.room_name \
             FROM message \
             LEFT OUTER JOIN chat_message_join ON message.ROWID = chat_message_join.message_id \
             LEFT OUTER JOIN chat ON chat_message_join.chat_id = chat.ROWID \
             ORDER BY message.ROWID ASC;')
        for row in query:
            number = handles[row[0]][0] if row[0] in handles else "unknown"
            text = core.Text(
                num = number,
                date = long((row[1] + 978307200)*1000),
                incoming = row[2] == 0,
                body = row[3],
                chatroom = row[4],
                members=(chats[row[4]] if row[4] else None))
            texts.append(text)
        return texts

    def write(self, texts, outfilepath):
        print "Creating empty iOS 6 SQLITE db"
        conn = sqlite3.connect(outfilepath)
        conn.executescript(INIT_DB_SQL)

        cursor = conn.cursor()
        self.write_cursor(texts, cursor)

        conn.commit()
        cursor.close()
        conn.close()
        print "changes saved to", outfilepath


    def write_cursor(self, texts, cursor):

        if (cursor.execute("SELECT Count() FROM message").fetchone()[0] > 0):
            raise sms_exceptions.NonEmptyStartDBError("Output DB has existing messages!")

        ## First populate the 'handle' table with each contact
        handles_lookup = {} # cleaned # -> handle ROWID
        chat_lookup = {} # chat_key -> chat ROWID
        chat_participants = {} # chat_key -> [cleaned1, cleaned2]
        for txt in texts:
            try:
                clean_number = core.cleanNumber(txt.num)
                chat_key = txt.chatroom if txt.chatroom else txt.num

                ## Create the handle table (effectively a contacts table)
                if (clean_number) and (not clean_number in handles_lookup):
                    cursor.execute( "INSERT INTO handle ('id', service, uncanonicalized_id ) \
                        VALUES (?,?,?)", [txt.num,"SMS",clean_number])
                    handles_lookup[clean_number] = cursor.lastrowid

                if not chat_key:
                    core.warning("no txt chat_key [%s] for %s" % (chat_key, txt))
                ## Create the chat table (effectively a threads table)
                if not chat_key in chat_lookup:
                    guid = ("SMS;+;%s" % txt.chatroom) if txt.chatroom else ("SMS;-;%s" % txt.num)
                    style = 43 if txt.chatroom else 45
                    cursor.execute( "INSERT INTO chat (guid, style, state, chat_identifier, service_name, room_name ) \
                        VALUES (?,?,?,?,?,?)", [guid, style, 3, chat_key, 'SMS', txt.chatroom])
                    chat_lookup[chat_key] = cursor.lastrowid

                ## Create the chat_handle_join table (represents participants in all threads)
                if not chat_key in chat_participants:
                    chat_participants[chat_key] = set()
                if not clean_number in chat_participants[chat_key]:
                    chat_participants[chat_key].add(clean_number)
                    chat_id = chat_lookup[chat_key]
                    try:
                        handle_id = handles_lookup[clean_number]
                        cursor.execute( "INSERT INTO chat_handle_join (chat_id, handle_id ) \
                            VALUES (?,?)", [chat_id, handle_id])
                    except: pass #don't add handle joins for unknown contacts.
            except:
                print core.term.red("something failed at: %s") % (txt)
                raise

        print "built handles table with %i, chat with %i, chat_handle_join with %i entries" \
            % (len(handles_lookup), len(chat_lookup), len(chat_participants))


        for txt in texts:
            chat_key = txt.chatroom if txt.chatroom else txt.num
            handle_i = handles_lookup[core.cleanNumber(txt.num)] if core.cleanNumber(txt.num) in handles_lookup else 0
            idate = long( (float(txt.date)/1000) - 978307200)
            from_me = 0 if txt.incoming else 1
            guid = str(uuid.uuid1())

            cursor.execute( "INSERT INTO message \
                ('text', guid, handle_id, version, type, service, 'date', is_finished, is_from_me, is_sent, is_read ) \
                VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [txt.body, guid, handle_i, 1, txt.chatroom != None, 'SMS', idate, 1, from_me, from_me, (1 - from_me)])
            message_id = cursor.lastrowid

            chat_id = chat_lookup[chat_key]
            cursor.execute( "INSERT INTO chat_message_join (chat_id, message_id) \
                VALUES (?,?)", [chat_id, message_id])

        print "built messages table with %i entries" % len(texts)


INIT_DB_SQL = "\
    BEGIN TRANSACTION;\
    CREATE TABLE attachment (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, guid TEXT UNIQUE NOT NULL, created_date INTEGER DEFAULT 0, start_date INTEGER DEFAULT 0, filename TEXT, uti TEXT, mime_type TEXT, transfer_state INTEGER DEFAULT 0, is_outgoing INTEGER DEFAULT 0);\
    CREATE TABLE chat (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, guid TEXT UNIQUE NOT NULL, style INTEGER, state INTEGER, account_id TEXT, properties BLOB, chat_identifier TEXT, service_name TEXT, room_name TEXT, account_login TEXT, is_archived INTEGER DEFAULT 0, last_addressed_handle TEXT);\
    CREATE TABLE chat_handle_join ( chat_id INTEGER REFERENCES chat (ROWID) ON DELETE CASCADE, handle_id INTEGER REFERENCES handle (ROWID) ON DELETE CASCADE, UNIQUE(chat_id, handle_id));\
    CREATE TABLE chat_message_join ( chat_id INTEGER REFERENCES chat (ROWID) ON DELETE CASCADE, message_id INTEGER REFERENCES message (ROWID) ON DELETE CASCADE, PRIMARY KEY (chat_id, message_id));\
    CREATE TABLE handle ( ROWID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, id TEXT NOT NULL, country TEXT, service TEXT NOT NULL, uncanonicalized_id TEXT, UNIQUE (id, service) );\
    CREATE TABLE message (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, guid TEXT UNIQUE NOT NULL, text TEXT, replace INTEGER DEFAULT 0, service_center TEXT, handle_id INTEGER DEFAULT 0, subject TEXT, country TEXT, attributedBody BLOB, version INTEGER DEFAULT 0, type INTEGER DEFAULT 0, service TEXT, account TEXT, account_guid TEXT, error INTEGER DEFAULT 0, date INTEGER, date_read INTEGER, date_delivered INTEGER, is_delivered INTEGER DEFAULT 0, is_finished INTEGER DEFAULT 0, is_emote INTEGER DEFAULT 0, is_from_me INTEGER DEFAULT 0, is_empty INTEGER DEFAULT 0, is_delayed INTEGER DEFAULT 0, is_auto_reply INTEGER DEFAULT 0, is_prepared INTEGER DEFAULT 0, is_read INTEGER DEFAULT 0, is_system_message INTEGER DEFAULT 0, is_sent INTEGER DEFAULT 0, has_dd_results INTEGER DEFAULT 0, is_service_message INTEGER DEFAULT 0, is_forward INTEGER DEFAULT 0, was_downgraded INTEGER DEFAULT 0, is_archive INTEGER DEFAULT 0, cache_has_attachments INTEGER DEFAULT 0, cache_roomnames TEXT, was_data_detected INTEGER DEFAULT 0, was_deduplicated INTEGER DEFAULT 0);\
    CREATE TABLE message_attachment_join ( message_id INTEGER REFERENCES message (ROWID) ON DELETE CASCADE, attachment_id INTEGER REFERENCES attachment (ROWID) ON DELETE CASCADE, UNIQUE(message_id, attachment_id));\
    CREATE TRIGGER clean_orphaned_messages AFTER DELETE ON chat_message_join BEGIN     DELETE FROM message         WHERE message.ROWID = old.message_id     AND         (SELECT 1 from chat_message_join WHERE message_id = old.message_id LIMIT 1) IS NULL; END;\
    CREATE TRIGGER clean_orphaned_attachments AFTER DELETE ON message_attachment_join BEGIN     DELETE FROM attachment         WHERE attachment.ROWID = old.attachment_id     AND         (SELECT 1 from message_attachment_join WHERE attachment_id = old.attachment_id LIMIT 1) IS NULL; END;\
    CREATE TRIGGER clean_orphaned_handles AFTER DELETE ON chat_handle_join BEGIN     DELETE FROM handle         WHERE handle.ROWID = old.handle_id     AND         (SELECT 1 from chat_handle_join WHERE handle_id = old.handle_id LIMIT 1) IS NULL     AND         (SELECT 1 from message WHERE handle_id = old.handle_id LIMIT 1) IS NULL; END;\
    CREATE TRIGGER clean_orphaned_handles2 AFTER DELETE ON message BEGIN     DELETE FROM handle         WHERE handle.ROWID = old.handle_id     AND         (SELECT 1 from chat_handle_join WHERE handle_id = old.handle_id LIMIT 1) IS NULL     AND         (SELECT 1 from message WHERE handle_id = old.handle_id LIMIT 1) IS NULL; END;\
    CREATE TRIGGER set_message_has_attachments AFTER INSERT ON message_attachment_join BEGIN     UPDATE message       SET cache_has_attachments = 1     WHERE       message.ROWID = new.message_id; END;\
    CREATE TRIGGER clear_message_has_attachments AFTER DELETE ON message_attachment_join BEGIN     UPDATE message       SET cache_has_attachments = 0     WHERE       message.ROWID = old.message_id       AND       (SELECT 1 from message_attachment_join WHERE message_id = old.message_id LIMIT 1) IS NULL; END;\
    CREATE TRIGGER update_message_roomname_cache_insert AFTER INSERT ON chat_message_join BEGIN     UPDATE message       SET cache_roomnames = (         SELECT group_concat(c.room_name)         FROM chat c         INNER JOIN chat_message_join j ON c.ROWID = j.chat_id         WHERE           j.message_id = new.message_id       )       WHERE         message.ROWID = new.message_id; END;\
    CREATE TRIGGER update_message_roomname_cache_delete AFTER DELETE ON chat_message_join BEGIN     UPDATE message       SET cache_roomnames = (         SELECT group_concat(c.room_name)         FROM chat c         INNER JOIN chat_message_join j ON c.ROWID = j.chat_id         WHERE           j.message_id = old.message_id       )       WHERE         message.ROWID = old.message_id; END;\
    CREATE TRIGGER delete_attachment_files AFTER DELETE ON attachment BEGIN   SELECT delete_attachment_path(old.filename); END;\
    CREATE INDEX chat_idx_identifier ON chat(chat_identifier);\
    CREATE INDEX chat_idx_room_name ON chat(room_name);\
    CREATE INDEX message_idx_was_downgraded ON message(was_downgraded);\
    CREATE INDEX message_idx_is_read ON message(is_read, is_from_me, is_finished);\
    CREATE INDEX message_idx_failed ON message(is_finished, is_from_me, error);\
    CREATE INDEX message_idx_handle ON message(handle_id, date);\
    CREATE INDEX chat_message_join_idx_message_id ON chat_message_join(message_id, chat_id);\
    COMMIT; "


