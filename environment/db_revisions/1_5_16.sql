ALTER TABLE courses ADD title_desc_tsv tsvector;
UPDATE courses SET title_desc_tsv = setweight(to_tsvector(coalesce(title,'')), 'A') || setweight(to_tsvector(coalesce(description,'')), 'B');
