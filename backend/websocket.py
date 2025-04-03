from fastapi import WebSocket, WebSocketDisconnect # type: ignore
from sqlalchemy.orm import Session
from models import Agent

async def websocket_endpoint(websocket: WebSocket, agent_id: int, db: Session):
    await websocket.accept()
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            await websocket.close(code=1008)
            return
        
        websocket.state.agent_id = agent_id
        websocket.state.agent_persona = agent.persona

        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Hi")

    except WebSocketDisconnect:
        print(f"Agent {agent_id} Not Found")