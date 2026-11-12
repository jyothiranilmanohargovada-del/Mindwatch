FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Rebuild data + model inside the image so the pickle matches the installed scikit-learn
RUN python -m src.generate_sample_data && python -m src.train
RUN useradd -m app && chown -R app /app
USER app
ENV MINDWATCH_DB=/app/data_store/mindwatch.db
RUN mkdir -p /app/data_store
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app.app:create_app()"]
