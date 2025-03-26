from fastapi import FastAPI, Depends, WebSocket, HTTPException, WebSocketDisconnect # type: ignore
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import LoginRequest, LoginResponse, LogoutRequest, Agent, AgentSessionDetails
from auth import authenticate_agent, create_jwt_token, verify_jwt_token
import logging
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://pocjldbpinmlaekfdloponfhainfipkl",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

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