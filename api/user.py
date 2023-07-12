from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from cache import redis_client
from database.orm import User
from database.repository import UserRepository
from schema.request import SignUpRequest, LogInRequest, CreateOTPRequest, VerifyOTPRequest
from schema.response import UserSchema, JWTResponse
from security import get_access_token
from service.user import UserService

router = APIRouter(prefix="/users")


@router.post("/sign-up", status_code=201)
def user_sign_up_handler(
    request: SignUpRequest,
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    hashed_password: str = user_service.hash_password(
        plain_password=request.password
    )
    user: User = User.create(
        username=request.username, hashed_password=hashed_password
    )
    user: User = user_repo.save_user(user=user)  # id=int
    return UserSchema.from_orm(user)


@router.post("/log-in")
def user_log_in_handler(
    request: LogInRequest,
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    user: User | None = user_repo.get_user_by_username(
        username=request.username
    )
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    verified: bool = user_service.verify_password(
        plain_password=request.password,
        hashed_password=user.password,
    )
    if not verified:
        raise HTTPException(status_code=401, detail="Not Authorized")

    access_token: str = user_service.create_jwt(username=user.username)
    return JWTResponse(access_token=access_token)

# 회원가입(username, password) / 로그인
# 이메일 알림: 회원가입 -> 이메일 인증(otp) -> 유저 이메일 저장 -> 이메일 알림

# POST /users/email/otp -> otp(key: email, value: 1234, exp: 3min)
# POST /users/email/otp/verify -> request(email, otp) -> user(email)


@router.post("/email/otp")
def create_otp_handler(
    request: CreateOTPRequest,
    _: str = Depends(get_access_token),
    user_service: UserService = Depends(),
):
    otp: int = user_service.create_otp()
    redis_client.set(request.email, otp)
    redis_client.expire(request.email, 3 * 60)

    # send otp to email
    return {"otp": otp}


@router.post("/email/otp/verify")
def verify_otp_handler(
    request: VerifyOTPRequest,
    background_tasks: BackgroundTasks,
    access_token: str = Depends(get_access_token),
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    otp: str | None = redis_client.get(request.email)
    if not otp:
        raise HTTPException(status_code=400, detail="Bad Request")

    if request.otp != int(otp):
        raise HTTPException(status_code=400, detail="Bad Request")

    username: str = user_service.decode_jwt(access_token=access_token)
    user: User | None = user_repo.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    # save email to user

    # send email to user
    background_tasks.add_task(
        user_service.send_email_to_user,
        email="admin@fastapi.com"
    )
    return UserSchema.from_orm(user)


# Server        Request -> verify otp -> Response
# Background                                    -> send email(10s)
