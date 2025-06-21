from db.database import SessionLocal
from db.models import Category, Expense


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


def has_expenses(user_id: int, category_id: int) -> bool:
    db = SessionLocal()
    cnt = db.query(Expense).filter_by(user_id=user_id, category_id=category_id).count()
    db.close()
    return cnt > 0


def delete_category_and_expenses(user_id: int, category_id: int):
    db = SessionLocal()
    # удаляем траты
    db.query(Expense).filter_by(user_id=user_id, category_id=category_id).delete()
    # удаляем категорию
    cat = db.query(Category).filter_by(user_id=user_id, id=category_id).first()
    if cat:
        db.delete(cat)
    db.commit()
    db.close()


def get_category_by_name(user_id: int, name: str) -> Category | None:
    """
    Возвращает категорию по имени для пользователя или None
    """
    db = SessionLocal()
    cat = db.query(Category).filter_by(user_id=user_id, name=name).first()
    db.close()
    return cat


def get_category_by_id(category_id: int) -> Category | None:
    """
    Возвращает категорию по её ID или None
    """
    db = SessionLocal()
    cat = db.query(Category).filter_by(id=category_id).first()
    db.close()
    return cat
