CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id int REFERENCES students,
    created_at timestamp DEFAULT now(),
    type text,
    read boolean DEFAULT false,
    data jsonb
);