-- on a fresh installation, run cat schema.sql | psql postgres

CREATE DATABASE davis_course_search;
\c davis_course_search

CREATE TABLE students (
	id SERIAL PRIMARY KEY,
	name text,
	email text,
	password_checksum text,
	salt text,
	major_ids int[],
	verified boolean DEFAULT false,
	verification_code text,
	CONSTRAINT unique_student UNIQUE (email)
);

CREATE TABLE sessions (
	student_id int REFERENCES students,
	token_checksum text,
	expires timestamp
);

CREATE TABLE students_added_courses (
	student_id int REFERENCES students,
	course_id int REFERENCES courses,
	CONSTRAINT unique_added_course UNIQUE (student_id, course_id)
);

CREATE TABLE instructors (
	id SERIAL PRIMARY KEY,
	name text);

CREATE TABLE majors(
	id SERIAL PRIMARY KEY,
	name text,
  variant text,
  requirements_json text,
	CONSTRAINT unique_major_variants UNIQUE (name, variant));

CREATE TABLE majors_required_courses(
	major_id int REFERENCES majors,
	subject text,
	number text,
	is_hard_requirement boolean,
	CONSTRAINT unique_requirement UNIQUE (major_id, subject, number, is_hard_requirement)
);

CREATE TABLE courses (
	id SERIAL PRIMARY KEY,
 	term_year smallint,
 	term_month smallint,
 	crn varchar(10),
 	units_low float,
 	units_hi float,
 	subject varchar(3),
 	max_enrollment smallint,
 	number text,
 	title text,
 	available_seats smallint,
 	instructor_id int REFERENCES instructors(id),
 	description text,
 	section text,
 	drop_time smallint,
 	prerequisites text,
 	prerequisite_tree text,
 	ge_areas text[],
 	CONSTRAINT unique_course UNIQUE (term_year, term_month, crn)
);

CREATE INDEX course_subject_number ON courses(subject, number);

CREATE TABLE courses_textbooks (
	course_id int REFERENCES courses,
	isbn text,
	CONSTRAINT unique_book UNIQUE (course_id, isbn)
);

CREATE TABLE course_affiliate_offers (
	isbn text REFERENCES courses_textbooks(isbn),
	merchant_name text,
	url text,
	author text,
	brand text,
	edition text,
	lowest_new_price text,
	lowest_used_price text
);

CREATE TABLE courses_prerequisites(
	id SERIAL PRIMARY KEY,
	course_id int REFERENCES courses,
	parent_req int REFERENCES courses_prerequisites,
	rel varchar(3),
	subject varchar(3),
	number text
);

CREATE TABLE students_completed_courses(
	student_id int REFERENCES students,
	course_id int REFERENCES courses,
	units float,
	letter_grading boolean,
	ge_areas text[],
	from_transcript boolean,
	CONSTRAINT unique_completed_course UNIQUE (student_id, course_id));

CREATE TABLE students_tentative_courses(
	student_id int REFERENCES students,
	course_id int REFERENCES courses,
	units float,
	ge_areas text[],
	from_transcript boolean,
	CONSTRAINT unique_tentative_course UNIQUE (student_id, course_id));

CREATE TABLE students_course_equivalences(
	student_id int REFERENCES students,
	subject text,
	number text,
	course_exists boolean,
	description text, -- APCA - ADV PLAC Computer Science A (score: 5) 2.00  P
	term_year int,				 -- May break this down into 'code' and 'description'
	term_month int,
	units float,
	grade text,
	ge_areas text[],
	from_transcript boolean,
	CONSTRAINT unique_course_equivalence UNIQUE (student_id, subject, number, term_year, term_month));

CREATE TABLE students_ge_progress(
	student_id int REFERENCES students,
	ge_area text,
	category text,
	units float,
	is_complete boolean,
	CONSTRAINT unique_completed_course UNIQUE (student_id, ge_area));

CREATE TABLE ge_areas(
	id SERIAL PRIMARY KEY,
	name text,
	min_units float);

CREATE TABLE meetings (
	id SERIAL PRIMARY KEY,
	course_id int REFERENCES courses(id),
	start_time time,
	end_time time,
	time_tba boolean,
	location text,
	monday boolean,
	tuesday boolean,
	wednesday boolean,
	thursday boolean,
	friday boolean,
	saturday boolean,
	CONSTRAINT unique_meeting UNIQUE (course_id, start_time,
		end_time, time_tba,
		location, monday,
		tuesday, wednesday,
		thursday, friday, saturday)
	);

CREATE USER dcs WITH PASSWORD 'Y3NxsYo8JNjARJ';
GRANT ALL PRIVILEGES on database davis_course_search to dcs;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dcs;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dcs;