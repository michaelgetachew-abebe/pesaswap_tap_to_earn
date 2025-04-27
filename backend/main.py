from fastapi import FastAPI, Depends, WebSocket, HTTPException, WebSocketDisconnect # type: ignore
from sqlalchemy.orm import Session
import logging
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from datetime import datetime

from fastapi import FastAPI, HTTPException # type: ignore
from fastapi.responses import JSONResponse # type: ignore

from database import Base, engine, get_local_db, SessionLocal
from models import LoginRequest, LoginResponse, LogoutRequest, Agent, AgentSessionDetails, User, Message, TranslationRequest, UserORM, MessageORM, MessageResponse, ChatDetailsRequest
from auth import authenticate_agent, create_jwt_token, verify_jwt_token
from friendship import calculate_friendship_score, calculate_friendship_score_zep
from translator import translate_text
from data_extractor import extract_unread

from seed_db import seed_data

import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def on_startup():
    db: Session = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()

def handle_logout(agent_id: int, db: Session):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent:
        session_details = agent.session_details
        if session_details and session_details.recent_login:
            now = datetime.utcnow()
            if session_details.recent_login > now:
                session_duration = 0  # Prevent negative duration
            else:
                session_duration = (now - session_details.recent_login).total_seconds() / 60
            session_details.total_active_time += int(session_duration)
            session_details.recent_logout = now
        agent.online_status = False
        db.commit()

@app.post("/login", response_model=LoginResponse)
def login(login: LoginRequest, db: Session = Depends(get_local_db)):
    logger.info(f"Agent {login.agentname} attempting to login")
    agent = authenticate_agent(login, db)
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update or create session details
    session_details = agent.session_details
    now = datetime.utcnow()
    if session_details is None:
        session_details = AgentSessionDetails(id=agent.id, recent_login=now, total_active_time=0)
        db.add(session_details)
    else:
        session_details.recent_login = now
    db.commit()
    
    token = create_jwt_token(agent.id, agent.agentname, agent.persona)
    logger.info(f"Agent {agent.id} logged in successfully")
    return {"token": token, "agent": {"id": agent.id, "agentname": agent.agentname, "persona": agent.persona}}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_local_db)):
    token = websocket.query_params.get("token")
    if not token:
        logger.warning("No token provided for WebSocket connection")
        await websocket.close(code=1008)
        return
    payload = verify_jwt_token(token)
    if not payload:
        logger.warning("Invalid token for WebSocket connection")
        await websocket.close(code=1008)
        return
    agent_id = payload["agent_id"]
    agentname = payload["agentname"]
    role = payload["role"]

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        logger.warning(f"Agent {agent_id} not found")
        await websocket.close(code=1008)
        return

    agent.online_status = True
    db.commit()

    await websocket.accept()
    websocket.state.agent_id = agent_id
    websocket.state.agentname = agentname
    websocket.state.agent_role = role
    logger.info(f"Agent {agent_id} connected via WebSocket")

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Role: {role} | Message: {data}")
    except WebSocketDisconnect:
        handle_logout(agent_id, db)
        logger.info(f"Agent {agent_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket for agent {agent_id}: {e}")
        await websocket.close(code=1011)

@app.post("/logout")
def logout(logout: LogoutRequest, db: Session = Depends(get_local_db)):
    agent_id = logout.agent_id
    handle_logout(agent_id, db)
    logger.info(f"Agent {agent_id} logged out successfully")
    return {"message": "Logged out successfully"}

# New Implementations

@app.get("/messages/get/{user_id}", response_model=List[MessageResponse])
def get_messages(user_id: str, limit: int = 20, db: Session = Depends(get_local_db)):
    return db.query(MessageORM).filter_by(user_id=user_id).order_by(MessageORM.timestamp.desc()).limit(limit).all()

@app.post("/messages/", response_model=MessageResponse)
def post_message(message: Message, db: Session = Depends(get_local_db)):
    if message.sender not in ["user", "ai"]:
        raise HTTPException(status_code=400, detail="Sender must be 'user' or 'ai'")
    db_message = MessageORM(**message.dict())
    if db_message.timestamp is None:
        db_message.timestamp = datetime.utcnow()
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@app.delete("/messages/{user_id}/{message_id}", response_model=dict)
def delete_message(user_id: str, message_id: int, db: Session = Depends(get_local_db)):
    message = (db.query(MessageORM).filter_by(id=message_id, user_id=user_id)).first()

    if not message:
        raise HTTPException(status_code=404, detail=f"No message #{message_id} found for user {user_id}")
    
    db.delete(message)
    db.commit()
    return {"deleted": True}
    

@app.delete("/messages/delete/last-ai/{user_id}", response_model=dict)
def delete_latest_ai_message(user_id: str, db: Session = Depends(get_local_db)):
    # Get the most recent message sent by 'ai' for this user
    message = (
        db.query(MessageORM)
        .filter_by(user_id=user_id, sender="ai")
        .order_by(MessageORM.timestamp.desc())
        .first()
    )

    if not message:
        raise HTTPException(status_code=404, detail="No AI messages found for this user")

    db.delete(message)
    db.commit()
    return {"deleted": True, "deleted_message_id": message.id}

@app.post("/users")
def upsert_user(user: User, db: Session = Depends(get_local_db)):
    db_user = db.query(UserORM).filter_by(user_id=user.user_id).first()
    if db_user:
        for field, value in user.dict(exclude_unset=True).items():
            setattr(db_user, field, value)
    else:
        db_user = UserORM(**user.dict())
        db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}/exists", response_model=dict)
def user_exists(user_id: str, db: Session = Depends(get_local_db)):
    exists = db.query(UserORM).filter_by(user_id=user_id).first() is not None
    return {"exists": exists}


@app.get("/users/{user_id}/language", response_model=dict)
def get_user_language(user_id: str, db: Session = Depends(get_local_db)):
    user = db.query(UserORM).filter_by(user_id=user_id).first()
    if not user:
        return {"language": None}
    return {"language": user.language}

@app.post("/translate")
async def translate(req: TranslationRequest):
    translated = await translate_text(
        content=req.content,
        source_lang=req.source_lang,
        target_lang=req.target_lang
    )
    return {"translated_content": translated}


@app.get("/friendship-statistical-score/{user_id}")
def get_friendship_statistical_score(user_id: int, db: Session = Depends(get_local_db)):
    score = calculate_friendship_score(db, user_id, datetime.now(datetime.timetz.utc))
    return {"user_id": user_id, "statistical_friendship_score": score}

@app.get("/friendship-score-zep/{user_id}")
def get_friendship__score(user_id: int):
    score = calculate_friendship_score_zep(user_id=user_id)
    return {"user_id": user_id, "zep_friendship_score": score}


@app.post("/extract_chat_details")
async def extract_chat_details(request: ChatDetailsRequest):
    try:
        result = await extract_unread(input_html=request.request)
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Invalid JSON response from OpenRouter API")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Response validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")