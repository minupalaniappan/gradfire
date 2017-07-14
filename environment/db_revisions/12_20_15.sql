ALTER TABLE students ADD major_ids int[];
UPDATE students SET major_ids = ARRAY[major_id];
UPDATE students SET major_ids = ARRAY[]::integer[] WHERE EXISTS (select 1 from unnest(major_ids) ids(id) where id is null);
ALTER TABLE students ADD verified boolean DEFAULT false;
ALTER TABLE students ADD CONSTRAINT unique_student UNIQUE (email);
ALTER TABLE students ADD verification_code text;