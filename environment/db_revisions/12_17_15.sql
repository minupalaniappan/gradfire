CREATE TABLE students_added_courses (
  student_id int REFERENCES students,
  course_id int REFERENCES courses,
  CONSTRAINT unique_added_course UNIQUE (student_id, course_id)
);