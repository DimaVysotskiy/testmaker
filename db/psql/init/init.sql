CREATE TYPE role_enum AS ENUM ('ADMIN', 'TEACHER', 'STUDENT');

CREATE TABLE "Users"(
    id SERIAL PRIMARY KEY,
    user_login VARCHAR(255) NOT NULL UNIQUE,
    user_role role_enum NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO "Users" (user_login, user_role, password_hash)
VALUES ('admin', 'ADMIN', '$2b$12$.ngX8xgxkJbBSfkFe7YymuEM6v0XTsly79UPMGKeopi3MXMbZx2fm'); --password=admin123
