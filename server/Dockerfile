# server/Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install uv

# 🌟 ติดตั้ง xgboost แบบระบุให้ดึงแค่ตัวประมวลผลด้วย CPU (ตัดขยะ 300MB ของค่าย NVIDIA ทิ้ง)
RUN uv pip install --system fastapi uvicorn joblib pandas scikit-learn==1.6.1 --extra-index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system xgboost --config-setting=pip_mode=true

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT}"]