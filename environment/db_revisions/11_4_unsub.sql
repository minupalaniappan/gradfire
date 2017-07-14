CREATE TABLE unsubscribe (id SERIAL PRIMARY KEY,
email text,
timestamp timestamp default now()
);