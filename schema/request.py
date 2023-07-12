from pydantic import BaseModel


class CreateToDoRequest(BaseModel):
    contents: str
    is_done: bool


class SignUpRequest(BaseModel):
    username: str
    password: str


class LogInRequest(BaseModel):
    username: str
    password: str


class CreateOTPRequest(BaseModel):
    email: str


class VerifyOTPRequest(BaseModel):
    email: str
    otp: int
