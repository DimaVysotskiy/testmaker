from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class OAuthProvider(str, Enum):
    GOOGLE = "google"
    GITHUB = "github"
    LOCAL = "local"


class LessonType(str, Enum):
    LECTURE = "LECTURE"
    PRACTICE = "PRACTICE"
    LAB = "LAB"

class AnswerStatus(str, Enum):
    SUBMITTED = "SUBMITTED"  # Отправлено на проверку
    GRADED = "GRADED"        # Оценено
    RETURNED = "RETURNED"  