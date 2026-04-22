# Auth refactor: replace session tokens with JWT
import jwt

def create_token(user_id: int) -> str:
    return jwt.encode({'user_id': user_id}, 'secret', algorithm='HS256')

def verify_token(token: str) -> dict:
    return jwt.decode(token, 'secret', algorithms=['HS256'])
