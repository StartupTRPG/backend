#!/bin/bash

# 배포 스크립트 - StartupTRPG Backend
set -e  # 에러 발생 시 스크립트 중단

echo "🚀 StartupTRPG Backend 배포 시작..."

# 1. 최신 코드 가져오기
echo " 최신 코드를 가져오는 중..."
git pull origin main

# 2. 기존 컨테이너 중지 및 제거
echo "🛑 기존 컨테이너 중지 중..."
docker-compose down

# 3. 새로운 이미지 빌드 (변경사항이 있을 경우)
echo "🔨 Docker 이미지 빌드 중..."
docker-compose build --no-cache

# 4. 컨테이너 시작
echo "▶️  컨테이너 시작 중..."
docker-compose up -d

# 5. 헬스 체크
echo " 헬스 체크 중..."
sleep 10  # 애플리케이션 시작 대기

# 헬스 체크 시도 (최대 30초)
for i in {1..6}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 배포 성공! 애플리케이션이 정상적으로 실행 중입니다."
        echo "🌐 서버 주소: http://localhost:8000"
        echo "📚 API 문서: http://localhost:8000/docs"
        exit 0
    else
        echo "⏳ 헬스 체크 시도 $i/6... (5초 대기)"
        sleep 5
    fi
done

echo "❌ 배포 실패: 헬스 체크에 실패했습니다."
echo "📋 로그 확인: docker-compose logs -f"
exit 1