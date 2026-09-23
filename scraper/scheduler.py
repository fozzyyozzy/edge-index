"""
Scheduled scraper runner
Runs scraper based on game schedule:
- Weekdays (Mon-Wed): 10 AM, 2 PM, 6 PM ET
- TNF (Thursday): Hourly
- SNF (Sunday): Hourly  
- MNF (Monday): Hourly
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz
import logging
from alt_lines_scraper import run_scraper

logger = logging.getLogger(__name__)

def start_scheduler():
    """Start the APScheduler for recurring scraper runs"""
    
    scheduler = BackgroundScheduler(timezone=pytz.timezone('US/Eastern'))
    
    # Weekday schedule (Mon-Wed): 10 AM, 2 PM, 6 PM ET
    scheduler.add_job(
        run_scraper,
        'cron',
        day_of_week='0-2',  # Mon-Wed
        hour='10,14,18',
        minute=0,
        id='weekday_scraper'
    )
    
    # TNF (Thu): Hourly from 6 AM to midnight
    scheduler.add_job(
        run_scraper,
        'cron',
        day_of_week='3',  # Thu
        hour='6-23',
        minute=0,
        id='tnf_scraper'
    )
    
    # SNF (Sun): Hourly from 6 AM to midnight
    scheduler.add_job(
        run_scraper,
        'cron',
        day_of_week='6',  # Sun
        hour='6-23',
        minute=0,
        id='snf_scraper'
    )
    
    # MNF (Mon): Hourly from 6 PM to midnight
    scheduler.add_job(
        run_scraper,
        'cron',
        day_of_week='0',  # Mon
        hour='18-23',
        minute=0,
        id='mnf_scraper'
    )
    
    scheduler.start()
    logger.info("✅ Scheduler started")
    logger.info("Weekday: 10 AM, 2 PM, 6 PM ET")
    logger.info("TNF/SNF: Hourly 6 AM - 11 PM ET")
    logger.info("MNF: Hourly 6 PM - 11 PM ET")
    
    return scheduler

if __name__ == "__main__":
    scheduler = start_scheduler()
    try:
        # Keep scheduler running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
