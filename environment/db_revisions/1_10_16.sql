CREATE TABLE courses_grades (
  term_year int,
  term_month int,
  subject varchar(3),
  number text,
  title text,
  instructor text,
  letter varchar(2),
  count int
);

ALTER TABLE courses_grades ADD CONSTRAINT unique_grade UNIQUE (term_year, term_month, subject, number, title, instructor, letter);