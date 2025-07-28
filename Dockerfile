FROM python:3.9
WORKDIR /app
COPY src/producer.py .
RUN pip install requirements.txt .

