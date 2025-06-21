# services/expenses.py

from db.database import SessionLocal
from db.models import Expense, User
import datetime

def add_expense(user_id: int, amount: float, comment: str, category_id: int, date: datetime.datetime):
    db = SessionLocal()
    exp = Expense(
        user_id=user_id,
        account_id=user_id,
        amount=amount,
        comment=comment,
        category_id=category_id,
        date=date  # передаём уже локальное время
    )
    db.add(exp)
    # уменьшаем баланс
    user = db.get(User, user_id)
    if not user:
        user = User(user_id=user_id, balance=0.0)
        db.add(user)
        db.commit()
        db.refresh(user)
    user.balance -= amount
    db.commit()
    db.refresh(exp)
    db.close()
    return exp

def get_recent_expenses(user_id: int, limit: int = 5):
    db = SessionLocal()
    lst = (db.query(Expense)
             .filter_by(user_id=user_id)
             .order_by(Expense.date.desc())
             .limit(limit)
             .all())
    db.close()
    return lst

def get_user_balance(user_id: int) -> float:
    db = SessionLocal()
    user = db.get(User, user_id)
    if not user:
        user = User(user_id=user_id, balance=0.0)
        db.add(user)
        db.commit()
        db.refresh(user)
    bal = user.balance
    db.close()
    return bal

def set_user_balance(user_id: int, amount: float):
    db = SessionLocal()
    user = db.get(User, user_id)
    if not user:
        user = User(user_id=user_id, balance=amount)
        db.add(user)
    else:
        user.balance = amount
    db.commit()
    db.close()

def get_expenses_filtered(user_id: int, category_id: int = None,
                          start: datetime.datetime = None,
                          end: datetime.datetime = None) -> list[Expense]:
    db = SessionLocal()
    q = db.query(Expense).filter(Expense.user_id == user_id)
    if category_id is not None:
        q = q.filter(Expense.category_id == category_id)
    if start:
        q = q.filter(Expense.date >= start)
    if end:
        q = q.filter(Expense.date <= end)
    rows = q.order_by(Expense.date.desc()).all()
    db.close()
    return rows

def delete_expense(user_id: int, expense_id: int) -> bool:
    db = SessionLocal()
    exp = db.get(Expense, expense_id)
    if not exp or exp.user_id != user_id:
        db.close()
        return False
    # Возвращаем сумму
    user = db.get(User, user_id)
    user.balance += exp.amount
    db.delete(exp)
    db.commit()
    db.close()
    return True