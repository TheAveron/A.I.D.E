-- backend/sql/seed_data.sql

INSERT INTO factions (
    name,
    description,
    currency_name,
    currency_amount,
    is_approved,
    created_at
) VALUES (
    'Default',
    '',
    'Diamond',
    0,
    TRUE,
    NOW()
)

-- Replace hash_placeholder with real bcrypt hashes later
