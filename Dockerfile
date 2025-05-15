FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip

RUN pip install -i  https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir -r requirements.txt

COPY src/ .

COPY .env .

EXPOSE 8000

CMD ["gunicorn", "auth.wsgi:application", "--bind", "0.0.0.0:8000"]
