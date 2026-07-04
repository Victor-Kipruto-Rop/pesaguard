FROM python:3.12-slim
WORKDIR /app
COPY requirements_3.txt ./
RUN pip install --no-cache-dir -r requirements_3.txt
COPY . .
CMD ["python", "app.py"]
