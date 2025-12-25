CREATE TYPE user_role AS ENUM ('STUDENT', 'TEACHER', 'ADMIN');
CREATE TYPE oauth_provider AS ENUM ('GOOGLE', 'GITHUB', 'LOCAL');
CREATE TYPE lesson_type AS ENUM ('LECTURE', 'PRACTICE', 'LAB');


CREATE TABLE users (
    id SERIAL PRIMARY KEY,

    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    role user_role NOT NULL DEFAULT 'STUDENT',

    oauth_provider oauth_provider NOT NULL DEFAULT 'LOCAL',
    oauth_id VARCHAR(255),
    oauth_access_token TEXT,
    oauth_refresh_token TEXT,
    oauth_token_expires_at TIMESTAMP,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,

    CONSTRAINT unique_oauth_provider_id UNIQUE (oauth_provider, oauth_id)
);



CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,

    title VARCHAR(255) UNIQUE NOT NULL,
    description TEXT NOT NULL, -- В описание можно оставить ссылки на доп материалы
    files_metadata JSONB DEFAULT '[]'::jsonb,
    photos_metadata JSONB DEFAULT '[]'::jsonb,

    lesson_name VARCHAR(255) NOT NULL,
    lesson_type lesson_type NOT NULL,
    checker INTEGER NOT NULL REFERENCES users(id),

    specialty VARCHAR(255) NOT NULL,
    course INT NOT NULL,

    deadline TIMESTAMP
);

INSERT INTO users (email, username, hashed_password, role, is_verified, is_email_verified) 
VALUES 
('admin@example.com', 'admin', '$argon2id$v=19$m=65536,t=3,p=4$gDa6b58Z0M14aO/PAMe4MQ$gjkvtMJH1VjRRHsSRT0ZW6Acxlclo2vv5UjyXhzOiNE', 'ADMIN', TRUE, TRUE),
('teacher@example.com', 'teacher1', '$argon2id$v=19$m=65536,t=3,p=4$gDa6b58Z0M14aO/PAMe4MQ$gjkvtMJH1VjRRHsSRT0ZW6Acxlclo2vv5UjyXhzOiNE', 'TEACHER', TRUE, TRUE),
('student@example.com', 'student1', '$argon2id$v=19$m=65536,t=3,p=4$gDa6b58Z0M14aO/PAMe4MQ$gjkvtMJH1VjRRHsSRT0ZW6Acxlclo2vv5UjyXhzOiNE', 'STUDENT', TRUE, TRUE);



CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();



CREATE TYPE answer_status AS ENUM ('SUBMITTED', 'GRADED', 'RETURNED');

CREATE TABLE answers (
    id SERIAL PRIMARY KEY,

    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    message TEXT NOT NULL,
    files_metadata JSONB DEFAULT '[]'::jsonb,
    photos_metadata JSONB DEFAULT '[]'::jsonb,

    status answer_status NOT NULL DEFAULT 'SUBMITTED',
    grade INTEGER CHECK (grade >= 0 AND grade <= 100),
    teacher_comment TEXT,

    add_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    graded_at TIMESTAMP,

    -- Студент может отправить только один ответ на задание
    CONSTRAINT unique_student_task UNIQUE (task_id, student_id)
);

-- Индексы для быстрого поиска
CREATE INDEX idx_answers_task_id ON answers(task_id);
CREATE INDEX idx_answers_student_id ON answers(student_id);
CREATE INDEX idx_answers_status ON answers(status);
CREATE INDEX idx_answers_add_at ON answers(add_at);