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


@app.get("api/")
def read_root():
    return {
        "message": "Welcome to CropYield-AI-Platform API",
        "status": "ready" if model is not None else "model_not_found"
    }


@app.post("api/predict")
def predict_yield(payload: PredictionRequest):
    if model is None or model_features is None:
        raise HTTPException(status_code=500, detail="เซิร์ฟเวอร์ยังไม่พร้อมใช้งานเนื่องจากโหลดไฟล์โมเดลไม่สำเร็จ")
    
    try:
        # 1. สร้าง DataFrame เปล่าที่มีคอลัมน์และลำดับเหมือนตอนเทรนโมเดลเป๊ะๆ (ค่าเริ่มต้นเป็น 0)
        input_df = pd.DataFrame(0, index=[0], columns=model_features)
        
        # ปรับชื่อคอลัมน์ใน DataFrame ให้เป็นตัวพิมพ์เล็กชั่วคราวเพื่อใช้ค้นหาตำแหน่งในการเติมค่า
        cols_lower = [str(c).lower() for c in input_df.columns]
        
        # 2. 🛡️ ตรวจสอบและเติมค่าประเภทตัวเลข (Numerical Features) แบบยืดหยุ่นไม่สนใจตัวพิมพ์เล็ก-ใหญ่
        # ปีเพาะปลูก (Year)
        if 'year' in cols_lower:
            idx = cols_lower.index('year')
            input_df.iloc[0, idx] = int(payload.year)
            
        # ปริมาณน้ำฝนเฉลี่ย (average_rain_fall_mm_per_year)
        if 'average_rain_fall_mm_per_year' in cols_lower:
            idx = cols_lower.index('average_rain_fall_mm_per_year')
            input_df.iloc[0, idx] = float(payload.rain)
            
        # ปริมาณยาฆ่าแมลง (pesticides_tonnes)
        if 'pesticides_tonnes' in cols_lower:
            idx = cols_lower.index('pesticides_tonnes')
            input_df.iloc[0, idx] = float(payload.pesticide)
            
        # อุณหภูมิเฉลี่ย (avg_temp)
        if 'avg_temp' in cols_lower:
            idx = cols_lower.index('avg_temp')
            input_df.iloc[0, idx] = float(payload.temp)


        # 3. 🗺️ จัดการ One-Hot Encoding แบบยืดหยุ่นรองรับทุกรูปแบบ (ตัวเล็ก/ตัวใหญ่/ขีดล่าง)
        # จำลองค่าข้อความประเทศ และชนิดพืช
        country_target = f"area_{payload.country}".lower()
        item_target = f"item_{payload.item}".lower()
        
        # ค้นหาและเปิดสวิตช์ (เปลี่ยนเป็น 1) ในคอลัมน์ที่ชื่อตรงกัน
        for i, col_name in enumerate(cols_lower):
            if col_name == country_target or col_name.endswith(f"_{payload.country}".lower()):
                input_df.iloc[0, i] = 1
            if col_name == item_target or col_name.endswith(f"_{payload.item}".lower()):
                input_df.iloc[0, i] = 1
                
        # 4. 🚀 ส่งข้อมูลเข้าสมองกลโมเดลเพื่อพยากรณ์ผลลัพธ์
        prediction_result = model.predict(input_df)[0]
        
        return {
            "status": "success",
            "data": {
                "input_summary": {
                    "country": payload.country,
                    "item": payload.item,
                    "year": payload.year
                },
                "prediction_hg_ha": float(prediction_result)
            }
        }
        
    except Exception as error:
        # แสดงข้อผิดพลาดที่เกิดขึ้นจริงออกทางคอนโซลหลังบ้านเพื่อใช้ดีบั๊กงาน
        import traceback
        print("❌ [DEBUG ERROR]:", traceback.format_exc())
        raise HTTPException(
            status_code=400, 
            detail=f"เกิดข้อผิดพลาดภายในระบบประมวลผลโมเดล: {str(error)}"
        )