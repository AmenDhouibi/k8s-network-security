FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN mkdir -p logs


RUN cp app_v9.py app.py


RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]
