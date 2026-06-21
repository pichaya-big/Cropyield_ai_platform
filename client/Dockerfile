# client/Dockerfile
# 🌟 เปลี่ยนจาก node:18 เป็น node:22-alpine ให้เข้าคู่กับ Vite เวอร์ชันล่าสุด
FROM node:22-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build
RUN npm install -g serve

CMD ["sh", "-c", "serve -s dist -l ${FRONTEND_PORT}"]