from backend.utils.security import (
    create_access_token,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
    verify_reset_token,
)


class SecurityPasswordService:
    def hash_password(self, password: str) -> str:
        return hash_password(password)

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        return verify_password(plain_password, password_hash)

    def generate_reset_token(self) -> str:
        return generate_reset_token()

    def hash_reset_token(self, token: str) -> str:
        return hash_reset_token(token)

    def verify_reset_token(self, plain_token: str, token_hash: str) -> bool:
        return verify_reset_token(plain_token, token_hash)


class JwtAccessTokenProvider:
    def create_access_token(self, *, subject: str) -> str:
        return create_access_token(data={"sub": subject})
