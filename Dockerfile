FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (e.g., ping for OS command injection)
RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Initialize the database
RUN python init_db.py

EXPOSE 5000

CMD ["python", "app.py"]
