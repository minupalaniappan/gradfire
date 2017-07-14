CREATE TABLE program_types (
    id SERIAL PRIMARY KEY,
    name text,
    CONSTRAINT unique_program_type UNIQUE (name)
);
INSERT INTO program_types (name) VALUES ('major');
CREATE TABLE programs (
    id SERIAL PRIMARY KEY,
    name text,
    variant text,
    program_type int REFERENCES program_types,
    CONSTRAINT unique_program UNIQUE (name, variant, program_type)
);

INSERT INTO programs (name, variant, program_type)
SELECT name, variant, (SELECT id FROM program_types WHERE name = 'major')
FROM majors;

CREATE TABLE students_programs(
    user_id int REFERENCES users,
    program_id int REFERENCES programs,
    CONSTRAINT unique_student_program UnIQUE (user_id, program_id)
);

ALTER TABLE majors_required_courses ADD program_id int REFERENCES programs;
UPDATE majors_required_courses SET program_id = (SELECT id FROM programs WHERE
    name = (SELECT name FROM majors WHERE majors.id = majors_required_courses.major_id)
    AND variant = (SELECT variant FROM majors WHERE majors.id = majors_required_courses.major_id));

INSERT INTO students_programs (user_id, program_id)
SELECT students_dep.id, programs.id
FROM students_dep
LEFT JOIN majors ON majors.id = ANY(students_dep.major_ids)
LEFT JOIN programs ON programs.name = majors.name AND programs.variant = majors.variant AND program_type = 1
WHERE programs.id IS NOT NULL;