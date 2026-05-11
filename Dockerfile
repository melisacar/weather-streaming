FROM python:3.9
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/producer/producer.py .
COPY src/producer/schema.py .
COPY setup/topics.py setup/topics.py

CMD ["sh", "-c", "python setup/topics.py && python producer.py"]