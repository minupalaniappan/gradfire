alter table students rename password to password_checksum;
alter table students add session_token_checksum text;