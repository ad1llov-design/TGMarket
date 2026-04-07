FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port (useful for cloud providers that check health)
EXPOSE 8080

# Run the bot
CMD ["python", "main.py"]
