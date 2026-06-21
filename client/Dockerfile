# client/Dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
# คอมไพล์โปรเจกต์ Vite
RUN npm run build

# ติดตั้ง 'serve' สำหรับเสิร์ฟไฟล์ Static โดยไม่พึ่ง Nginx
RUN npm install -g serve

# รัน Serve ชี้ไปที่โฟลเดอร์ dist และบังคับ Port ตาม .env
CMD ["sh", "-c", "serve -s dist -l ${FRONTEND_PORT}"]