# Pricing Engine

## Overview
Pricing Engine is a Django-based web application designed to scrape and analyze product pricing data. The project is containerized using Docker for easy deployment.

## Features
- Product data scraping
- API endpoints for fetching and updating data
- Swagger and Redoc documentation for API exploration

## Installation
### Prerequisites
- Python 3.12
- Docker & Docker Compose
- Git

### Clone the Repository
```sh
git clone https://github.com/bigmike2307/pricing-engine.git
cd pricing-engine
```

### Set Up Virtual Environment (For Local Development)
```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```



### Run Migrations
```sh
python manage.py migrate
```

### Run Development Server
```sh
python manage.py runserver
```

## Docker Setup
### Build and Run the Containers
```sh
docker-compose up --build
```

## API Endpoints


### Available Endpoints
| Method | Endpoint                              | Description                         |
|--------|--------------------------------------|-------------------------------------|
| POST   | `/scrape-product/`                  | Scrape product data                |
| GET    | `/scraped-data/<user_identifier>/`  | Get scraped data for a user        |
| PUT    | `/scraped-data/<user_identifier>/?id=<product_id>` | Update scraped data (excluding URL & price) |
| GET    | `/swagger/`                         | API documentation (Swagger)        |
| GET    | `/redoc/`                           | API documentation (Redoc)          |

### Using Endpoints
#### Scrape a Product
**Endpoint:**
```
POST /scrape-product/
```
**Request Body (JSON):**
```json
{
    "user_identifier": "string",
    "url": "string",
    "save": true
}
```

**Response:**
```json
[
    {
        "id": 1,
        "product_name": "Sample Product",
        "current_price": "$99.99",
        "previous_price": "$129.99",
        "description": "A high-quality product",
        "timestamp": "2024-03-05 12:00:00"
    }
]
```





## Contributing
1. Fork the repository
2. Create a new branch
3. Make your changes and commit them
4. Push to your fork and submit a pull request


