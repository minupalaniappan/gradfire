alter table courses_prerequisites rename subject to req_subject;
alter table courses_prerequisites rename number to req_number;
alter table courses_prerequisites add subject text;;
alter table courses_prerequisites add number text;
alter table courses_prerequisites add term_year int;
alter table courses_prerequisites add term_month int;
update courses_prerequisites set subject = (SELECT subject FROM courses WHERE id = course_id),
    number = (SELECT number FROM courses WHERE id = course_id),
    term_year = (SELECT term_year FROM courses WHERE id = course_id),
    term_month = (SELECT term_month FROM courses WHERE id = course_id);
alter table courses_prerequisites drop course_id;

CREATE INDEX courses_prerequisites_subj_num ON courses_prerequisites (subject, number);

ALTER TABLE course_answers DROP CONSTRAINT course_answers_question_id_fkey;
ALTER TABLE course_answers ADD CONSTRAINT course_answers_question_id_fkey
    FOREIGN KEY (question_id) REFERENCES course_questions(id) ON DELETE CASCADE;

ALTER TABLE course_votes DROP CONSTRAINT course_votes_answer_id_fkey;
ALTER TABLE course_votes ADD CONSTRAINT course_votes_answer_id_fkey
    FOREIGN KEY (answer_id) REFERENCES course_answers(id) ON DELETE CASCADE;

ALTER TABLE course_votes DROP CONSTRAINT course_votes_question_id_fkey;
ALTER TABLE course_votes ADD CONSTRAINT course_votes_question_id_fkey
    FOREIGN KEY (question_id) REFERENCES course_questions(id) ON DELETE CASCADE;

ALTER TABLE course_answers DROP CONSTRAINT one_answer_per_user;
ALTER TABLE course_answers ADD CONSTRAINT one_answer_per_user UNIQUE (question_id, user_id, deleted);