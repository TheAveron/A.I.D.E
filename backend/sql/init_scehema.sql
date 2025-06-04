-- backend/sql/init_schema.sql

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

-- Add more tables here later (factions, items, offers, etc.)
