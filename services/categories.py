from db.database import SessionLocal
from db.models import Category

def get_categories(user_id: int) -> list[Category]:
    db = SessionLocal()
    lst = db.query(Category).filter_by(user_id=user_id).all()
    db.close()
    return lst

def add_category(user_id: int, name: str) -> Category:
    db = SessionLocal()
    cat = Category(user_id=user_id, name=name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    db.close()
    return cat

def delete_category(user_id: int, category_id: int) -> bool:
    db = SessionLocal()
    cat = db.query(Category).filter_by(user_id=user_id, id=category_id).first()
    if not cat:
        db.close()
        return False
    db.delete(cat)
    db.commit()
    db.close()
    return True
