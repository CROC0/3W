from datetime import datetime, timedelta
from scripts.item import ItemModel
from scripts.login import UserModel
from scripts.mail import overdue_item_email


due_today = "Your item is due today."
due_tomorrow = "Your item is due tomorrow"
due_next_week = "Your item is due in one week"
today = datetime.now().date()
tomorrow = datetime.now().date() + timedelta(days=1)
next_week = datetime.now().date() + timedelta(days=7)

def tasks_overdue(app):
    with app.app_context():
        items = ItemModel.listItems()

        for item in items:
            user = UserModel.find_by_id(item.who_id)
            due_date = datetime.strptime(item.when, '%Y-%m-%d')
            if due_date.date() == today:
                overdue_item_email(user.username, due_today, "today")

            elif due_date.date() == tomorrow:
                overdue_item_email(user.username, due_tomorrow, "tomorrow")

            elif due_date.date() == next_week:
                overdue_item_email(user.username, due_next_week, "in seven days")

