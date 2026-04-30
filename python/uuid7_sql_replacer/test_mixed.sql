INSERT INTO users (id, session_id, name, email) VALUES ('b0913943-0197-77cf-b774-9429d8fcb9b2', 'b0919cf6-0197-76e9-98d8-365837f3c55a',   'Dave',   'dave@example.com');
UPDATE users SET id = 'b0913943-0197-7fa6-a6ce-fb7e0ce99a21', session_id = 'b0919cf6-0197-74db-8a89-80bae91c366b', name = 'Dave Updated' WHERE email = 'dave@example.com';
INSERT INTO users (id, session_id, name, email) VALUES ('b0913943-0197-7a3a-a413-3c231ab6f04a', 'b0919cf6-0197-7d4a-b297-33c1b941dc94',   'Eve',   'eve@example.com');
UPDATE users SET id = 'b0913943-0197-76d5-943a-3f6882ce7f9e', session_id = 'b0919cf6-0197-754e-86a9-7e21ebafb36d', name = 'Eve Updated' WHERE email = 'eve@example.com';
