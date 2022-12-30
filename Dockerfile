FROM python:3.11-alpine

WORKDIR /app
COPY requirements.txt requirements.txt

RUN apk add --no-cache build-base linux-headers tzdata \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apk del build-base linux-headers

COPY . .

CMD [""]
ENTRYPOINT [ "python3", "/app/sensormqtt.py"]
