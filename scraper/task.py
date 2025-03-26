import json
import logging
from celery import shared_task
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from scraper.models import ScrapedData
from scrapy_scraper.spiders.price_checker import setup_driver, extract_product_data

logger = logging.getLogger(__name__)

@shared_task
def update_scraped_data(product_id):
    """Task to scrape and update product price at set intervals"""
    driver = setup_driver()
    try:
        product = ScrapedData.objects.get(id=product_id)
        new_data = extract_product_data(product.url, driver)
        if new_data:
            product.previous_price = product.current_price
            product.current_price = new_data.get("current_price", product.current_price)
            product.save()
            logger.info(f"Updated product {product.id} price to {product.current_price}")
            return product.current_price  # Return the updated price
    except ScrapedData.DoesNotExist:
        logger.warning(f"Product {product_id} not found. Removing scheduled task.")
        PeriodicTask.objects.filter(name=f"update_product_{product_id}").delete()
        return "Product not found"
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        return str(e)
    finally:
        driver.quit()


def schedule_product_update(product_id, frequency):
    """Schedules or updates a periodic Celery Beat task for a specific product with error handling"""
    try:
        PERIODS = {
            "minutes": IntervalSchedule.MINUTES,
            "hourly": IntervalSchedule.HOURS,
            "daily": IntervalSchedule.DAYS,
        }

        task_name = f"update_product_{product_id}"

        if frequency == "monthly":
            # Handle Monthly Schedule using Crontab
            cron_schedule, _ = CrontabSchedule.objects.get_or_create(
                minute="0", hour="0", day_of_month="1", month_of_year="*", day_of_week="*"
            )

            existing_task = PeriodicTask.objects.filter(name=task_name).first()
            if existing_task:
                existing_task.crontab = cron_schedule
                existing_task.save()
                logger.info(f"Updated existing monthly task: {task_name}")
            else:
                PeriodicTask.objects.create(
                    crontab=cron_schedule,
                    name=task_name,
                    task="scraper.tasks.update_scraped_data",
                    args=json.dumps([product_id]),
                )
                logger.info(f"Scheduled new monthly task: {task_name}")

        else:
            # Handle Minutes, Hourly, and Daily Scheduling
            interval_period = PERIODS.get(frequency)
            if not interval_period:
                logger.error(f"Invalid frequency: {frequency}")
                return "Invalid frequency"

            schedule, _ = IntervalSchedule.objects.get_or_create(every=1, period=interval_period)

            existing_task = PeriodicTask.objects.filter(name=task_name).first()
            if existing_task:
                existing_task.interval = schedule
                existing_task.save()
                logger.info(f"Updated existing periodic task: {task_name}")
            else:
                PeriodicTask.objects.create(
                    interval=schedule,
                    name=task_name,
                    task="scraper.tasks.update_scraped_data",
                    args=json.dumps([product_id]),
                )
                logger.info(f"Scheduled new periodic task: {task_name}")

    except Exception as e:
        logger.error(f"Error scheduling product {product_id} update task: {e}")
        return str(e)
