-- Создание ENUM типа для ролей
CREATE TYPE user_role AS ENUM ('student', 'teacher', 'admin');

-- Создание ENUM типа для провайдеров OAuth
CREATE TYPE oauth_provider AS ENUM ('google', 'github', 'microsoft', 'local');

-- Создание таблицы пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    
    -- Основная информация
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    full_name VARCHAR(255),
    
    -- Аутентификация (для локальной регистрации)
    hashed_password VARCHAR(255),  -- NULL если OAuth
    
    -- Роль пользователя
    role user_role NOT NULL DEFAULT 'student',
    
    -- OAuth информация
    oauth_provider oauth_provider NOT NULL DEFAULT 'local',
    oauth_id VARCHAR(255),  -- ID от провайдера (Google ID, GitHub ID и т.д.)
    oauth_access_token TEXT,  -- Токен доступа от провайдера
    oauth_refresh_token TEXT,  -- Refresh токен
    oauth_token_expires_at TIMESTAMP,  -- Когда истекает токен
    
    -- Статус аккаунта
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Временные метки
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    
    -- Ограничения
    CONSTRAINT unique_oauth_provider_id UNIQUE (oauth_provider, oauth_id)
);

-- Создание индексов для быстрого поиска
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_oauth_provider ON users(oauth_provider);
CREATE INDEX idx_users_oauth_id ON users(oauth_id);
CREATE INDEX idx_users_is_active ON users(is_active);

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Вставка тестовых данных (опционально)
-- Пароль: admin123 (хеш для bcrypt)
INSERT INTO users (email, username, full_name, hashed_password, role, is_verified, is_email_verified) 
VALUES 
    ('admin@example.com', 'admin', 'System Administrator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeJFxYw1pNji', 'admin', TRUE, TRUE),
    ('teacher@example.com', 'teacher1', 'John Teacher', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeJFxYw1pNji', 'teacher', TRUE, TRUE),
    ('student@example.com', 'student1', 'Alice Student', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeJFxYw1pNji', 'student', TRUE, TRUE);

-- Пример пользователя с OAuth (Google)
INSERT INTO users (email, username, full_name, role, oauth_provider, oauth_id, avatar_url, is_verified, is_email_verified) 
VALUES 
    ('oauth.user@gmail.com', 'oauth_user', 'OAuth User', 'student', 'google', '1234567890', 'https://lh3.googleusercontent.com/...', TRUE, TRUE);

-- Комментарии к таблице и колонкам
COMMENT ON TABLE users IS 'Таблица пользователей с поддержкой OAuth2 и ролевой модели';
COMMENT ON COLUMN users.role IS 'Роль пользователя: student, teacher, admin';
COMMENT ON COLUMN users.oauth_provider IS 'Провайдер OAuth: google, github, microsoft, local';
COMMENT ON COLUMN users.oauth_id IS 'Уникальный ID пользователя от OAuth провайдера';
COMMENT ON COLUMN users.hashed_password IS 'Хешированный пароль (NULL для OAuth пользователей)';