from typing import List, Optional

from src.repositories.database import get_database,Database
from src.repositories.schemas.mcp_schema import MenuItem, Order, OrderItem,ErrLog,Customer
from src.utils.custom_app_exception import CustomAppException
from sqlalchemy import select,join
import secrets
import string
from fastmcp.dependencies import Depends

class ErrorRepository:
    
    def __init__(self):
        self.db = get_database()

    def add_error(self,file_name:str,function_name:str,message:str):

        try:
            
            db_session = self.db.get_db()
            new_err = ErrLog(
                filename = file_name,
                function_name = function_name,
                message = message
            )

            db_session.add(new_err)
            db_session.commit()

            print(f'Err log added successfully: {new_err.id}')

        except CustomAppException:
            raise
        except Exception as e:
            raise CustomAppException(
                message=f"Failed to add error log: {str(e)}",
                status_code=500,
                err_code="INTERNAL SERVER ERROR",
            )


class MCPRepository:

    def __init__(self,db):
        self.db = db
        self.err_repo = get_err_repo()
    
    async def get_menu_items(self, active_only: bool = True) -> List[MenuItem]:
        try:
                db_session = self.db.get_db()
                query = db_session.query(MenuItem)
                if active_only:
                    query = query.filter(MenuItem.is_active == True)
                return query.all()
        except CustomAppException:
            raise
        except Exception as e:
            self.err_repo.add_error(
                file_name='mcp_repository',
                function_name='get_menu_items',
                message=f"Failed to fetch menu items: {str(e)}"
            )
            raise CustomAppException(
                message=f"Failed to fetch menu items: {str(e)}",
                status_code=500,
                err_code="DB_QUERY_ERROR",
            )


    async def check_customer_exists(self,phone_no:str,customer_name:str = None, customer_id:str = None) -> Optional[Customer]:
        try:
                db_session = self.db.get_db()
                if customer_name:
                    customer = db_session.query(Customer).filter(Customer.customer_name == customer_name,Customer.phone_no == phone_no,Customer.is_active == True).first()
                if customer_id:
                    customer = db_session.query(Customer).filter(Customer.customer_id == customer_id,Customer.phone_no == phone_no,Customer.is_active == True).first()

                if not customer:
                    return None
                return customer
        except CustomAppException:
            raise
        except Exception as e:
            self.err_repo.add_error(
                file_name='mcp_repository',
                function_name='check_customer_exists',
                message=f"Failed to perform check_customer_exists: {str(e)}"
            )
            raise CustomAppException(
                message=f"Failed to perform check_customer_exists: {str(e)}",
                status_code=500,
                err_code="DB_QUERY_ERROR",
            )
            
    async def create_customer(self,customer_name,phone_no) -> Optional[Customer]:
        try:
             db_session = self.db.get_db()
             new_customer = Customer(
                  customer_name = customer_name,
                  phone_no = phone_no
             )

             db_session.add(new_customer)
             db_session.commit()
             db_session.refresh(new_customer)
             return new_customer
                

        except CustomAppException:
            raise
        except Exception as e:
            self.err_repo.add_error(
                file_name='mcp_repository',
                function_name='check_customer_exists',
                message=f"Failed to perform check_customer_exists: {str(e)}"
            )
            raise CustomAppException(
                message=f"Failed to perform check_customer_exists: {str(e)}",
                status_code=500,
                err_code="DB_QUERY_ERROR",
            )


    async def get_menu_item_by_name(self, name: str) -> Optional[MenuItem]:
        try:
            db_session = self.db.get_db()
            return (
                    db_session.query(MenuItem)
                    .filter(MenuItem.name.ilike(name), MenuItem.is_active == True)
                    .first()
                )
        except CustomAppException:
            raise
        except Exception as e:
            self.err_repo.add_error(
                file_name='mcp_repository',
                function_name='get_menu_item_by_name',
                message=f"Failed to fetch item by name: {str(e)}"
            )
            raise CustomAppException(
                message=f"Failed to fetch item by name: {str(e)}",
                status_code=500,
                err_code="DB_QUERY_ERROR",
            )

    async def get_order_by_id(self,ord_code: str = None) -> Optional[Order]:
        try:
                db_session = self.db.get_db()
                stmt = (select(Order.ord_code,Order.status,Order.created_at,Customer.customer_name,Order.customer_id).join(Customer,Customer.customer_id == Order.customer_id).filter(Order.ord_code == ord_code).filter(Order.is_active == True))

                orders = db_session.execute(stmt).first()
                print(dir(orders),orders,'orders')
                return orders

        except CustomAppException:
            raise
        except Exception as e:
            self.err_repo.add_error(
                file_name='mcp_repository',
                function_name='get_order_by_id',
                message=f"Failed to fetch order: {str(e)}"
            )

            raise CustomAppException(
                message=f"Failed to fetch order: {str(e)}",
                status_code=500,
                err_code="DB_QUERY_ERROR",
            )

    async def create_order(self, customer_id: str, items: List[dict], status: str = "PENDING") -> Order:
        try:
                # Create the Order record
                db_session = self.db.get_db()
                alphabet = string.ascii_uppercase + string.digits
                order_suffix = ''.join(secrets.choice(alphabet) for _ in range(6))
                

                order_id = f"ORD-{order_suffix}"
                new_order = Order(
                    customer_id=customer_id,
                    ord_code = order_id,
                    status=status,
                    created_by="chatbot",
                    updated_by="chatbot",
                )
                db_session.add(new_order)
                db_session.flush()  # flush to get order_id before inserting items

                # Insert each OrderItem
                for item_data in items:
                    item_name = item_data.get("item")
                    quantity = item_data.get("quantity", 1)

                    menu_item = (
                        db_session.query(MenuItem)
                        .filter(MenuItem.name.ilike(item_name), MenuItem.is_active == True)
                        .first()
                    )
                    if not menu_item:
                        raise CustomAppException(
                            message=f"Menu item '{item_name}' not found",
                            status_code=404,
                            err_code="ITEM_NOT_FOUND",
                        )

                    order_item = OrderItem(
                        order_id=new_order.order_id,
                        menu_item_id=menu_item.menu_item_uuid,
                        quantity=quantity,
                        created_by="chatbot",
                        updated_by="chatbot",
                    )
                    menu_item.stock_quantity = menu_item.stock_quantity - quantity
                    db_session.add(menu_item)
                    db_session.commit()

                     
                    db_session.add(order_item)

                db_session.commit()

                
                db_session.refresh(new_order)
               

                return new_order
        except CustomAppException:
            raise
        except Exception as e:

            self.err_repo.add_error(
                file_name='mcp_repository',
                function_name='create_order',
                message=f"Failed to create order:: {str(e)}"
            )

            raise CustomAppException(
                message=f"Failed to create order: {str(e)}",
                status_code=500,
                err_code="DB_INSERT_ERROR",
            )
        


def get_mcp_repo(db:Database = Depends(get_database)):
    return MCPRepository(db)
def get_err_repo():
    return ErrorRepository()

