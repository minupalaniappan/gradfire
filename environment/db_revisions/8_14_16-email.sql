CREATE TABLE universities(
  id serial PRIMARY KEY,
  name text,
  city text
);

CREATE TABLE majors_v2(
  id serial PRIMARY KEY,
  university_id int REFERENCES universities,
  name text,
  variant text
);

CREATE TABLE directory_listings(
  university_id int REFERENCES universities,
  name text,
  email text,
  standing text,
  major_id int REFERENCES majors_v2
);
