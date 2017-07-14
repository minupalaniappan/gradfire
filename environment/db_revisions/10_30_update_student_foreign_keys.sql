ALTER TABLE course_advice DROP CONSTRAINT course_advice_user_id_fkey;
ALTER TABLE course_advice ADD CONSTRAINT course_advice_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE course_answers DROP CONSTRAINT course_answers_user_id_fkey;
ALTER TABLE course_answers ADD CONSTRAINT course_answers_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE course_questions DROP CONSTRAINT course_questions_user_id_fkey;
ALTER TABLE course_questions ADD CONSTRAINT  course_questions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE course_votes DROP CONSTRAINT course_votes_user_id_fkey;
ALTER TABLE course_votes ADD CONSTRAINT  course_votes_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE courses_notes DROP CONSTRAINT courses_notes_user_id_fkey;
ALTER TABLE courses_notes ADD CONSTRAINT  courses_notes_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE notifications DROP CONSTRAINT notifications_user_id_fkey;
ALTER TABLE notifications ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE users_saved_advice DROP CONSTRAINT users_saved_advice_user_id_fkey;
ALTER TABLE users_saved_advice ADD CONSTRAINT users_saved_advice_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE users_saved_questions DROP CONSTRAINT users_saved_questions_user_id_fkey;
ALTER TABLE users_saved_questions ADD CONSTRAINT  users_saved_questions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

