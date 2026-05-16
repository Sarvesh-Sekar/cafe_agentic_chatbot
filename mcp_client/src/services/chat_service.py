from src.models.chat_model import APIResponse
from src.agents.agent import Agent
from src.utils.custom_app_exception import CustomAppException
from src.models.chat_model import OrderDetails,InterruptModel
from typing import Optional
from langchain.agents.middleware._redaction import (apply_strategy,PIIDetectionError,detect_email,detect_credit_card,detect_ip,detect_mac_address,detect_url)
from typing import List

class ChatService:

    async def  process_chat_service(self, chat: str,session_id:str,customer_id:str,interrupt:List[InterruptModel]) -> APIResponse:
        """Process the user's chat message through the AI agent.

        Args:
            chat: The raw user query string.

        Returns:
            ChatResponse containing the agent's reply.
        """
        try:

            if chat == "" :
                raise CustomAppException(
                message=f"Chat service processing failed: User Query is not found",
                status_code=404,
                err_code="QUERY_NOT_FOUND_ERROR",
                )
            agent = Agent()
            await agent.get_llm()
            await agent.create_client()
            filtered_message = await input_filter(message=chat)
            await agent.load_prompts(message=filtered_message)
            await agent.load_resources()
            
            print(filtered_message,'filter')
            await agent.load_context(message=filtered_message)
            await agent.load_tools()

            agent_response = await agent.load_memory(message=chat,session_id = session_id,customer_id = customer_id,decisions=interrupt)

            structured = agent_response.get("structured_response")
            print(structured)



            
            
            
            return APIResponse(structured_content=structured,status_code=200,message="Response generated Successfully" )

        except CustomAppException:
            raise
        except Exception as e:

            raise CustomAppException(
                message=f"Chat service processing failed: {str(e)}",
                status_code=500,
                err_code="SERVICE_ERROR",
            )

async def input_filter(message:str):
        try:
            all_matches=(detect_email(message)
                            + detect_credit_card(message)
                            + detect_ip(message)
                            + detect_mac_address(message)
                            +detect_url(message))

            for m in all_matches:
                print(f"  detected  [{m['type']:15}]  {m['value']!r}")

            print("redact :", apply_strategy(message, all_matches, "redact"))
            print("mask   :", apply_strategy(message, all_matches, "mask"))
            print("hash   :", apply_strategy(message, all_matches, "hash"))
            return apply_strategy(message,all_matches,"mask")
        except CustomAppException:
            raise
        except Exception as e:

            raise CustomAppException(
                err_code= "INPUT_FILTER_FAILED",
                message=f"Input Filtering Failed : {str(e)}",
                status_code=500,
            )
        





