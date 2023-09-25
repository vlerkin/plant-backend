FROM python:3.11.4-slim

ENV TZ=UTC

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY ./*.py     /app/
COPY ./api      /app/api/
COPY ./services /app/services/

RUN pip install gunicorn
CMD ["gunicorn", "server:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]