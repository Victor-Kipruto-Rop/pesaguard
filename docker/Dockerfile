FROM python:3.12-slim
WORKDIR /app
COPY pesaguard_backend_pipeline/requirements_3.txt ./requirements_3.txt
RUN pip install --no-cache-dir -r requirements_3.txt
COPY . .
CMD ["python", "pesaguard_backend_pipeline/app.py"]
