FROM python:alpine

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN pip install gunicorn
CMD ["gunicorn", "-w1", "-b :8000", "gmail:app"]
