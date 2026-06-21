# server/Dockerfile
FROM python:3.12-slim

# คัดลอกโค้ดเข้าไปใน Container
WORKDIR /app
COPY . /app

# ติดตั้ง uv
RUN pip install uv

# 🌟 เพิ่มบรรทัดนี้: ขยายเวลาดาวน์โหลดของ uv เป็น 900 วินาที (15 นาที) เพื่อรองรับไฟล์ขนาดใหญ่
ENV UV_HTTP_TIMEOUT=900

# ติดตั้งแพ็กเกจทั้งหมด (คราวนี้จะไม่หมดเวลาแล้วครับ)
RUN uv pip install --system fastapi uvicorn joblib pandas scikit-learn==1.6.1 xgboost

# รัน FastAPI โดยดึง Port จาก Environment Variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT}"]