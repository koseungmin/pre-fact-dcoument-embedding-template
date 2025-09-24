# 📄 Document Processing Pipeline with Prefect

AI 기반 문서 처리 파이프라인입니다. PDF 문서에서 텍스트와 이미지를 추출하고, GPT Vision으로 이미지 설명을 생성한 후, 벡터 데이터베이스에 저장하여 검색 가능하도록 만드는 완전 자동화된 시스템입니다.

## 🏗️ 시스템 구조

```
📦 prefect_test/
├── 🎛️ base/                    # Prefect 관리 스크립트
│   ├── start_prefect_server.py # Prefect UI 서버 시작
│   ├── start_worker.py         # 워커 프로세스 시작
│   ├── deploy_pipeline.py      # 파이프라인 배포
│   └── run_flow.py            # Flow 등록
├── 🧠 flow/                    # 핵심 파이프라인 로직
│   ├── config.py              # 환경 설정
│   ├── database.py            # PostgreSQL 데이터 모델
│   └── document_processing_pipeline.py  # 메인 파이프라인
├── 🚢 k8s/                     # Kubernetes 배포 (선택사항)
├── 🖼️ extracted_image/         # 추출된 이미지들
├── 📋 prefect.yaml             # Prefect 배포 설정
├── 🔧 requirements.txt         # Python 패키지
├── ▶️ run_document_pipeline.py # 직접 실행 스크립트
├── 🔍 run_search.py           # 검색 스크립트
└── 📄 test.pdf               # 샘플 PDF 파일
```

## 🚀 빠른 시작 가이드

### 1단계: 환경 설정

```bash
# 가상환경 활성화
source venv/bin/activate

# 환경변수 설정 (.env 파일 생성)
cp env.template .env
# .env 파일을 편집하여 Azure OpenAI 정보 입력
```

### 2단계: Prefect UI 서버 시작

```bash
# 터미널 1: Prefect 서버 시작 (백그라운드에서 계속 실행)
python base/start_prefect_server.py
```

✅ **서버 실행 확인**: http://127.0.0.1:4200 접속 가능

### 3단계: 파이프라인 배포

```bash
# 터미널 2: 파이프라인을 Prefect에 배포
python base/deploy_pipeline.py
```

✅ **배포 확인**: Prefect UI → Deployments 메뉴에서 `document-processing-pipeline` 확인

### 4단계: 워커 시작

```bash
# 터미널 3: 실제 작업을 수행할 워커 시작
python base/start_worker.py
```

✅ **워커 확인**: Prefect UI → Workers 메뉴에서 활성 워커 확인

## 🎯 파이프라인 실행 방법

### A. 웹 UI에서 실행 (추천)

1. **브라우저에서 접속**: http://127.0.0.1:4200
2. **Deployments 메뉴** 클릭
3. **`document-processing-pipeline`** 선택
4. **Quick Run** 버튼 클릭
5. **Parameters 설정**:
   ```json
   {
     "document_path": "/Users/a09156/Desktop/workforce/prefect_test/test.pdf",
     "skip_image_processing": false,
     "max_pages": 50
   }
   ```

### B. 명령줄에서 직접 실행

```bash
# 50페이지로 제한하여 실행
MAX_PAGES_TO_PROCESS=50 python run_document_pipeline.py
```

## ⏰ 스케줄 설정하기

### 1. 기본 스케줄 (이미 설정됨)
- **현재 설정**: 매년 1월 1일 자정 실행
- **위치**: `prefect.yaml` 파일의 `schedule` 섹션

### 2. UI에서 스케줄 변경

1. **Deployments** → **`document-processing-pipeline`** 선택
2. **Edit** 버튼 클릭
3. **Schedule** 탭에서 크론 표현식 수정:

```bash
# 매일 오전 9시
0 9 * * *

# 매주 월요일 오후 2시
0 14 * * 1

# 매월 1일 오전 6시
0 6 1 * *

# 매 시간마다
0 * * * *
```

### 3. 스케줄 활성화/비활성화
- **Deployments** 페이지에서 토글 스위치로 on/off 가능

## 🔧 주요 설정 파일들

### `prefect.yaml` - 파이프라인 정의
```yaml
deployments:
  - name: document-processing-pipeline
    entrypoint: flow/document_processing_pipeline.py:document_processing_pipeline
    parameters:
      document_path: "/Users/a09156/Desktop/workforce/prefect_test/test.pdf"
    schedule:
      cron: "0 0 1 1 *"  # 스케줄 설정
      timezone: "Asia/Seoul"
```

### `flow/document_processing_pipeline.py` - 메인 로직
```python
@flow(
    name="document_processing_pipeline",
    description="4단계 문서 처리 파이프라인",
    task_runner=ConcurrentTaskRunner()
)
def document_processing_pipeline(
    document_path: str,
    skip_image_processing: bool = False,
    max_pages: Optional[int] = None
):
    # 파이프라인 로직...
```

## 📊 파이프라인 단계별 설명

### 1단계: 텍스트 추출 📝
- PDF에서 모든 텍스트를 페이지별로 추출
- PyMuPDF를 사용한 고품질 텍스트 추출

### 2단계: 이미지 캡처 📸
- PDF를 페이지별 이미지로 변환
- `extracted_image/` 폴더에 PNG 형태로 저장

### 3단계: GPT Vision 설명 생성 🤖
- Azure OpenAI GPT-4 Vision으로 각 이미지 분석
- 한국어로 상세한 설명 생성

### 4단계: 벡터 데이터베이스 구성 🔍
- 텍스트 + 이미지 설명을 결합
- Azure OpenAI text-embedding-3-large로 벡터화
- Milvus Lite에 저장하여 검색 가능

### 5단계: PostgreSQL 메타데이터 저장 💾
- 문서 메타데이터, 청크 정보, 작업 로그를 관계형 DB에 저장
- 테이블: `DOCUMENT_METADATA`, `DOCUMENT_CHUNKS`, `PROCESSING_JOBS`

## 🔍 검색 기능

처리 완료된 문서를 검색할 수 있습니다:

```bash
# 검색 실행
python run_search.py "16비트 데이터"
python run_search.py "워드형 라벨"
python run_search.py "비트 디바이스"
```

## 📈 모니터링 및 로그

### Prefect UI에서 확인 가능:
- **Flow Runs**: 모든 실행 히스토리
- **Task Runs**: 각 단계별 실행 상태
- **Logs**: 실시간 로그 스트림
- **Artifacts**: 실행 결과물

### 주요 메트릭:
- 처리된 총 페이지 수
- 생성된 이미지 개수
- Vector DB 저장된 항목 수
- 처리 시간 및 성능

## 🚀 VS Code Launch 설정 (선택사항)

`.vscode/launch.json`을 만들어서 빠르게 실행할 수 있습니다:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "🖥️ Prefect Server",
            "type": "python",
            "request": "launch",
            "program": "base/start_prefect_server.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "🏃 Prefect Worker", 
            "type": "python",
            "request": "launch",
            "program": "base/start_worker.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "🚀 Deploy Pipeline",
            "type": "python", 
            "request": "launch",
            "program": "base/deploy_pipeline.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "▶️ Run Pipeline Direct",
            "type": "python",
            "request": "launch", 
            "program": "run_document_pipeline.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "env": {
                "MAX_PAGES_TO_PROCESS": "50"
            }
        }
    ]
}
```

### 🔄 **재시작 시나리오별 실행:**

#### **첫 번째 설정 (최초 1회)**
1. VS Code → Run → `🖥️ Prefect Server` 
2. VS Code → Run → `🚀 Deploy Pipeline`
3. VS Code → Run → `🏃 Prefect Worker`

#### **일반적인 재시작 (코드 변경 없음)**
1. VS Code → Run → `🖥️ Prefect Server`
2. VS Code → Run → `🏃 Prefect Worker`

#### **코드 수정 후 재시작**
1. VS Code → Run → `🖥️ Prefect Server`
2. VS Code → Run → `🚀 Deploy Pipeline` (변경사항 반영)
3. VS Code → Run → `🏃 Prefect Worker`

## 🔧 문제 해결

### 1. 서버가 시작되지 않을 때
```bash
# 기존 프로세스 종료
pkill -f "prefect.*server"
pkill -f "prefect.*worker"

# 다시 시작
python base/start_prefect_server.py
```

### 2. 배포가 실패할 때
```bash
# prefect.yaml 파일 확인
# 환경변수 설정 확인
python -c "from flow.config import config; config.validate_config()"
```

### 3. 워커가 작업을 받지 않을 때
```bash
# 워커 재시작
python base/start_worker.py
```

### 4. 파이프라인 실행 오류
- **Azure OpenAI 키 확인**: `.env` 파일의 API 키
- **PDF 파일 경로 확인**: 파일이 존재하는지 확인
- **디스크 용량 확인**: 이미지 저장 공간 충분한지 확인

## 🌟 고급 설정

### 병렬 처리 조정
`flow/document_processing_pipeline.py`에서 `ConcurrentTaskRunner` 설정 변경:

```python
@flow(task_runner=ConcurrentTaskRunner(max_workers=5))
```

### 페이지 처리 제한
환경변수로 조정:
```bash
export MAX_PAGES_TO_PROCESS=100
```

### 데이터베이스 설정
`flow/config.py`에서 PostgreSQL 연결 정보 수정

## 📚 추가 리소스

- **Prefect 공식 문서**: https://docs.prefect.io/
- **Azure OpenAI 문서**: https://learn.microsoft.com/azure/ai-services/openai/
- **Milvus 문서**: https://milvus.io/docs

---

## ❓ FAQ

**Q: 다른 PDF 파일을 처리하고 싶어요**  
A: Prefect UI에서 Quick Run 시 `document_path` 파라미터를 변경하거나, `prefect.yaml`의 기본값을 수정하세요.

**Q: 스케줄을 매일 실행으로 바꾸고 싶어요**  
A: Prefect UI → Deployments → Edit → Schedule에서 크론 표현식을 `0 9 * * *`로 변경하세요.

**Q: 처리 결과를 어떻게 확인하나요?**  
A: `python run_search.py "검색어"`로 처리된 내용을 검색할 수 있습니다.

**Q: 여러 문서를 동시에 처리할 수 있나요?**  
A: 현재는 한 번에 하나씩만 처리됩니다. 여러 파일은 각각 별도로 실행해주세요.

---

🎉 **이제 시작하세요!** 터미널에서 `python base/start_prefect_server.py`를 실행하고 http://127.0.0.1:4200 에서 멋진 Prefect UI를 만나보세요!# pre-fact-dcoument-embedding-template
