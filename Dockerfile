FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install uv

RUN uv pip install --no-cache-dir -r requirements.txt --system

COPY . .

EXPOSE 5000

CMD ["uv", "run", "app.py"]