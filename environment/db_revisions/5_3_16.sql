CREATE TABLE course_questions
    (id SERIAL PRIMARY KEY,
     subject text,
     number text,
     term_year int,
     term_month int,
     user_id int REFERENCES students(id),
     question text,
     timestamp timestamp default (now())
     );

CREATE TABLE course_answers
    (id SERIAL PRIMARY KEY,
     question_id int REFERENCES course_questions(id),

     user_id int REFERENCES students(id),
     answer text,
     timestamp timestamp default (now())
     );

CREATE TABLE course_votes
    (vote smallint,
     user_id int REFERENCES students(id),
     question_id int REFERENCES course_questions(id), -- Vote is either for a question
     answer_id int REFERENCES course_answers(id), -- Or for an answer
     timestamp timestamp default (now())
    );
ALTER TABLE course_votes ADD CONSTRAINT question_or_answer_only_one
    CHECK ((question_id IS NOT NULL and answer_id IS NULL)
            OR (question_id IS NULL and answer_id IS NOT NULL));

ALTER TABLE students ADD role text;
UPDATE students SET role = 'students';
ALTER TABLE course_questions ADD votable boolean DEFAULT true;