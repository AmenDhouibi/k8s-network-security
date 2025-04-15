FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Create logs dir inside container
RUN mkdir -p logs

EXPOSE 5000

CMD ["python", "app.py"]
