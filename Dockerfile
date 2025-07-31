FROM python:3.9
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/producer/producer.py .
COPY setup/topics.py setup/topics.py

CMD ["python", "producer.py"]