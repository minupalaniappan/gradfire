ALTER TABLE courses ADD waitlist_length smallint;
ALTER TABLE courses ADD updated timestamp;
ALTER TABLE courses ADD registrar_removed boolean DEFAULT false;