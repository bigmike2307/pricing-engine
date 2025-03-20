import json
import logging
from celery import shared_task
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from scraper.models import ScrapedData
from scrapy_scraper.spiders.price_checker import setup_driver, extract_product_data

logger = logging.getLogger(__name__)

@shared_task
def update_scraped_data(product_id):
    """ Task to scrape and update product price at set intervals """
    driver = setup_driver()
    try:

        product = ScrapedData.objects.get(id=product_id)

        new_data = extract_product_data(product.url, driver)
        if new_data:
            product.previous_price = product.current_price
            product.current_price = new_data.get("current_price", product.current_price)
            product.save()
            logger.info(f"Updated product {product.id} price to {product.current_price}")

    except ScrapedData.DoesNotExist:
        logger.warning(f"Product {product_id} not found. Removing scheduled task.")
        PeriodicTask.objects.filter(name=f"update_product_{product_id}").delete()

    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")

    finally:
        driver.quit()

def schedule_product_update(product_id, frequency_hours):
    """ Schedules or updates a periodic Celery Beat task for a specific product """
    schedule, _ = IntervalSchedule.objects.get_or_create(every=frequency_hours, period=IntervalSchedule.HOURS)
    task_name = f"update_product_{product_id}"

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
            args=json.dumps([product_id])
        )
        logger.info(f"Scheduled new periodic task: {task_name}")
