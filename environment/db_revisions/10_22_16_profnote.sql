CREATE TABLE courses_notes(
    id SERIAL PRIMARY KEY,
    user_id int REFERENCES students,
    subject text,
    number text,
    note_json text,
    note_plain text,
    timestamp timestamp DEFAULT now()
);

CREATE INDEX courses_notes_latest_revision ON courses_notes(timestamp DESC NULLS LAST);