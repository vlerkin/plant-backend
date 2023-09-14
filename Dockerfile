FROM python:3.11.4-slim

ENV TZ=UTC

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY ./*.py     /app/
COPY ./api      /app/api/
COPY ./services /app/services/

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]