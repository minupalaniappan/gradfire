ALTER TABLE instructors ADD name_tsv tsvector;
UPDATE instructors SET name_tsv = to_tsvector('english', name);
ALTER TABLE courses_grades ADD instructor_id int REFERENCES instructors(id);
UPDATE courses_grades SET instructor_id = (SELECT id FROM instructors, plainto_tsquery(courses_grades.instructor) query ORDER BY ts_rank(name_tsv, query) DESC LIMIT 1);