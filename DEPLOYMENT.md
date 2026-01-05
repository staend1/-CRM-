# 클라우드타입 배포 가이드

## 📦 스택 정보

### 언어 및 프레임워크
- **언어**: Python 3.13.0
- **프레임워크**: Flask 3.0.0
- **WSGI 서버**: Gunicorn 21.2.0

### 주요 라이브러리
- `fuzzywuzzy==0.18.0` - 문자열 유사도 매칭
- `python-Levenshtein==0.27.3` - 편집 거리 계산 (성능 최적화)

---

## 🚀 클라우드타입 배포 방법

### 1. 클라우드타입 접속
1. https://cloudtype.io/ 접속
2. GitHub 계정으로 로그인

### 2. 새 프로젝트 생성
1. **"새 프로젝트"** 클릭
2. 프로젝트 이름: `salesmap-crm-mapper` (원하는 이름)
3. **"생성"** 클릭

### 3. 서비스 추가
1. **"새 서비스"** 클릭
2. **"GitHub 연동"** 선택
3. 저장소 선택: `staend1/-CRM-`
4. 브랜치: `main`

### 4. 빌드 설정

#### ✅ 빌드 설정 (자동 감지됨)
클라우드타입이 자동으로 감지합니다:
- `runtime.txt` → Python 버전
- `requirements.txt` → 의존성 패키지
- `Procfile` → 실행 명령어

#### 수동 설정 (필요 시)
**빌드 명령어:**
```bash
pip install -r requirements.txt
```

**실행 명령어:**
```bash
bash start.sh
```
또는
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
```

**포트:**
- 자동 감지 (환경변수 `PORT` 사용)
- 기본값: 8080

### 5. 환경 변수 설정

❌ **환경 변수 없음** - 별도 설정 불필요!

이 앱은 환경 변수가 필요 없습니다. 모든 설정이 코드에 포함되어 있습니다.

### 6. 배포 실행
1. **"배포"** 버튼 클릭
2. 빌드 진행 상황 확인 (약 2-3분 소요)
3. 배포 완료 후 자동으로 URL 생성됨

---

## 🔧 클라우드타입 설정 요약

```yaml
# 프로젝트 설정
프로젝트 이름: salesmap-crm-mapper
저장소: https://github.com/staend1/-CRM-.git
브랜치: main

# 스택
언어: Python
버전: 3.13.0 (runtime.txt)
프레임워크: Flask

# 빌드
빌드 명령어: pip install -r requirements.txt
실행 명령어: gunicorn app:app (Procfile에 정의됨)

# 포트
포트: 자동 감지 (환경변수 PORT 사용)

# 환경 변수
없음 (Not Required)

# 리소스
CPU: 0.25 Core (Free Tier)
Memory: 512MB (Free Tier)
```

---

## 📊 배포 후 확인 사항

### 1. 배포 성공 확인
- 클라우드타입 대시보드에서 **"Running"** 상태 확인
- 생성된 URL 클릭하여 접속 테스트

### 2. 기능 테스트
1. 그룹 수 설정 (2~10개)
2. 데이터 입력 (엑셀/구글 시트 복사-붙여넣기)
3. "분석 시작" 클릭
4. 결과 확인:
   - 매핑 커버리지 분석
   - 차집합 분석 (유사 항목 추천)
   - 교집합 분석

### 3. 로그 확인
클라우드타입 대시보드 → **"로그"** 탭에서 실시간 로그 확인

---

## 🐛 트러블슈팅

### 빌드 실패 시
**에러:** `No module named 'fuzzywuzzy'`
**해결:** requirements.txt 파일 확인 및 재배포

**에러:** `Port already in use`
**해결:** 클라우드타입이 자동으로 포트 할당함 (문제 없음)

### 배포는 성공했지만 접속 안 될 때
1. 로그 확인: `gunicorn` 정상 실행 여부
2. 포트 바인딩: `0.0.0.0`으로 설정되어 있는지 확인
3. 방화벽: 클라우드타입은 자동으로 방화벽 설정

---

## 🔄 재배포 방법

### 코드 수정 후 자동 배포
1. 로컬에서 코드 수정
2. Git commit & push:
```bash
cd "/Users/siyeol/Desktop/매핑 키 검사기"
git add .
git commit -m "Update: 기능 개선"
git push origin main
```
3. 클라우드타입이 **자동으로 재배포** (Webhook 설정 시)

### 수동 재배포
클라우드타입 대시보드 → **"재배포"** 버튼 클릭

---

## 📝 참고 사항

### 무료 플랜 제한사항
- **CPU**: 0.25 Core
- **메모리**: 512MB
- **대역폭**: 제한 있음
- **동시 접속**: 제한 있음

### 성능 최적화
- Fuzzy Matching은 CPU 집약적이므로 대량 데이터(1000개 이상) 처리 시 시간 소요
- 필요 시 유료 플랜으로 업그레이드 고려

### 도메인 연결
클라우드타입에서 제공하는 기본 도메인:
- `https://your-app-name.cloudtype.app`

커스텀 도메인 연결:
- 클라우드타입 대시보드 → **"도메인"** 탭에서 설정

---

## 🎉 배포 완료!

배포가 완료되면:
- URL: `https://[your-app].cloudtype.app`
- 이 URL을 공유하여 누구나 접속 가능
- HTTPS 자동 적용 (SSL 인증서 자동 발급)

---

## 📧 지원

문제가 발생하면:
- GitHub Issues: https://github.com/staend1/-CRM-/issues
- 클라우드타입 문서: https://docs.cloudtype.io/
