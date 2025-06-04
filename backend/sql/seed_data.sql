-- backend/sql/seed_data.sql

INSERT INTO users (username, hashed_password, is_admin)
VALUES
('admin', 'zerzerzer', TRUE),
('player1', 'tester1', FALSE);

-- Replace hash_placeholder with real bcrypt hashes later
