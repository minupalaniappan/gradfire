ALTER TABLE students ADD session_token_checksums text[];
UPDATE students SET session_token_checksums = ARRAY[session_token_checksum];
ALTER TABLE students DROP session_token_checksum;