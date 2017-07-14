CREATE TABLE rmp_instructors (
	rmp_id int,
	instructor_id int REFERENCES instructors(id),
	name text,
	title text,
	avg_grade text,
	hotness text,
	rating_averages text[],
        ratings json,
	tags text[],
        CONSTRAINT unique_instructor UNIQUE (rmp_id)
);
