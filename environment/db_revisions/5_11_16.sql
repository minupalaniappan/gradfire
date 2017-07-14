ALTER TABLE course_questions ADD deleted boolean DEFAULT false;
ALTER TABLE course_answers ADD deleted boolean DEFAULT false;
ALTER TABLE course_questions DROP CONSTRAINT unique_question;
ALTER TABLE course_questions ADD CONSTRAINT unique_question UNIQUE(user_id, question, subject, number, deleted);