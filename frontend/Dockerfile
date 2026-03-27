# Stage 1: Builder
FROM python:3.13-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.headless", "true"]
