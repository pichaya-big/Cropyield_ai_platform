from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
import os

app = FastAPI(
    title="CropYield-AI-Platform API",
    description="Backend Server สำหรับระบบพยากรณ์ผลผลิต (สลับใช้ Pipeline ของเพื่อน)",
    version="1.1.0"
)

# 🌐 ตั้งค่า CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 กำหนด Path ชี้ไปที่ไฟล์โมเดล Pipeline ของเพื่อนชิ้นเดียวโดดๆ
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, 'crop_yield_model.pkl') 

# 🤖 โหลดโมเดล Pipeline ขึ้นมารอไว้
try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("ไม่พบไฟล์ friend_model.pkl ในโฟลเดอร์เซิร์ฟเวอร์ กรุณาตรวจสอบการวางไฟล์")
        
    model = joblib.load(MODEL_PATH)
    print("🎯 [SUCCESS] โหลดโมเดล Pipeline ของเพื่อนสำเร็จ! พร้อมแปลงข้อมูลอัตโนมัติ")
except Exception as e:
    print(f"❌ [ERROR] โหลดโมเดลไม่สำเร็จ: {e}")
    model = None


# 📝 Schema รับข้อมูลจากหน้าบ้าน (เหมือนเดิมทุกประการ ไม่ต้องแก้ UI)
class PredictionRequest(BaseModel):
    country: str
    item: str
    year: int
    rain: float
    temp: float
    pesticide: float


@app.get("/")
def read_root():
    return {
        "message": "Welcome to CropYield-AI-Platform API",
        "status": "ready" if model is not None else "model_not_found"
    }


@app.post("/api/predict")
def predict_yield(payload: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="เซิร์ฟเวอร์ยังไม่พร้อมใช้งานเนื่องจากโหลดไฟล์โมเดลไม่สำเร็จ")
    
    try:
        # ✨ จุดเปลี่ยนชีวิต: สร้าง DataFrame ดิบๆ ส่งให้ Pipeline ของเพื่อนไป One-Hot ทำเองข้างใน
        # ⚠️ ข้อสำคัญ: ชื่อคอลัมน์ฝั่งซ้าย ต้องสะกดตรงกับชื่อคอลัมน์ดั้งเดิมในไฟล์ CSV ที่เพื่อนใช้เทรนเป๊ะๆ 
        input_df = pd.DataFrame([{
            'Area': payload.country.strip(),
            'Item': payload.item.strip(),
            'Year': int(payload.year),
            'average_rain_fall_mm_per_year': float(payload.rain),
            'pesticides_tonnes': float(payload.pesticide),
            'avg_temp': float(payload.temp)
        }])
        
        # 🚀 ยิงข้อมูลเข้าโมเดลของเพื่อนตรงๆ ไม่ต้องวนลูปสับคอลัมน์เองให้เมื่อยแล้วครับ
        prediction_result = model.predict(input_df)[0]
        
        return {
            "status": "success",
            "data": {
                "input_summary": {
                    "country": payload.country,
                    "item": payload.item,
                    "year": payload.year,
                    "rain": payload.rain,
                    "temp": payload.temp
                },
                "prediction_hg_ha": float(prediction_result) # พ่นค่าหลักแสนดิบๆ ส่งให้สูตรหน้าบ้านหารต่อ
            }
        }
        
    except Exception as error:
        import traceback
        print("❌ [DEBUG ERROR]:", traceback.format_exc())
        raise HTTPException(
            status_code=400, 
            detail=f"เกิดข้อผิดพลาดในการทำนายผลผ่าน Pipeline: {str(error)}"
        )