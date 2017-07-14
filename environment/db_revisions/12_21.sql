ALTER TABLE students_added_courses DROP CONSTRAINT students_added_courses_student_id_fkey;
ALTER TABLE students_added_courses ADD FOREIGN KEY (student_id) REFERENCES users ON DELETE CASCADE;

ALTER TABLE students_completed_courses DROP CONSTRAINT students_completed_courses_student_id_fkey;
ALTER TABLE students_completed_courses ADD FOREIGN KEY (student_id) REFERENCES users ON DELETE CASCADE;

ALTER TABLE students_course_equivalences DROP CONSTRAINT students_course_equivalences_student_id_fkey;
ALTER TABLE students_course_equivalences ADD FOREIGN KEY (student_id) REFERENCES users ON DELETE CASCADE;

ALTER TABLE students_ge_progress DROP CONSTRAINT students_ge_progress_student_id_fkey;
ALTER TABLE students_ge_progress ADD FOREIGN KEY (student_id) REFERENCES users ON DELETE CASCADE;

ALTER TABLE students_tentative_courses DROP CONSTRAINT students_tentative_courses_student_id_fkey;
ALTER TABLE students_tentative_courses ADD FOREIGN KEY (student_id) REFERENCES users ON DELETE CASCADE;

ALTER TABLE students ADD salt text;