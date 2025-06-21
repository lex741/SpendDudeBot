import datetime
from db.database import SessionLocal
from db.models import Expense
from sqlalchemy import func

from services.categories import get_category_by_id

def get_sum_by_category(user_id: int, start: datetime.datetime, end: datetime.datetime) -> dict[str, float]:
    """
    Возвращает словарь {название_категории: сумма} за период [start, end].
    """
    db = SessionLocal()
    rows = (
        db.query(Expense.category_id, func.sum(Expense.amount))
          .filter(
              Expense.user_id == user_id,
              Expense.date >= start,
              Expense.date <= end
          )
          .group_by(Expense.category_id)
          .all()
    )
    db.close()
    return {
        get_category_by_id(cat_id).name: total
        for cat_id, total in rows
    }


def get_weekly_expenses(user_id: int, start: datetime.datetime, end: datetime.datetime) -> dict[str, float]:
    """
    Возвращает словарь {"Неделя N": сумма} за период [start, end].
    """
    db = SessionLocal()
    exps = (
        db.query(Expense)
          .filter(
              Expense.user_id == user_id,
              Expense.date >= start,
              Expense.date <= end
          )
          .all()
    )
    db.close()

    weeks: dict[str, float] = {}
    for e in exps:
        week_idx = (e.date.day - 1) // 7 + 1
        key = f"Неделя {week_idx}"
        weeks[key] = weeks.get(key, 0) + e.amount
    return weeks