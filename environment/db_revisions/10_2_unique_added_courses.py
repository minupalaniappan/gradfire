ALTER TABLE students_added_courses DROP CONSTRAINT unique_added_course;
ALTER TABLE students_added_courses ADD CONSTRAINT unique_added_course UNIQUE (student_id, subject, number, title);
ALTER TABLE course_advice DROP term_year;
ALTER TABLE course_advice DROP term_month;