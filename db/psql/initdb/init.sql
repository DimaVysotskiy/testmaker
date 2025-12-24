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
    file_urls TEXT[],
    photo_urls TEXT[],

    lesson_name VARCHAR(255) NOT NULL,
    lesson_type lesson_type NOT NULL,
    checker INTEGER NOT NULL REFERENCES users(id),

    specialty VARCHAR(255) NOT NULL,
    course INT NOT NULL,

    deadline TIMESTAMP NOT NULL
);




CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lectures_updated_at BEFORE UPDATE ON lectures FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_practices_updated_at BEFORE UPDATE ON practices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lab_works_updated_at BEFORE UPDATE ON lab_works FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_student_group ON student_info(group_id);
CREATE INDEX idx_lectures_specialty_course ON lectures(specialty_id, course_number);
CREATE INDEX idx_practices_specialty_course ON practices(specialty_id, course_number);
CREATE INDEX idx_labs_specialty_course ON lab_works(specialty_id, course_number);
CREATE INDEX idx_submissions_type_id ON activity_submissions(type, activity_id);