from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
import os

app = FastAPI(
    title="CropYield-AI-Platform API",
    description="Backend Server สำหรับระบบพยากรณ์ผลผลิตทางการเกษตร (FastAPI + uv)",
    version="1.0.0"
)

# 🌐 ตั้งค่า CORS (Cross-Origin Resource Sharing)
# เพื่ออนุญาตให้ฝั่ง client (Vite) ที่รันคนละพอร์ตสามารถส่งข้อมูลมาหาหลังบ้านได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ใน Production จริงสามารถเจาะจงเฉพาะเช่น ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 กำหนด Path ของไฟล์โมเดลที่สอดคล้องกับที่คุณเซฟมาจาก Google Colab
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, 'crop_yield_stacking_model.pkl') # อัปเดตชื่อไฟล์ตรงนี้ครับ
FEATURES_PATH = os.path.join(CURRENT_DIR, 'features_list.pkl')         # อัปเดตชื่อไฟล์ตรงนี้ครับ

# 🤖 โหลดโมเดลและฟีเจอร์เตรียมไว้ตั้งแต่ตอน Start Server
try:
    if not os.path.exists(MODEL_PATH) or not os.path.exists(FEATURES_PATH):
        raise FileNotFoundError("ไม่พบไฟล์ .pkl ในโฟลเดอร์ server กรุณาตรวจสอบว่าย้ายไฟล์มาถูกที่และชื่อตรงกัน")
        
    model = joblib.load(MODEL_PATH)
    model_features = joblib.load(FEATURES_PATH)
    print("🎯 [SUCCESS] โหลดไฟล์ Stacking Model และ Features List เข้าสู่ระบบเรียบร้อยแล้ว!")
except Exception as e:
    print(f"❌ [ERROR] เกิดข้อผิดพลาดในการโหลดโมเดล: {e}")
    model = None
    model_features = None


# 📝 กำหนด Schema ของข้อมูลที่รับมาจากหน้าบ้าน (Vite) ด้วย Pydantic
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
    if model is None or model_features is None:
        raise HTTPException(status_code=500, detail="เซิร์ฟเวอร์ยังไม่พร้อมใช้งานเนื่องจากโหลดไฟล์โมเดลไม่สำเร็จ")
    
    try:
        # 1. สร้าง DataFrame เปล่าที่มีคอลัมน์และลำดับเหมือนตอนเทรนโมเดลเป๊ะๆ (เริ่มต้นเป็น 0)
        input_df = pd.DataFrame(0.0, index=[0], columns=model_features)
        
        # 2. เติมค่าประเภทตัวเลข (Numerical Features) โดยจับคู่ชื่อคอลัมน์แบบ Case-Insensitive
        for col in input_df.columns:
            col_lower = str(col).lower()
            
            if col_lower == 'year':
                input_df[col] = int(payload.year)
            elif col_lower == 'average_rain_fall_mm_per_year':
                input_df[col] = float(payload.rain)
            elif col_lower == 'pesticides_tonnes':
                input_df[col] = float(payload.pesticide)
            elif col_lower == 'avg_temp':
                # 🛡️ ป้องกันอุณหภูมิเวอร์เกินจริง (Data Validation)
                if payload.temp > 60:
                    input_df[col] = 35.0  # ดักไว้ไม่ให้โมเดลหลุดเพดานบินแช่แข็ง
                else:
                    input_df[col] = float(payload.temp)

        # 3. 🔥 แก้บั๊ก One-Hot Encoding (เปิดสวิตช์คอลัมน์ประเทศและพืชให้เป็น 1)
        # สร้างแพทเทิร์นชื่อคอลัมน์ที่คาดหวัง เช่น "area_thailand" หรือ "item_potatoes"
        target_country_col = f"area_{payload.country.strip()}".lower()
        target_item_col = f"item_{payload.item.strip()}".lower()
        
        for col in input_df.columns:
            col_lower = str(col).lower().replace(" ", "_") # ล้างฟอร์แมตช่องว่าง
            
            if col_lower == target_country_col or col_lower == target_item_col:
                input_df[col] = 1.0  # เปิดสวิตช์เป็น 1 ให้โมเดลรับรู้พืชและประเทศ!

        # 4. ตรวจสอบและแปลง Data Type ให้ตรงกับโมเดล
        for col in input_df.columns:
            if str(col).lower() == 'year':
                input_df[col] = input_df[col].astype('int64')
            else:
                input_df[col] = input_df[col].astype('float64')
                
        # 5. 🚀 ส่งข้อมูลทำนายผล
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
                "prediction_hg_ha": float(prediction_result)
            }
        }
        
    except Exception error:
        import traceback
        print("❌ [DEBUG ERROR]:", traceback.format_exc())
        raise HTTPException(
            status_code=400, 
            detail=f"เกิดข้อผิดพลาดภายในระบบประมวลผลโมเดล: {str(error)}"
        )