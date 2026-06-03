FROM python:3.9
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY setup/topics.py setup/topics.py

ENV PYTHONPATH=/app

CMD ["sh", "-c", "python setup/topics.py && python src/producer/producer.py"]