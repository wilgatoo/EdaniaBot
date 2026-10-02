import sqlite3

DB_NAME = "edania.db"


def connect():

    return sqlite3.connect(DB_NAME)


def initialize():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detected_calls (
            call_id INTEGER PRIMARY KEY,
            buff_id TEXT NOT NULL,
            started_at INTEGER NOT NULL,
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_message (
            channel_id INTEGER PRIMARY KEY,
            message_id INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def get_call_ids():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT call_id FROM detected_calls"
    )

    rows = cursor.fetchall()

    conn.close()

    return {
        row[0]
        for row in rows
    }


def save_call(
    call_id,
    buff_id,
    started_at
):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO detected_calls
        (call_id, buff_id, started_at)
        VALUES (?, ?, ?)
    """, (
        call_id,
        buff_id,
        started_at
    ))

    conn.commit()
    conn.close()


def clear_calls():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM detected_calls"
    )

    conn.commit()
    conn.close()


def get_meta(key):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT value FROM meta WHERE key = ?",
        (key,)
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return row[0]


def set_meta(
    key,
    value
):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO meta (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
    """, (
        key,
        value
    ))

    conn.commit()
    conn.close()


def get_status_message(
    channel_id
):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT message_id
        FROM status_message
        WHERE channel_id = ?
    """, (
        channel_id,
    ))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return row[0]


def set_status_message(
    channel_id,
    message_id
):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO status_message
        (channel_id, message_id)
        VALUES (?, ?)
        ON CONFLICT(channel_id)
        DO UPDATE SET message_id = excluded.message_id
    """, (
        channel_id,
        message_id
    ))

    conn.commit()
    conn.close()