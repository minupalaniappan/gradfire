INSERT INTO course_questions (user_id, votable, question, subject, number, term_year, term_month)
 (SELECT 756, false, 'What advice do you have for students who want to take this class?', subject, number,
 2016, 10 FROM courses WHERE from_transcript = false GROUP BY subject, number) RETURNING id;

