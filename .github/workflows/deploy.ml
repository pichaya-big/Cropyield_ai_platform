# .github/workflows/deploy.yml
name: Deploy to Production Server

on:
  push:
    branches: [ "master" ] # เมื่อมีการ Push โค้ดเข้า master

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: 🚀 วิ่งเข้า Server ไปดึงโค้ดและ Build Docker
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            # 1. เข้าไปที่โฟลเดอร์โปรเจกต์บน Server ของคุณ
            cd /path/to/your/project
            
            # 2. ดึงโค้ดใหม่ล่าสุดจาก GitHub
            git pull origin master
            
            # 3. สั่ง Build และรัน Docker ใหม่ทั้งหมดแบบ Background (-d)
            docker-compose up -d --build