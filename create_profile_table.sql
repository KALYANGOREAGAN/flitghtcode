
CREATE TABLE IF NOT EXISTS accounts_userprofile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bio TEXT NOT NULL,
    profile_picture VARCHAR(100) NULL,
    user_id INTEGER NOT NULL UNIQUE REFERENCES auth_user(id)
);

