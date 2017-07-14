ALTER TABLE students_programs ADD timestamp timestamp DEFAULT now(),
ALTER TABLE students_programs ADD expired boolean default false;