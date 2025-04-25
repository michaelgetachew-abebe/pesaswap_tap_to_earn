from sqlalchemy import Column, Integer, Float, String, Enum, Boolean, DateTime, ForeignKey, CheckConstraint, Index, desc
from sqlalchemy.orm import relationship
from pydantic import BaseModel, field_validator
from passlib.context import CryptContext #type: ignore
from database import Base, Base2  # Import Base2 for Supabase models
from datetime import datetime
from typing import Optional
import enum

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class FriendshipStatus(enum.Enum):
    Early = "Early"
    Moderate = "Moderate"
    Good = "Good"
    Best = "Best"
    Sext = "Sext"

class Personas(enum.Enum):
    Emilianilson = "Emilianilson"
    ValentinaSokolova = "ValentinaSokolova"
    TinaStewart = "TinaStewart"
    LisaWilliams = "LisaWilliams"
    AshlynnReyes = "AshlynnReyes"
    AnnaVasilenko = "AnnaVasilenko"
    AmeliaNixon = "AmeliaNixon"
    LenaLindberg = "LenaLindberg"
    AnastasiyaJohansson = "AnastasiyaJohansson"
    RosieRangel = "RosieRangel"
    NatashaSokolova = "NatashaSokolova"

class Entities(enum.Enum):
    user = "user"
    ai = "ai"

# Local Database Models (using Base)
class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    agentname = Column(String, nullable=False)
    password = Column(String, nullable=False)
    persona = Column(Enum(Personas), nullable=False)
    online_status = Column(Boolean, default=False)
    session_details = relationship("AgentSessionDetails", uselist=False, back_populates="agent")

class AgentSessionDetails(Base):
    __tablename__ = "agent_session_details"
    id = Column(Integer, ForeignKey('agents.id'), primary_key=True)
    recent_login = Column(DateTime, nullable=True)
    recent_logout = Column(DateTime, nullable=True)
    total_active_time = Column(Integer, default=0)
    agent = relationship("Agent", back_populates="session_details")
    
class UserORM(Base):
    __tablename__ = "users"
    user_id = Column(String(255), primary_key=True)
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    sex = Column(String, nullable=True)
    language = Column(String, nullable=True)
    alias = Column(String, nullable=True)
    geography = Column(String, nullable=True)
    messages = relationship("MessageORM", order_by="MessageORM.timestamp", back_populates="user")

class MessageORM(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    sender = Column(String(10), nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("UserORM", back_populates="messages")
    __table_args__ = (
    CheckConstraint("sender IN ('user', 'ai')", name="check_sender"),
    Index('idx_messages_user_id_timestamp', 'user_id', desc('timestamp')),
)

# Pydantic Models for API
class LoginRequest(BaseModel):
    agentname: str
    password: str

class LogoutRequest(BaseModel):
    agent_id: int

class AgentInfo(BaseModel):
    id: int
    agentname: str
    persona: str

class LoginResponse(BaseModel):
    token: str
    agent: AgentInfo

class User(BaseModel):
    user_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    language: Optional[str] = None
    alias: Optional[str] = None
    geography: Optional[str] = None

class TranslationRequest(BaseModel):
    content: str
    source_lang: str
    target_lang: str

class Message(BaseModel):
    user_id: str
    sender: str  # 'user' or 'ai'
    content: str
    timestamp: Optional[datetime] = None

    @field_validator('sender')
    def sender_must_be_user_or_ai(cls, v):
        if v not in ['user', 'ai']:
            raise ValueError('sender must be "user" or "ai"')
        return v

class MessageResponse(BaseModel):
    id: int
    user_id: str
    sender: str
    content: str  # <- match the ORM model
    timestamp: datetime

    class Config:
        from_attributes = True


class ChatDetailsRequest(BaseModel):
    request: str