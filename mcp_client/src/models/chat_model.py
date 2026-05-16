from pydantic import BaseModel,Field
from typing import List, Optional,Literal,Text
from enum import Enum 
from pydantic.config import ConfigDict

class OrderStatusEnum(str, Enum):
    ORDERED = "ORDERED"
    FULFILLED = "FULFILLED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"





# class OrderItem(BaseModel):
#     item: str
#     quantity: int
#     price: float


# class OrderDetails(BaseModel):
#     user_query: str = Field(description="The CURRENT specific question the user just asked.")
#     response_text: str = Field(description="The actual answer to the current question. If asking for status, provide the status.")
    

class OrderDetails(BaseModel):
    """
    Structured response schema for a confirmed or existing order.

    Returned exclusively when the agent resolves a STATUS intent via the
    `check_order_status` tool. Every field maps 1-to-1 to a database column
    on the Orders table. Do NOT use this schema for menu lookups or inventory
    checks.
    """

    ord_code: str = Field(
        description=(
            "Unique order reference code assigned at order creation "
            " Used by the customer to track their order."
        )
    )
    customer_name: str = Field(
        description="Full name of the customer who placed the order, as stored in the database."
    )

    customer_id:str =Field(
        description="ID of the customer"
    )
    status: str = Field(
        description=(
            "Current lifecycle state of the order. "
            "Expected values: PENDING | PREPARING | READY | COMPLETED | CANCELLED."
        )
    )
    created_at: str = Field(
        description="timestamp of when the order was created (e.g. '2026-03-24 19:59:35.839217')."
    )


class ChatResponse(BaseModel):
    """
    Structured response schema for all non-order, non-menu agent replies.

    Used for inventory checks, policy questions, preparation tips, and any
    conversational turn that does not produce an OrderDetails or MenuItem
    payload. Keeps the user-facing reply tightly coupled to the question
    that triggered it, preventing stale context bleed from prior turns.
    """
    model_config = ConfigDict(strict=True)
    response_type:Literal["chat"]
    user_query: str = Field(
        description=(
            "Verbatim restatement of the CURRENT user question. "
            "Must reflect only the latest message, never a prior turn's question."
        )
    )
    response_text: str = Field(
        description=(


            "Direct, complete answer to `user_query`. "
            "For inventory: include availability and quantity. "
            "For policy/tips: answer from [CONTEXT] only. "
            "Never leave this field empty or deferring ('see above', etc.)."
        )
    )

class InterruptModel(BaseModel):
    interrupt_id:str
    interrupt_action:str

class ChatRequest(BaseModel):
    user_query: str
    session_id : Optional[str] =None
    customer_id : Optional[str] =None
    interrupt:Optional[List[InterruptModel]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_query": "What is on the menu?"
            }
        }


class MenuItem(BaseModel):
    """
    Structured response schema for a single menu item.

    """

    name: str = Field(description="Display name of the menu item (e.g. 'Oat Milk Latte').")
    description: str = Field(
        description="Short customer-facing description of the item (ingredients, flavour profile, size)."
    )
    price: float = Field(description="Item price in the shop's base currency, rounded to 2 decimal places.")

class MenuResponse(BaseModel):
    """Structured response for menu listings. 
    Wraps a list of MenuItem objects returned by check_menu tool."""
    model_config = ConfigDict(strict=True)
    items: List[MenuItem] = Field(
        description="List of all available menu items, each with name, description and price."
    )


class NeedContextResponse(BaseModel):
        """Structured response for requesting detailed context from User"""

        response :str = Field(description="Fill the field with explanation requesting relevant details from the user query")





class APIResponse(BaseModel):
    status_code: int
    message: str
    structured_content:Optional[OrderDetails] | Optional[MenuResponse] | Optional[ChatResponse] | Optional[NeedContextResponse] = None
