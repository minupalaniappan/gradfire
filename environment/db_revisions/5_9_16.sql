ALTER TABLE course_questions ADD CONSTRAINT unique_question UNIQUE (user_id, question, subject, number);
ALTER TABLE course_votes ADD CONSTRAINT one_question_vote_per_user UNIQUE (user_id, question_id);
ALTER TABLE course_votes ADD CONSTRAINT one_answer_vote_per_user UNIQUE (user_id, answer_id);
ALTER TABLE course_votes DROP CONSTRAINT one_vote_per_user;