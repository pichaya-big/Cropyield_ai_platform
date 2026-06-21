# server/Dockerfile
FROM python:3.12-slim

# คัดลอกโค้ดเข้าไปใน Container
WORKDIR /app
COPY . /app

# ติดตั้ง uv และแพ็กเกจ (เพื่อความรวดเร็วและเสถียร)
RUN pip install uv
RUN uv pip install --system fastapi uvicorn joblib pandas scikit-learn==1.6.1 xgboost

# รัน FastAPI โดยดึง Port จาก Environment Variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT}"]