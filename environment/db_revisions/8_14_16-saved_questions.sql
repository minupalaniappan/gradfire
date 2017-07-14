CREATE TABLE users_saved_questions (
  user_id int REFERENCES students,
  question_id int REFERENCES course_questions,
  saved_on timestamp default now(),
  CONSTRAINT unique_saved_question UNIQUE (user_id, question_id)
);
