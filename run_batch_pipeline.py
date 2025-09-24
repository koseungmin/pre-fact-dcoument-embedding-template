#!/usr/bin/env python3
"""
배치 문서 처리 파이프라인 실행 스크립트
"""

import sys
from pathlib import Path

# flow 모듈을 import path에 추가
sys.path.append(str(Path(__file__).parent / "flow"))

from batch_document_processing_pipeline import batch_document_processing_pipeline

def main():
    """배치 파이프라인 실행"""
    
    # 처리할 폴더 경로 (현재 프로젝트 폴더)
    folder_path = "/Users/a09156/Desktop/workforce/prefect_test"
    
    print("📁 배치 문서 처리 파이프라인")
    print(f"   폴더: {folder_path}")
    print(f"   최대 페이지: 5페이지")
    print(f"   최대 파일 크기: 50MB")
    print("=" * 50)
    
    try:
        # 배치 처리 실행
        result = batch_document_processing_pipeline(
            folder_path=folder_path,
            max_pages=5,
            max_file_size_mb=50.0,
            skip_existing=True
        )
        
        # 결과 출력
        print("\n📊 최종 결과:")
        print(f"   - 상태: {result['status']}")
        print(f"   - 발견된 파일: {result['total_files_found']}개")
        print(f"   - 처리 대상: {result['total_files_processed']}개")
        print(f"   - 성공: {result['successful_files']}개")
        print(f"   - 실패: {result['failed_files']}개")
        print(f"   - 건너뜀: {result['skipped_files']}개")
        print(f"   - 총 시간: {result['total_duration_seconds']:.1f}초")
        
        if 'detailed_stats' in result:
            stats = result['detailed_stats']
            print(f"\n📈 상세 통계:")
            print(f"   - 처리된 페이지: {stats['total_pages_processed']}페이지")
            print(f"   - 생성된 벡터: {stats['total_vectors_created']}개")
            print(f"   - 저장된 청크: {stats['total_chunks_saved']}개")
        
        return 0
        
    except Exception as e:
        print(f"❌ 배치 처리 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
