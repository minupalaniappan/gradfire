CREATE TABLE course_advice (
    id SERIAL PRIMARY KEY,
    user_id int REFERENCES students,
    subject text,
    number text,
    title text,
    term_year int,
    term_month int,
    advice text,
    timestamp timestamp DEFAULT now(),
    deleted boolean default false,
    CONSTRAINT unique_advice UNIQUE (user_id, subject, number, title, advice)
);

CREATE TABLE users_saved_advice (
    user_id int REFERENCES students,
    advice_id int REFERENCES course_advice,
    timestamp timestamp DEFAULT now()
);