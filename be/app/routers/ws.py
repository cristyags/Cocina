from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.services import auth_service, notification_service


router = APIRouter(tags=["ws"])


@router.websocket("/ws/notifications")
async def notifications_socket(websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    try:
        token_data = auth_service.decode_token(token)
        if token_data.user_id is None:
            raise JWTError("Missing user id")
    except JWTError:
        await websocket.close(code=1008)
        return

    user_id = token_data.user_id
    await websocket.accept()
    notification_service.register_ws(user_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_service.unregister_ws(user_id)
