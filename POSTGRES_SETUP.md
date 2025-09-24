# PostgreSQL 설치 및 설정 가이드

## 🗄️ PostgreSQL이란?
PostgreSQL은 문서 메타데이터, 처리 작업 로그, 청크 정보를 체계적으로 관리하기 위한 관계형 데이터베이스입니다.

## 📦 1. PostgreSQL 설치

### macOS (Homebrew 사용)
```bash
# PostgreSQL 설치
brew install postgresql@15

# PostgreSQL 서비스 시작
brew services start postgresql@15

# PostgreSQL 버전 확인
psql --version
```

### Ubuntu/Debian
```bash
# 패키지 업데이트
sudo apt update

# PostgreSQL 설치
sudo apt install postgresql postgresql-contrib

# PostgreSQL 서비스 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Windows
1. [PostgreSQL 공식 사이트](https://www.postgresql.org/download/windows/)에서 설치 프로그램 다운로드
2. 설치 프로그램 실행 및 기본 설정으로 설치
3. 설치 중 superuser 비밀번호 설정

## 🔧 2. 데이터베이스 및 사용자 생성

### PostgreSQL에 접속
```bash
# macOS/Linux
psql postgres

# Windows (PostgreSQL이 설치된 경우)
psql -U postgres
```

### 데이터베이스 및 사용자 생성
```sql
-- 새 데이터베이스 생성
CREATE DATABASE prefect_docs;

-- 새 사용자 생성 (선택사항)
CREATE USER prefect_user WITH PASSWORD 'your_secure_password';

-- 사용자에게 데이터베이스 권한 부여
GRANT ALL PRIVILEGES ON DATABASE prefect_docs TO prefect_user;

-- 연결 확인
\l  -- 데이터베이스 목록 확인
\q  -- 종료
```

## ⚙️ 3. 환경 변수 설정

### .env 파일에 PostgreSQL 설정 추가
```bash
# PostgreSQL 설정
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=prefect_docs
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=your_postgres_password
```

## 🧪 4. 연결 테스트

### Python에서 연결 테스트
```bash
cd /Users/a09156/Desktop/workforce/prefect_test
source venv/bin/activate

# 테스트 스크립트 실행
python -c "
from flow.database import db_manager
db_manager.initialize()
if db_manager.test_connection():
    print('✅ PostgreSQL 연결 성공!')
else:
    print('❌ PostgreSQL 연결 실패')
"
```

## 📊 5. 테이블 구조

Prefect 파이프라인이 자동으로 생성하는 테이블들:

### `document_metadata` - 문서 메타데이터
- `id`: UUID, Primary Key
- `doc_id`: 고유 문서 ID
- `document_path`: 파일 경로
- `document_name`: 파일명
- `processing_status`: 처리 상태
- `total_pages`, `processed_pages`: 페이지 정보
- `file_size`, `file_hash`: 파일 정보
- `created_at`, `updated_at`: 시간 정보

### `document_chunks` - 문서 청크 정보
- `id`: UUID, Primary Key  
- `chunk_id`: 고유 청크 ID
- `doc_id`: 참조 문서 ID
- `page_number`: 페이지 번호
- `chunk_type`: 청크 타입 (text, image, combined)
- `content`: 텍스트 내용
- `image_description`: 이미지 설명
- `milvus_id`: Milvus DB의 ID

### `processing_jobs` - 처리 작업 로그
- `id`: UUID, Primary Key
- `job_id`: 고유 작업 ID
- `doc_id`: 처리된 문서 ID
- `job_status`: 작업 상태 (running, completed, failed)
- `total_chunks`, `successful_chunks`: 처리 통계
- `started_at`, `completed_at`: 시간 정보

## 🔍 6. 데이터 조회 예제

### psql에서 데이터 확인
```sql
-- prefect_docs 데이터베이스 연결
\c prefect_docs

-- 모든 문서 목록
SELECT doc_id, document_name, processing_status, total_pages, created_at 
FROM document_metadata 
ORDER BY created_at DESC;

-- 특정 문서의 청크 정보
SELECT chunk_id, chunk_type, page_number, char_count 
FROM document_chunks 
WHERE doc_id = 'your_doc_id' 
ORDER BY page_number;

-- 처리 작업 통계
SELECT job_status, COUNT(*) as count 
FROM processing_jobs 
GROUP BY job_status;
```

## 🚨 7. 문제 해결

### 연결 오류
```bash
# PostgreSQL 서비스 상태 확인
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux

# 포트 확인
netstat -an | grep 5432

# 로그 확인
tail -f /usr/local/var/log/postgresql@15.log  # macOS
sudo tail -f /var/log/postgresql/postgresql-*.log  # Linux
```

### 권한 오류
```sql
-- 사용자 권한 확인
\du

-- 권한 다시 부여
GRANT ALL PRIVILEGES ON DATABASE prefect_docs TO your_username;
GRANT ALL ON SCHEMA public TO your_username;
```

## 📈 8. 성능 최적화 (선택사항)

### PostgreSQL 설정 조정
```sql
-- 연결 수 확인
SHOW max_connections;

-- 현재 연결 수 확인
SELECT count(*) FROM pg_stat_activity;
```

### 인덱스 추가 (필요시)
```sql
-- 자주 검색하는 필드에 인덱스 생성
CREATE INDEX idx_document_metadata_doc_id ON document_metadata(doc_id);
CREATE INDEX idx_document_chunks_doc_id ON document_chunks(doc_id);
CREATE INDEX idx_processing_jobs_status ON processing_jobs(job_status);
```

## ✅ 완료 확인

모든 설정이 완료되면:
1. ✅ PostgreSQL 서비스 실행 중
2. ✅ `prefect_docs` 데이터베이스 생성됨
3. ✅ 환경 변수 설정됨
4. ✅ Python에서 연결 테스트 성공

이제 Prefect 파이프라인을 실행하면 자동으로 문서 메타데이터가 PostgreSQL에 저장됩니다! 🎉
