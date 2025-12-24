from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class OAuthProvider(str, Enum):
    GOOGLE = "google"
    GITHUB = "github"
    LOCAL = "local"