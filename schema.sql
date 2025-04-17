CREATE TABLE IF NOT EXISTS user_message_status (
    user_id INTEGER PRIMARY KEY,
    last_seen_message_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (last_seen_message_id) REFERENCES private_messages(id)
); 