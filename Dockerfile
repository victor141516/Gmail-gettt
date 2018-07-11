FROM python:alpine

COPY . /app
WORKDIR /app
RUN apk add --no-cache git
RUN git clone https://github.com/victor141516/Redpie
RUN pip install -r requirements.txt
RUN pip install gunicorn
CMD ["gunicorn", "-w1", "-b :8000", "gmail:app"]
