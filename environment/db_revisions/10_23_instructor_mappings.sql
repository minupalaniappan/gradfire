CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email text,
    password_checksum text,
    name text,
    common_names text[],
    is_admin boolean DEFAULT false,
    session_token_checksum text,
    verified boolean DEFAULT false,
    verification_code text,
    salt text,
    password_reset_token text,
    signup_time timestamp without time zone default now(),
    role text,
    session_token_checksums text[] DEFAULT ARRAY[]::text[],
    google_id_token text,
    google_id_sub text,
    given_name text,
    family_name text,
    locale text,
    CONSTRAINT unique_user UNIQUE (email)
);

CREATE TABLE students_new (
    user_id int primary key REFERENCES users,
    transcript_needs_update boolean DEFAULT true
);

INSERT INTO users (id,
    email,
    password_checksum,
    name,
    is_admin,
    verified,
    verification_code,
    salt,
    password_reset_token,
    signup_time,
    role,
    session_token_checksums)
SELECT students.id,
    students.email,
    students.password_checksum,
    students.name,
    students.is_admin,
    students.verified,
    students.verification_code,
    students.salt,
    students.password_reset_token,
    students.signup_time,
    students.role,
    students.session_token_checksums FROM students;

ALTER TABLE students RENAME TO students_dep;
ALTER TABLE students_new RENAME TO students;

INSERT INTO students (user_id, transcript_needs_update)
SELECT id, true FROM users WHERE role = 'student';

ALTER TABLE instructors ADD user_id int REFERENCES users;

-- Many-many relationship between courses and instructors

CREATE TABLE courses_instructors(course_id int REFERENCES courses,
    instructor_id int REFERENCES instructors,
    CONSTRAINT unique_course_instructor UNIQUE (course_id, instructor_id));

-- TODO copy instructor_id from courses into courses_instructors
