from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from passlib.context import CryptContext # type: ignore
from database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    agentname = Column(String, nullable=False)
    password = Column(String, nullable=False)
    persona = Column(Enum("Natasha Sokolova", "persona_2", "persona_3", "persona_4", "persona_5", name="agent_persona"), nullable=False)
    online_status = Column(Boolean, default=False)
    session_details = relationship("AgentSessionDetails", uselist=False, back_populates="agent")

class AgentSessionDetails(Base):
    __tablename__ = "agent_session_details"
    id = Column(Integer, ForeignKey('agents.id'), primary_key=True)
    recent_login = Column(DateTime, nullable=True)
    recent_logout = Column(DateTime, nullable=True)
    total_active_time = Column(Integer, default=0)
    agent = relationship("Agent", back_populates="session_details")

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