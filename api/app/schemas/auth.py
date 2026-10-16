from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    turnstile_token: str | None = None
    referral_code: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str
    turnstile_token: str | None = None


class ProfileUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None

    @field_validator("username")
    @classmethod
    def username_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Username cannot be empty")
        return value.strip() if value else value


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_min_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("New password must be at least 8 characters")
        return value
