from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.models.chat_model import ChatRequest, APIResponse
from src.utils.custom_app_exception import CustomAppException
from src.services.chat_service import ChatService

router = APIRouter(prefix = "/api",tags=["Chat"])


@router.post("/chat", response_model=APIResponse)
async def process_chat(request: ChatRequest) -> JSONResponse:
    """Process a chat message and return the AI agent's response.

    Args:
        request: ChatRequest containing the user_query field.

    Returns:
        JSONResponse with the agent's message.
    """
    try:
        service = ChatService()
        print('came 1 ')
        response = await service.process_chat_service(chat = request.user_query,session_id = request.session_id,customer_id = request.customer_id,interrupt = request.interrupt)
        return JSONResponse(
            status_code=200,
            content= response.model_dump(),
        )
    except CustomAppException:
        raise
    except Exception as e:


        raise CustomAppException(
            message=f"Router err at process_chat: ${str(e)}",
            err_code = "INTERNAL SERVER ERROR",
            status_code = 500)

    
        
