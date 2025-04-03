from fastapi import FastAPI, Depends, WebSocket, HTTPException, WebSocketDisconnect # type: ignore
from sqlalchemy.orm import Session
import logging
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from datetime import datetime

from database import Base, engine, get_db, SessionLocal
from models import LoginRequest, LoginResponse, LogoutRequest, MessageCreate, Agent, AgentSessionDetails, User, Message
from auth import authenticate_agent, create_jwt_token, verify_jwt_token
from friendship import calculate_friendship_score, calculate_friendship_score_zep

from seed_db import seed_data

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
def login(login: LoginRequest, db: Session = Depends(get_db)):
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
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
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
def logout(logout: LogoutRequest, db: Session = Depends(get_db)):
    agent_id = logout.agent_id
    handle_logout(agent_id, db)
    logger.info(f"Agent {agent_id} logged out successfully")
    return {"message": "Logged out successfully"}

@app.post("/messages/{user_id}")
def create_message(user_id: int, message: MessageCreate, db: Session = Depends(get_db)):
    # Just for now nut remove it for future
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check consistency of server and frontend timestamps
    db_message = Message(
        user_id=user_id,
        sender=message.sender,
        message_text=message.message_text,
        timestamp=message.timestamp
    )

    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    return {"id": db_message.id, "user_id": user_id, "sender": message.sender, "message": message.message_text, "timestamp": message.timestamp}


@app.get("/check_new_user/{user_id}") # Check if the user is new or not - > * If new * If not new
def check_new_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        user = User(
            user_id=user_id
        )

        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        return {"user": "exists"}


@app.get("/friendship-statistical-score/{user_id}")
def get_friendship_statistical_score(user_id: int, db: Session = Depends(get_db)):
    score = calculate_friendship_score(db, user_id, datetime.now(datetime.timetz.utc))
    return {"user_id": user_id, "statistical_friendship_score": score}

@app.get("/friendship-score-zep/{user_id}")
def get_friendship__score(user_id: int):
    score = calculate_friendship_score_zep(user_id=user_id)
    return {"user_id": user_id, "zep_friendship_score": score}