# Use Python 3.12 as base image
FROM python:3.12

# Set working directory inside the container
WORKDIR /app

# Copy dependencies file
COPY requirements.txt ./

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire project
COPY . .

# Expose port for Django
EXPOSE 8000

# Run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
