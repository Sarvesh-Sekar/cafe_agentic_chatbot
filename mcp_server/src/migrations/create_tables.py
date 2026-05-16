from src.repositories.database import Database ,Base,get_database
from src.repositories.schemas.mcp_schema import MenuItem
from fastmcp.dependencies import Depends


db = Database()
def create_tables() -> None:
    """Create all database tables if they don't already exist."""
    
    Base.metadata.create_all(bind=db.engine)
    print("[Migrations] All tables created successfully.")
    seed_data()


def seed_data() -> None:
    """Seed initial menu items into the database if empty."""

    db_session = db.get_db()
    try:
        existing = db_session.query(MenuItem).first()
        if existing:
            print("[Migrations] Seed data already exists, skipping.")
            return

        menu_items = [
            MenuItem(name="Espresso",        description="Rich, bold single shot espresso",          price=3.50,  stock_quantity=100, created_by="system", updated_by="system"),
            MenuItem(name="Americano",        description="Espresso diluted with hot water",           price=4.00,  stock_quantity=100, created_by="system", updated_by="system"),
            MenuItem(name="Latte",            description="Espresso with steamed milk and light foam", price=4.50,  stock_quantity=80,  created_by="system", updated_by="system"),
            MenuItem(name="Cappuccino",       description="Espresso with equal parts milk and foam",   price=4.50,  stock_quantity=80,  created_by="system", updated_by="system"),
            MenuItem(name="Flat White",       description="Smooth espresso with velvety microfoam",    price=4.75,  stock_quantity=70,  created_by="system", updated_by="system"),
            MenuItem(name="Mocha",            description="Espresso with chocolate and steamed milk",  price=5.00,  stock_quantity=60,  created_by="system", updated_by="system"),
            MenuItem(name="Cold Brew",        description="Slow-steeped cold brew coffee",             price=5.00,  stock_quantity=50,  created_by="system", updated_by="system"),
            MenuItem(name="Iced Latte",       description="Espresso with cold milk over ice",          price=5.00,  stock_quantity=70,  created_by="system", updated_by="system"),
            MenuItem(name="Chai Latte",       description="Spiced chai tea with steamed milk",         price=4.50,  stock_quantity=60,  created_by="system", updated_by="system"),
            MenuItem(name="Croissant",        description="Buttery, flaky French-style croissant",     price=3.00,  stock_quantity=30,  created_by="system", updated_by="system"),
            MenuItem(name="Blueberry Muffin", description="Freshly baked muffin with blueberries",    price=2.75,  stock_quantity=25,  created_by="system", updated_by="system"),
            MenuItem(name="Avocado Toast",    description="Sourdough toast with smashed avocado",      price=7.50,  stock_quantity=20,  created_by="system", updated_by="system"),
        ]

        db_session.add_all(menu_items)
        db_session.commit()
        print(f"[Migrations] Seeded {len(menu_items)} menu items successfully.")
    except Exception as e:
        db_session.rollback()
        print(f"[Migrations] Seed failed: {e}")
    finally:
        db_session.close()
