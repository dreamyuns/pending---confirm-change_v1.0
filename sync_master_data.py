# sync_master_data.py - 공통 데이터 동기화 스크립트
import shutil
from pathlib import Path
import os

def sync_master_data():
    """모든 프로젝트에 master_data.xlsx 동기화"""
    
    # 소스 파일 경로
    source_file = Path("C:/Users/윤성균/Documents/python_study/통합관리시스템_v2.0/data/master_data.xlsx")
    
    # 대상 프로젝트 목록
    projects = [
        "admin_예약확정처리_v2.0",
        "취소일괄처리_v2.0", 
        "CX클레임처리_v2.0",
        "admin_예약상태변경_v2.0",
        "admin_b2b채널타입변경_v2.0"
    ]
    
    print("🔄 공통 데이터 동기화 시작...")
    print(f"📁 소스 파일: {source_file}")
    print("=" * 50)
    
    success_count = 0
    error_count = 0
    
    for project in projects:
        try:
            # 대상 경로 설정
            dest_path = Path(f"C:/Users/윤성균/Documents/python_study/{project}/data/master_data.xlsx")
            
            # 대상 디렉토리가 없으면 생성
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 파일 복사
            shutil.copy2(source_file, dest_path)
            print(f"✅ 복사 완료: {project}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 복사 실패: {project} - {e}")
            error_count += 1
    
    print("=" * 50)
    print(f"📊 동기화 완료: 성공 {success_count}개, 실패 {error_count}개")
    
    if error_count == 0:
        print("🎉 모든 프로젝트에 공통 데이터가 성공적으로 동기화되었습니다!")
    else:
        print("⚠️ 일부 프로젝트 동기화에 실패했습니다. 오류를 확인해주세요.")

if __name__ == "__main__":
    sync_master_data()
