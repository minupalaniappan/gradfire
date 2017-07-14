CREATE TABLE courses_textbooks (
	course_id int REFERENCES courses,
	isbn text,
	CONSTRAINT unique_book UNIQUE (course_id, isbn)
);
