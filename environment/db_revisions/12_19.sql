ALTER TABLE students REMOVE session_token_checksum;

CREATE TABLE sessions (
  student_id int REFERENCES students,
  token_checksum text,
  expires timestamp
);