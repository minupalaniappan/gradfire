ALTER TABLE courses ADD from_transcript boolean;
UPDATE courses SET from_transcript = false where from_transcript is null;
