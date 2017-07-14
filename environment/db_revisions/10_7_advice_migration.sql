INSERT INTO course_advice (user_id, subject, number, title, advice, timestamp, deleted) (
    SELECT ans.user_id,
        subject,
        number,
        (SELECT title FROM courses WHERE courses.subject = q.subject AND courses.number = q.number
            ORDER BY term_year DESC, term_month DESC LIMIT 1),
        answer,
        ans.timestamp,
        ans.deleted
    FROM course_answers ans
    JOIN students ON students.name = 'Discourse' and students.email = 'team@gradfire.com'
    JOIN course_questions q ON ans.question_id = q.id AND q.user_id = students.id
);

UPDATE course_questions SET deleted = true
 WHERE user_id = (SELECT id FROM students
    WHERE students.name = 'Discourse' and students.email = 'team@gradfire.com');