ALTER TABLE course_answers ADD CONSTRAINT one_answer_per_user UNIQUE (question_id, user_id);
ALTER TABLE course_votes ADD CONSTRAINT one_vote_per_user UNIQUE (user_id, question_id, answer_id);