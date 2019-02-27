from apscheduler.schedulers.blocking import BlockingScheduler
from scripts.schedule import tasks_overdue
from app import app

sched = BlockingScheduler()

@sched.scheduled_job('cron', day_of_week='mon-sun', hour=17)
def scheduled_job():
    tasks_overdue(app)
