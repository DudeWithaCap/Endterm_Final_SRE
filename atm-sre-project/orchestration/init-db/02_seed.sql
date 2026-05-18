-- Seed users
-- PINs: alice=1234, bob=5678, charlie=9999, diana=1111, eve=2222
-- Hashes generated with bcrypt (cost=12)
INSERT INTO users (account_number, name, pin_hash) VALUES
  ('ACC0000001', 'Alice Johnson',   '$2b$12$ypN3YBfY2A9PittIn59p2es3yyFJlc.HBj7/Xknp2/kMPQt0oPFfq'),
  ('ACC0000002', 'Bob Smith',       '$2b$12$Xy1XyZakkMUw2cQFt29jp.FIMKc6Sx73lFrYjZcF0YRhzlOICX9Su'),
  ('ACC0000003', 'Charlie Brown',   '$2b$12$57SwliR5XUjBwDgKZ9m1FeF2NOcLXAD.A2C7ivX81TDTnYXYGPs4O'),
  ('ACC0000004', 'Diana Prince',    '$2b$12$S.zks1QXU3uq9gti4WNnvuRwJVtp1lpnprfEsJ5m6h/zrTD05qhzC'),
  ('ACC0000005', 'Eve Davis',       '$2b$12$zqoHT6Dj3DYAUDKHvIch0.Hvi2nRFxXMsAS0KzbIhMgX87jZ5EQEa')
ON CONFLICT (account_number) DO NOTHING;

-- Seed accounts (linked to users above)
INSERT INTO accounts (user_id, account_number, balance, currency) VALUES
  (1, 'ACC0000001', 5000.00,  'USD'),
  (2, 'ACC0000002', 12500.50, 'USD'),
  (3, 'ACC0000003', 750.25,   'USD'),
  (4, 'ACC0000004', 99999.99, 'USD'),
  (5, 'ACC0000005', 200.00,   'USD')
ON CONFLICT (account_number) DO NOTHING;

-- Seed cards
INSERT INTO cards (account_number, card_number, is_blocked, daily_limit) VALUES
  ('ACC0000001', '4111-1111-1111-0001', FALSE, 2000.00),
  ('ACC0000002', '4111-1111-1111-0002', FALSE, 5000.00),
  ('ACC0000003', '4111-1111-1111-0003', FALSE, 1000.00),
  ('ACC0000004', '4111-1111-1111-0004', FALSE, 10000.00),
  ('ACC0000005', '4111-1111-1111-0005', TRUE,  500.00)
ON CONFLICT (card_number) DO NOTHING;
