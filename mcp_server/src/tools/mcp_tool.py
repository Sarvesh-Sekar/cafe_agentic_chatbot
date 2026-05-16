from typing import Dict, List
from src.repositories.mcp_repository import MCPRepository,get_err_repo,get_mcp_repo
from src.utils.custom_app_exception import CustomAppException
from src.repositories.mcp_repository import ErrorRepository
from src.routers.mcp_router import router
from fastmcp.dependencies import Depends



@router.tool()
async def check_menu(repo: MCPRepository = Depends(get_mcp_repo), err_repo:ErrorRepository = Depends(get_err_repo)) -> Dict:
    """Get the full Bean & Brew menu. Returns a list of items under the key 
    'items', each with 'name' (str), 'description' (str), and 'price' (float).
    Map each entry to a MenuItem schema."""
    try:
        print('tool check_menu')
        items = await repo.get_menu_items(active_only=True)
        menu = [
            {
                "name": item.name,
                "description": item.description,
                "price": float(item.price),
                # ✅ removed in_stock — not in MenuItem schema
            }
            for item in items
        ]
        result = {"menu": menu}  # ✅ flat, named key the agent can unpack
        print(result)
        return result
    
    except CustomAppException:
        raise
    except Exception as e:
        err_repo.add_error(
            file_name="tools.py",
            function_name="check_menu",
            message=f"Failed to retrieve menu: {str(e)}"
        )
        raise CustomAppException(
            message=f"Failed to retrieve menu: {str(e)}",
            status_code=500,
            err_code="TOOL_MENU_ERROR",
        )


@router.tool()
async def check_inventory(item_name: str,repo:MCPRepository = Depends(get_mcp_repo),err_repo:ErrorRepository = Depends(get_err_repo)) -> Dict:
    """Check whether a specific menu item is available and how many are in stock.

    Args:
        item_name: The name of the menu item to check.
    """

    try:
        
        item = await repo.get_menu_item_by_name(item_name)
        if not item:
            return {"found": False, "message": f"'{item_name}' is not on our menu."}
        return {
            "found": True,
            "name": item.name,
            "price": float(item.price),
            "stock_quantity": item.stock_quantity,
            "in_stock": item.stock_quantity > 0,
        }
    except CustomAppException:
        raise
    except Exception as e:
        err_repo.add_error(
            file_name="tools.py",
            function_name="check_inventory",
            message=f"Failed to check inventory: {str(e)}"
        )
        raise CustomAppException(
            message=f"Failed to check inventory: {str(e)}",
            status_code=500,
            err_code="TOOL_INVENTORY_ERROR",
        )


@router.tool()
async def check_order_status(ord_code: str=None,repo:MCPRepository = Depends(get_mcp_repo),err_repo:ErrorRepository = Depends(get_err_repo)) -> Dict:
    """Check the status of an existing order using its order code.

    Args:
        ord_code: The order code of the order to look up.
    """
    try:
        


        if ord_code is None:
            return "Please send an ord_code to get your order details"
        
        order = await repo.get_order_by_id(ord_code=ord_code)
        if not order:
            return {"found": False, "message": f"No order found with ID '{ord_code}'."}
        result = {
            "ord_code": str(order.ord_code),
            "customer_id":order.customer_id,
            "customer_name": order.customer_name,
            "status": order.status,
            "created_at": str(order.created_at),
        }
        print(result,'resul')
        return result
    except CustomAppException:
        raise
    except Exception as e:
        err_repo.add_error(
            file_name="tools.py",
            function_name="check_order_status",
            message=f"Failed to  retrieve order status : {str(e)}"
        )
        raise CustomAppException(
            message=f"Failed to retrieve order status: {str(e)}",
            status_code=500,
            err_code="TOOL_ORDER_STATUS_ERROR",
        )


@router.tool()
async def add_order(customer_name: str, phone_no:str,items: List[Dict],repo:MCPRepository = Depends(get_mcp_repo),err_repo:ErrorRepository = Depends(get_err_repo)) -> Dict:
    """Place a new order for a customer.

    Args:
        customer_name: The name of the customer placing the order.
        phone_no : The phone number of the customer with minimum of 10 digits
        items: A list of dicts with 'item' (str) and 'quantity' (int) keys.
               Example: [{"item": "Latte", "quantity": 2}, {"item": "Espresso", "quantity": 1}]
    """
    try:
        
        customer = await repo.check_customer_exists(customer_name=customer_name,phone_no=phone_no)
        if not customer:
            customer = await repo.create_customer(customer_name=customer_name,phone_no=phone_no)
        order = await repo.create_order(customer_id=customer.customer_id, items=items, status="PENDING")

        # Calculate total from items
        total_price = 0.0
        order_summary = []
        for item_data in items:
            menu_item = await repo.get_menu_item_by_name(item_data["item"])
            if menu_item:
                line_total = float(menu_item.price) * item_data["quantity"]
                total_price += line_total
                order_summary.append({
                    "item": menu_item.name,
                    "quantity": item_data["quantity"],
                    "unit_price": float(menu_item.price),
                    "line_total": line_total,
                })

        return {
            "ord_code": str(order.ord_code),
            "customer_name": customer.customer_name,
            "customer_id":customer.customer_id,
            "status": order.status,
            "order_summary":order_summary
        }
    except CustomAppException:
        raise
    except Exception as e:
        err_repo.add_error(
            file_name="tools.py",
            function_name="check_order_status",
            message=f"Failed to place order: {str(e)}"
        )
                
        raise CustomAppException(
            message=f"Failed to place order: {str(e)}",
            status_code=500,
            err_code="TOOL_ADD_ORDER_ERROR",
        )
