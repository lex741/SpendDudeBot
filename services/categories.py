from db.database import SessionLocal
from db.models import Category
from db.models import Expense

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


def get_category_by_id(category_id: int) -> Category | None:
    db = SessionLocal()
    cat = db.query(Category).get(category_id)
    db.close()
    return cat

def has_expenses(user_id: int, category_id: int) -> bool:
    db = SessionLocal()
    cnt = db.query(Expense).filter_by(
        user_id=user_id, category_id=category_id
    ).count()
    db.close()
    return cnt > 0

def delete_category_and_expenses(user_id: int, category_id: int):
    db = SessionLocal()
    # Удаляем траты
    db.query(Expense).filter_by(
        user_id=user_id, category_id=category_id
    ).delete()
    # Удаляем саму категорию
    cat = db.query(Category).get(category_id)
    if cat and cat.user_id == user_id:
        db.delete(cat)
    db.commit()
    db.close()