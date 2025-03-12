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

[//]: # (### Environment Variables)

[//]: # (Create a `.env` file and configure the required environment variables:)

[//]: # (```)

[//]: # (DJANGO_SECRET_KEY=your_secret_key)

[//]: # (DEBUG=True)

[//]: # (DATABASE_URL=sqlite:///db.sqlite3  # Change this for production)

[//]: # (```)

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
### Base URL
```
http://localhost:8000/api/
```

### Available Endpoints
| Method | Endpoint                              | Description                     |
|--------|--------------------------------------|---------------------------------|
| POST   | `/api/scrape-product/`               | Scrape product data            |
| GET    | `/api/scraped-data/<user_identifier>/` | Fetch user's scraped data      |
| GET    | `/swagger/`                          | API documentation (Swagger)    |
| GET    | `/redoc/`                            | API documentation (Redoc)      |



## Contributing
1. Fork the repository
2. Create a new branch
3. Make your changes and commit them
4. Push to your fork and submit a pull request

## License
This project is licensed under the MIT License.

