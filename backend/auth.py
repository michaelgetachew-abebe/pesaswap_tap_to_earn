from passlib.context import CryptContext # type: ignore
import jwt # type: ignore
from datetime import datetime, timedelta
from fastapi import HTTPException # type: ignore
from sqlalchemy.orm import Session
from models import LoginRequest, Agent
from models import Personas

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration (store SECRET_KEY securely in production)
SECRET_KEY = "CONERED"
ALGORITHM = "HS256"
TOKEN_EXPIRATION = 24

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_agent(login: LoginRequest, db: Session) -> Agent:
    agent = db.query(Agent).filter(Agent.agentname == login.agentname).first()
    if not agent or not verify_password(login.password, agent.password):
        raise HTTPException(status_code=401, detail="Invalid agent ID or password")
    return agent

def create_jwt_token(agent_id: int, agentname: str, persona: Personas) -> str:
    expiration = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION)
    payload = {"agent_id": agent_id, "agentname": agentname, "role": persona.value, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
