ALTER TABLE courses ADD title_url_component text;
UPDATE courses SET title_url_component =  array_to_string(array_remove(regexp_split_to_array(lower(title), E'[^A-Za-z]'), ''), '-');