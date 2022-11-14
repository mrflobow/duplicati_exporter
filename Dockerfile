FROM python:3.10-alpine
EXPOSE 9123
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY exporter.py .

CMD [ "python", "./exporter.py" ]