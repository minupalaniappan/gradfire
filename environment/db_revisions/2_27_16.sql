ALTER TABLE students_course_equivalences ADD id SERIAL PRIMARY KEY;
ALTER TABLE students_ge_progress ADD id SERIAL PRIMARY KEY;

CREATE TABLE students_ge_courses (
  student_id int REFERENCES students(id),
  ge_area text,
  course_id int REFERENCES courses(id),
  course_equivalence_id int REFERENCES students_course_equivalences(id),
  CONSTRAINT unique_ge_course UNIQUE (student_id, ge_area, course_id),
  CONSTRAINT unique_ge_course_equiv UNIQUE (student_id, ge_area, course_equivalence_id)
);

--
