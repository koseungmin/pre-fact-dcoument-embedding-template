#!/usr/bin/env python3
"""
PostgreSQL 데이터베이스 모델 및 연결 관리
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, JSON, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from typing import Optional, Dict, Any
import logging

from config import config

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

class Document(Base):
    """통합 문서 테이블 (기존 업로드 시스템 + 처리 파이프라인)"""
    __tablename__ = "DOCUMENTS"
    
    # 문서 타입 상수
    TYPE_COMMON = 'common'
    TYPE_TYPE1 = 'type1'
    TYPE_TYPE2 = 'type2'
    VALID_DOCUMENT_TYPES = [TYPE_COMMON, TYPE_TYPE1, TYPE_TYPE2]
    
    # 기본 정보 (업로드 시스템 기존 필드)
    document_id = Column('DOCUMENT_ID', String(50), primary_key=True)
    document_name = Column('DOCUMENT_NAME', String(255), nullable=False)
    original_filename = Column('ORIGINAL_FILENAME', String(255), nullable=False)
    
    # 파일 정보 (업로드 시스템 기존 필드)
    file_key = Column('FILE_KEY', String(255), nullable=False)
    file_size = Column('FILE_SIZE', Integer, nullable=False)
    file_type = Column('FILE_TYPE', String(100), nullable=False)  # MIME 타입
    file_extension = Column('FILE_EXTENSION', String(10), nullable=False)
    upload_path = Column('UPLOAD_PATH', String(500), nullable=False)  # 실제 파일 경로
    
    # 사용자 정보 (업로드 시스템 기존 필드)
    user_id = Column('USER_ID', String(50), nullable=False)
    is_public = Column('IS_PUBLIC', Boolean, nullable=False, server_default=text('false'))
    permissions = Column('PERMISSIONS', JSON, nullable=True, comment='권한 목록 (문자열 배열)')
    document_type = Column('DOCUMENT_TYPE', String(20), nullable=False, server_default=text('\'common\''), comment='문서 타입 (common, type1, type2)')
    
    # 처리 상태 (업로드 시스템 기존 + 확장)
    status = Column('STATUS', String(20), nullable=False, server_default=text('\'processing\''))
    error_message = Column('ERROR_MESSAGE', Text, nullable=True)
    
    # 시간 정보 (업로드 시스템 기존)
    create_dt = Column('CREATE_DT', DateTime, nullable=False, server_default=func.now())
    is_deleted = Column('IS_DELETED', Boolean, nullable=False, server_default=text('false'))
    
    # ========== 확장 필드들 (처리 파이프라인용, Optional) ==========
    
    # 문서 처리 정보 (Optional)
    total_pages = Column('TOTAL_PAGES', Integer, nullable=True, default=0)
    processed_pages = Column('PROCESSED_PAGES', Integer, nullable=True, default=0)
    file_hash = Column('FILE_HASH', String(64), nullable=True)  # 중복 체크용
    
    # 벡터화 정보 (Optional)
    milvus_collection_name = Column('MILVUS_COLLECTION_NAME', String(255), nullable=True)
    vector_count = Column('VECTOR_COUNT', Integer, nullable=True, default=0)
    
    # 문서 메타데이터 (Optional)
    language = Column('LANGUAGE', String(10), nullable=True)
    author = Column('AUTHOR', String(255), nullable=True)
    subject = Column('SUBJECT', String(500), nullable=True)
    
    # JSON 필드 (Optional)
    metadata_json = Column('METADATA_JSON', JSON, nullable=True)
    processing_config = Column('PROCESSING_CONFIG', JSON, nullable=True)
    
    # 추가 시간 정보 (Optional)
    updated_at = Column('UPDATED_AT', DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column('PROCESSED_AT', DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Document(document_id='{self.document_id}', name='{self.document_name}', status='{self.status}')>"
    
    # ============== 권한 관리 메서드들 ==============
    
    def has_permission(self, permission: str) -> bool:
        """특정 권한이 있는지 확인"""
        if not self.permissions:
            return False
        return permission in self.permissions
    
    def add_permission(self, permission: str) -> None:
        """권한 추가"""
        if not self.permissions:
            self.permissions = []
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: str) -> None:
        """권한 제거"""
        if self.permissions and permission in self.permissions:
            self.permissions.remove(permission)
    
    def set_permissions(self, permissions: list) -> None:
        """권한 목록 설정"""
        self.permissions = permissions if permissions else []
    
    def get_permissions(self) -> list:
        """권한 목록 반환"""
        return self.permissions if self.permissions else []
    
    def has_any_permission(self, permissions: list) -> bool:
        """주어진 권한 중 하나라도 있는지 확인"""
        if not self.permissions or not permissions:
            return False
        return any(perm in self.permissions for perm in permissions)
    
    def has_all_permissions(self, permissions: list) -> bool:
        """주어진 모든 권한이 있는지 확인"""
        if not self.permissions or not permissions:
            return False
        return all(perm in self.permissions for perm in permissions)
    
    # ============== 문서 타입 관리 메서드들 ==============
    
    def set_document_type(self, doc_type: str) -> bool:
        """문서 타입 설정"""
        if doc_type in self.VALID_DOCUMENT_TYPES:
            self.document_type = doc_type
            return True
        else:
            logger.warning(f"유효하지 않은 문서 타입: {doc_type}. 사용 가능한 타입: {self.VALID_DOCUMENT_TYPES}")
            return False
    
    def get_document_type(self) -> str:
        """문서 타입 반환"""
        return self.document_type if self.document_type else self.TYPE_COMMON
    
    def is_common_type(self) -> bool:
        """일반 타입인지 확인"""
        return self.get_document_type() == self.TYPE_COMMON
    
    def is_type1(self) -> bool:
        """타입1인지 확인"""
        return self.get_document_type() == self.TYPE_TYPE1
    
    def is_type2(self) -> bool:
        """타입2인지 확인"""
        return self.get_document_type() == self.TYPE_TYPE2
    
    @classmethod
    def get_valid_document_types(cls) -> list:
        """사용 가능한 문서 타입 목록 반환"""
        return cls.VALID_DOCUMENT_TYPES.copy()

# 기존 DocumentMetadata와의 호환성을 위한 별칭
DocumentMetadata = Document

class DocumentChunk(Base):
    """문서 청크 정보 테이블"""
    __tablename__ = "DOCUMENT_CHUNKS"
    
    # 기본 필드
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(String(255), unique=True, nullable=False)  # 고유한 청크 ID
    doc_id = Column(String(255), nullable=False)  # 참조하는 문서 ID (Document.document_id와 연결)
    
    # 청크 정보
    page_number = Column(Integer, nullable=False)
    chunk_type = Column(String(50), nullable=False)  # text, image, combined
    content = Column(Text)                           # 텍스트 내용
    image_description = Column(Text)                 # 이미지 설명
    image_path = Column(String(500))                 # 이미지 파일 경로
    
    # 벡터 정보
    milvus_id = Column(String(255))          # Milvus에서의 ID
    embedding_model = Column(String(100))    # 사용된 임베딩 모델
    vector_dimension = Column(Integer)       # 벡터 차원
    
    # 메타데이터
    char_count = Column(Integer)             # 텍스트 길이
    word_count = Column(Integer)             # 단어 수
    language = Column(String(10))            # 언어
    
    # 추가 정보
    metadata_json = Column(JSON)             # 기타 메타데이터
    
    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DocumentChunk(chunk_id='{self.chunk_id}', doc_id='{self.doc_id}', type='{self.chunk_type}')>"

class ProcessingJob(Base):
    """처리 작업 로그 테이블"""
    __tablename__ = "PROCESSING_JOBS"
    
    # 기본 필드
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(255), unique=True, nullable=False)  # Prefect 플로우 실행 ID
    doc_id = Column(String(255), nullable=False)  # 처리된 문서 ID (Document.document_id와 연결)
    
    # 작업 정보
    job_type = Column(String(50), nullable=False)    # process_document, reprocess, etc
    job_status = Column(String(50), default="running")  # running, completed, failed, cancelled
    
    # 처리 결과
    total_chunks = Column(Integer, default=0)
    successful_chunks = Column(Integer, default=0)
    failed_chunks = Column(Integer, default=0)
    
    # 로그 및 오류
    logs = Column(Text)                      # 처리 로그
    error_message = Column(Text)             # 오류 메시지
    
    # 처리 시간
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # 메타데이터
    prefect_flow_run_id = Column(String(255))  # Prefect 플로우 실행 ID
    worker_name = Column(String(255))          # 처리한 워커
    processing_config = Column(JSON)           # 처리 설정
    
    def __repr__(self):
        return f"<ProcessingJob(job_id='{self.job_id}', doc_id='{self.doc_id}', status='{self.job_status}')>"

class DatabaseManager:
    """데이터베이스 연결 및 세션 관리"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        
    def initialize(self):
        """데이터베이스 연결 초기화"""
        try:
            self.engine = create_engine(
                config.postgres_url,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=1800,
                echo=config.DATABASE_ECHO  # SQL 쿼리 로깅 설정
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self.engine
            )
            
            # 테이블 생성
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ PostgreSQL 데이터베이스 연결 및 테이블 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL 데이터베이스 초기화 실패: {str(e)}")
            raise
    
    def get_session(self):
        """데이터베이스 세션 생성"""
        if not self.SessionLocal:
            self.initialize()
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.get_session() as session:
                from sqlalchemy import text
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL 연결 테스트 실패: {str(e)}")
            return False

# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()

def get_db_session():
    """데이터베이스 세션 컨텍스트 매니저"""
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
