from sqlalchemy import Column, Integer, Float, String, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from passlib.context import CryptContext # type: ignore
from database import Base
from datetime import datetime
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
    LenaLinderborg = "LenaLinderborg"
    AnastasiyaJohansson = "AnastasiyaJohansson"
    RosieRangel = "RosieRangel"
    NatashaSokolova = "NatashaSokolova"

class Entities(enum.Enum):
    user = "user"
    ai = "ai"

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

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    firstname = Column(String, nullable=True)
    lastname = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(FriendshipStatus), nullable=True)
    friendship_statistical_score = Column(Float, nullable=True)
    friendship_detail_score = Column(Float, nullable=True)
    messages = relationship("Message", back_populates="user")
    sessions = relationship("ChatSession", back_populates="user")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    sender = Column(Enum(Entities), nullable=False)
    message_text = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    user = relationship("User", back_populates="messages")

class ChatSession(Base):
    __tablename__ = "chatsessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    user = relationship("User", back_populates="sessions")

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

class MessageCreate(BaseModel):
    sender: str
    message_text: str
    timestamp: datetime = None