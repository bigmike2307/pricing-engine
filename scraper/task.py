from celery import shared_task
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json
from scraper.models import ScrapedData
from scrapy_scraper.spiders.price_checker import setup_driver, extract_product_data


# Import your actual scraping function


@shared_task
def update_scraped_data(product_id):
    """ Task to scrape and update product price at set intervals """
    try:
        driver = setup_driver()
        product = ScrapedData.objects.get(id=product_id)
        new_data = extract_product_data(product.url, driver)

        if new_data:
            product.previous_price = product.current_price
            product.current_price = new_data["current_price"]
            product.save()

    except ScrapedData.DoesNotExist:
        # If product is deleted, remove scheduled task
        PeriodicTask.objects.filter(name=f"update_product_{product_id}").delete()


def schedule_product_update(product_id, frequency_hours):
    """ Schedules or updates a periodic Celery Beat task for a specific product """
    schedule, _ = IntervalSchedule.objects.get_or_create(every=frequency_hours, period=IntervalSchedule.HOURS)

    task_name = f"update_product_{product_id}"

    # Check if task already exists, update frequency if needed
    existing_task = PeriodicTask.objects.filter(name=task_name).first()
    if existing_task:
        existing_task.interval = schedule
        existing_task.save()
    else:
        PeriodicTask.objects.create(
            interval=schedule,
            name=task_name,
            task='scraper.tasks.update_scraped_data',
            args=json.dumps([product_id])
        )
