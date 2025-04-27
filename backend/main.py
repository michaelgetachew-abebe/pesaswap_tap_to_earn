import logging
import json
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Depends, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import asyncio

from database import Base, engine, get_local_db, SessionLocal
from models import (
    LoginRequest, LoginResponse, LogoutRequest, Agent, AgentSessionDetails, 
    User, Message, TranslationRequest, UserORM, MessageORM, MessageResponse, 
    ChatDetailsRequest
)
from auth import authenticate_agent, create_jwt_token, verify_jwt_token
from friendship import calculate_friendship_score, calculate_friendship_score_zep
from translator import translate_text
from data_extractor import extract_unread
from seed_db import seed_data

from fastapi import FastAPI, Header, HTTPException
import logging

app = FastAPI()

# Configure logging with detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(name)s | %(module)s:%(lineno)d | %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Verbose FastAPI Backend", version="1.0.0")
logger.info("FastAPI application initialized")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured with allow_origins='*', allow_credentials=True, allow_methods='*', allow_headers='*'")

# Create database tables
logger.debug("Creating database tables if they do not exist")
Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

@app.on_event("startup")
def on_startup():
    logger.info("Application startup event triggered")
    db: Session = SessionLocal()
    try:
        logger.debug("Seeding database with initial data")
        seed_data(db)
        logger.info("Database seeding completed successfully")
    except Exception as e:
        logger.error(f"Failed to seed database: {str(e)}", exc_info=True)
        raise
    finally:
        logger.debug("Closing database session after startup")
        db.close()
        logger.info("Database session closed")

def handle_logout(agent_id: int, db: Session):
    logger.info(f"Handling logout for agent_id={agent_id}")
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            logger.warning(f"Agent with id={agent_id} not found during logout")
            return

        logger.debug(f"Agent found: agent_id={agent.id}, agentname={agent.agentname}")
        session_details = agent.session_details
        if session_details and session_details.recent_login:
            now = datetime.utcnow()
            logger.debug(f"Calculating session duration. Recent login: {session_details.recent_login}, Current time: {now}")
            if session_details.recent_login > now:
                session_duration = 0
                logger.warning(f"Recent login time {session_details.recent_login} is in the future. Setting session duration to 0")
            else:
                session_duration = (now - session_details.recent_login).total_seconds() / 60
                logger.info(f"Session duration calculated: {session_duration:.2f} minutes")
            session_details.total_active_time += int(session_duration)
            session_details.recent_logout = now
            logger.debug(f"Updated session details: total_active_time={session_details.total_active_time}, recent_logout={now}")

        agent.online_status = False
        logger.debug(f"Setting agent online_status to False for agent_id={agent_id}")
        db.commit()
        logger.info(f"Logout completed successfully for agent_id={agent_id}")
    except Exception as e:
        logger.error(f"Error during logout for agent_id={agent_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise

@app.post("/login", response_model=LoginResponse)
def login(login: LoginRequest, db: Session = Depends(get_local_db)):
    logger.info(f"Login attempt for agentname={login.agentname}")
    try:
        logger.debug(f"Authenticating agent with credentials: agentname={login.agentname}")
        agent = authenticate_agent(login, db)
        if not agent:
            logger.warning(f"Authentication failed for agentname={login.agentname}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        logger.info(f"Agent authenticated successfully: agent_id={agent.id}, agentname={agent.agentname}")
        session_details = agent.session_details
        now = datetime.utcnow()
        if session_details is None:
            logger.debug(f"No existing session details for agent_id={agent.id}. Creating new session details")
            session_details = AgentSessionDetails(id=agent.id, recent_login=now, total_active_time=0)
            db.add(session_details)
        else:
            logger.debug(f"Updating recent_login for existing session_details to {now}")
            session_details.recent_login = now
        db.commit()
        logger.info(f"Session details updated for agent_id={agent.id}")

        logger.debug(f"Creating JWT token for agent_id={agent.id}, agentname={agent.agentname}, persona={agent.persona}")
        token = create_jwt_token(agent.id, agent.agentname, agent.persona)
        logger.info(f"JWT token created successfully for agent_id={agent.id}")

        response = {
            "token": token,
            "agent": {"id": agent.id, "agentname": agent.agentname, "persona": agent.persona}
        }
        logger.debug(f"Login response prepared: {json.dumps(response, default=str)}")
        return response
    except HTTPException as e:
        logger.error(f"HTTP error during login for agentname={login.agentname}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login for agentname={login.agentname}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_local_db)):
    correlation_id = str(uuid.uuid4())
    logger.info(f"WebSocket connection initiated | correlation_id={correlation_id}")
    
    token = websocket.query_params.get("token")
    if not token:
        logger.warning(f"No token provided for WebSocket connection | correlation_id={correlation_id}")
        await websocket.close(code=1008)
        return

    logger.debug(f"Verifying JWT token | correlation_id={correlation_id}")
    payload = verify_jwt_token(token)
    if not payload:
        logger.warning(f"Invalid token provided for WebSocket connection | correlation_id={correlation_id}")
        await websocket.close(code=1008)
        return

    agent_id = payload["agent_id"]
    agentname = payload["agentname"]
    role = payload["role"]
    logger.info(f"Token verified successfully: agent_id={agent_id}, agentname={agentname}, role={role} | correlation_id={correlation_id}")

    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            logger.warning(f"Agent not found: agent_id={agent_id} | correlation_id={correlation_id}")
            await websocket.close(code=1008)
            return

        logger.debug(f"Agent found: agent_id={agent.id}, agentname={agent.agentname} | correlation_id={correlation_id}")
        agent.online_status = True
        db.commit()
        logger.info(f"Agent online_status set to True for agent_id={agent_id} | correlation_id={correlation_id}")

        await websocket.accept()
        websocket.state.agent_id = agent_id
        websocket.state.agentname = agentname
        websocket.state.agent_role = role
        logger.info(f"WebSocket connection accepted for agent_id={agent_id} | correlation_id={correlation_id}")

        try:
            while True:
                data = await websocket.receive_text()
                logger.debug(f"Received message from agent_id={agent_id}: {data} | correlation_id={correlation_id}")
                response = f"Role: {role} | Message: {data}"
                await websocket.send_text(response)
                logger.debug(f"Sent response to agent_id={agent_id}: {response} | correlation_id={correlation_id}")
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for agent_id={agent_id} | correlation_id={correlation_id}")
            handle_logout(agent_id, db)
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket for agent_id={agent_id}: {str(e)} | correlation_id={correlation_id}", exc_info=True)
            await websocket.close(code=1011)
    except Exception as e:
        logger.error(f"Error during WebSocket setup for agent_id={agent_id}: {str(e)} | correlation_id={correlation_id}", exc_info=True)
        db.rollback()
        await websocket.close(code=1011)

@app.post("/logout")
def logout(logout: LogoutRequest, db: Session = Depends(get_local_db)):
    logger.info(f"Logout request received for agent_id={logout.agent_id}")
    try:
        handle_logout(logout.agent_id, db)
        logger.info(f"Logout completed successfully for agent_id={logout.agent_id}")
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Error during logout for agent_id={logout.agent_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/messages/get/{user_id}", response_model=List[MessageResponse])
def get_messages(user_id: str, limit: int = 20, db: Session = Depends(get_local_db)):
    logger.info(f"Fetching messages for user_id={user_id} with limit={limit}")
    try:
        messages = (
            db.query(MessageORM)
            .filter_by(user_id=user_id)
            .order_by(MessageORM.timestamp.desc())
            .limit(limit)
            .all()
        )
        logger.debug(f"Retrieved {len(messages)} messages for user_id={user_id}")
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages for user_id={user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/messages/", response_model=MessageResponse)
def post_message(message: Message, db: Session = Depends(get_local_db)):
    logger.info(f"Posting message for user_id={message.user_id}, sender={message.sender}")
    try:
        if message.sender not in ["user", "ai"]:
            logger.warning(f"Invalid sender value: {message.sender}")
            raise HTTPException(status_code=400, detail="Sender must be 'user' or 'ai'")
        
        db_message = MessageORM(**message.dict())
        if db_message.timestamp is None:
            db_message.timestamp = datetime.utcnow()
            logger.debug(f"Setting timestamp to {db_message.timestamp} for new message")
        
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        logger.info(f"Message posted successfully: message_id={db_message.id}, user_id={message.user_id}")
        return db_message
    except HTTPException as e:
        logger.error(f"HTTP error during message posting for user_id={message.user_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during message posting for user_id={message.user_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/messages/{user_id}/{message_id}", response_model=dict)
def delete_message(user_id: str, message_id: int, db: Session = Depends(get_local_db)):
    logger.info(f"Deleting message: message_id={message_id}, user_id={user_id}")
    try:
        message = (
            db.query(MessageORM)
            .filter_by(id=message_id, user_id=user_id)
            .first()
        )
        if not message:
            logger.warning(f"Message not found: message_id={message_id}, user_id={user_id}")
            raise HTTPException(status_code=404, detail=f"No message #{message_id} found for user {user_id}")
        
        db.delete(message)
        db.commit()
        logger.info(f"Message deleted successfully: message_id={message_id}, user_id={user_id}")
        return {"deleted": True}
    except HTTPException as e:
        logger.error(f"HTTP error during message deletion: message_id={message_id}, user_id={user_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during message deletion: message_id={message_id}, user_id={user_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/messages/delete/last-ai/{user_id}", response_model=dict)
def delete_latest_ai_message(user_id: str, db: Session = Depends(get_local_db)):
    logger.info(f"Deleting latest AI message for user_id={user_id}")
    try:
        message = (
            db.query(MessageORM)
            .filter_by(user_id=user_id, sender="ai")
            .order_by(MessageORM.timestamp.desc())
            .first()
        )
        if not message:
            logger.warning(f"No AI messages found for user_id={user_id}")
            raise HTTPException(status_code=404, detail="No AI messages found for this user")
        
        db.delete(message)
        db.commit()
        logger.info(f"Latest AI message deleted: message_id={message.id}, user_id={user_id}")
        return {"deleted": True, "deleted_message_id": message.id}
    except HTTPException as e:
        logger.error(f"HTTP error during latest AI message deletion for user_id={user_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during latest AI message deletion for user_id={user_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/users")
def upsert_user(user: User, db: Session = Depends(get_local_db)):
    logger.info(f"Upserting user: user_id={user.user_id}")
    try:
        db_user = db.query(UserORM).filter_by(user_id=user.user_id).first()
        if db_user:
            logger.debug(f"Existing user found: user_id={user.user_id}. Updating fields")
            for field, value in user.dict(exclude_unset=True).items():
                setattr(db_user, field, value)
                logger.debug(f"Updated field {field} to {value} for user_id={user.user_id}")
        else:
            logger.debug(f"No existing user found. Creating new user: user_id={user.user_id}")
            db_user = UserORM(**user.dict())
            db.add(db_user)
        
        db.commit()
        db.refresh(db_user)
        logger.info(f"User upserted successfully: user_id={user.user_id}")
        return db_user
    except Exception as e:
        logger.error(f"Error during user upsert for user_id={user.user_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/users/{user_id}/exists", response_model=dict)
def user_exists(user_id: str, db: Session = Depends(get_local_db)):
    logger.info(f"Checking if user exists: user_id={user_id}")
    try:
        exists = db.query(UserORM).filter_by(user_id=user_id).first() is not None
        logger.debug(f"User existence check result: user_id={user_id}, exists={exists}")
        return {"exists": exists}
    except Exception as e:
        logger.error(f"Error checking user existence for user_id={user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/users/{user_id}/language", response_model=dict)
def get_user_language(user_id: str, db: Session = Depends(get_local_db)):
    logger.info(f"Fetching language for user_id={user_id}")
    try:
        user = db.query(UserORM).filter_by(user_id=user_id).first()
        if not user:
            logger.debug(f"No user found for user_id={user_id}. Returning None language")
            return {"language": None}
        logger.debug(f"User found: user_id={user_id}, language={user.language}")
        return {"language": user.language}
    except Exception as e:
        logger.error(f"Error fetching language for user_id={user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/translate")
async def translate(req: TranslationRequest):
    logger.info(f"Translation request: content={req.content[:50]}..., source_lang={req.source_lang}, target_lang={req.target_lang}")
    try:
        logger.debug("Calling translate_text function")
        translated = await translate_text(
            content=req.content,
            source_lang=req.source_lang,
            target_lang=req.target_lang
        )
        logger.info(f"Translation successful: translated_content={translated[:50]}...")
        return {"translated_content": translated}
    except Exception as e:
        logger.error(f"Error during translation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/friendship-statistical-score/{user_id}")
def get_friendship_statistical_score(user_id: int, db: Session = Depends(get_local_db)):
    logger.info(f"Calculating statistical friendship score for user_id={user_id}")
    try:
        score = calculate_friendship_score(db, user_id, datetime.now().astimezone())
        logger.debug(f"Statistical friendship score calculated: user_id={user_id}, score={score}")
        return {"user_id": user_id, "statistical_friendship_score": score}
    except Exception as e:
        logger.error(f"Error calculating statistical friendship score for user_id={user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/friendship-score-zep/{user_id}")
def get_friendship_score(user_id: int):
    logger.info(f"Calculating Zep friendship score for user_id={user_id}")
    try:
        score = calculate_friendship_score_zep(user_id=user_id)
        logger.debug(f"Zep friendship score calculated: user_id={user_id}, score={score}")
        return {"user_id": user_id, "zep_friendship_score": score}
    except Exception as e:
        logger.error(f"Error calculating Zep friendship score for user_id={user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/extract_chat_details")
async def extract_chat_details(request: ChatDetailsRequest, authorization: str = Header(...)):
    logger.info(f"Extracting chat details from input_html (first 50 chars): {request.request[:50]}...")
   
    if not authorization.startswith("Bearer "):
        logger.error("Invalid Authorization header: Must start with 'Bearer '")
        raise HTTPException(status_code=401, detail="Invalid Authorization header: Must start with 'Bearer '")
    
    api_key = authorization.replace("Bearer ", "").strip()
   
    model = "openai/gpt-4o-mini"
    logger.info(f"Using model: {model}")

    try:
        logger.debug("Calling extract_unread function")
        json_string = await extract_unread(input_html=request.request, token=api_key, model=model)
        # Parse JSON string to return a Python dictionary
        result = json.loads(json_string)
        logger.info(f"Chat details extracted successfully: result={json.dumps(result, default=str)[:100]}...")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error during chat details extraction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Invalid JSON response from OpenRouter API: {str(e)}")
    except ValueError as e:
        logger.error(f"Validation error during chat details extraction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Response validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during chat details extraction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")