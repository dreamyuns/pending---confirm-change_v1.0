# main.py - 예약확정처리 시스템 v2.0 메인 서버
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
from pathlib import Path
from datetime import datetime

# FastAPI 앱 생성
app = FastAPI(
    title="예약확정처리 시스템 v2.0",
    description="예약확정처리 자동화 시스템 - 프론트엔드 연동 버전",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 업로드 디렉토리 설정
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 설정 파일 경로
CONFIG_PATH = Path(__file__).parent / "admin_confirm_config.json"

# 정적 파일 서빙 (HTML, CSS, JavaScript 파일들)
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# 메인 페이지 라우트
@app.get("/")
async def read_root():
    """메인 페이지 반환"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        return {"message": "프론트엔드 파일이 없습니다. frontend/index.html을 생성해주세요."}

# 서버 상태 확인 API
@app.get("/api/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "message": "예약확정처리 시스템 v2.0이 정상 작동 중입니다.",
        "version": "2.0.0",
        "project": "admin_confirm"
    }

# 설정 로드 API
@app.get("/api/config")
async def get_config():
    """프로젝트 설정 로드"""
    try:
        config_path = Path(__file__).parent / "admin_confirm_config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return {"success": True, "config": config}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 설정 저장 API
@app.post("/api/config")
async def save_config(config_data: dict):
    """프로젝트 설정 저장"""
    try:
        config_path = Path(__file__).parent / "admin_confirm_config.json"
        
        # 기존 설정 로드
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
        except:
            existing_config = {}
        
        # 중첩된 딕셔너리 병합 함수
        def deep_merge(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_merge(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        # 새 설정과 기존 설정 병합
        deep_merge(existing_config, config_data)
        
        # 참고: search_status(변경 전 상태)와 change_to_status(변경할 상태)는 별개입니다.
        # 동기화하지 않습니다.
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(existing_config, f, ensure_ascii=False, indent=2)
        return {"success": True, "message": "설정이 저장되었습니다"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 프로젝트 시작 API
@app.post("/api/start")
async def start_project(config_data: dict):
    """프로젝트 시작"""
    try:
        # 하위 호환성: change_status를 search_status로 변환 (search_settings 내에서만)
        if 'search_settings' in config_data and 'change_status' in config_data['search_settings']:
            if 'search_status' not in config_data['search_settings']:
                config_data['search_settings']['search_status'] = config_data['search_settings']['change_status']
        
        # 참고: search_status(변경 전 상태)와 change_to_status(변경할 상태)는 별개입니다.
        # search_status는 검색 필터용, change_to_status는 상태 변경용입니다.
        # 동기화하지 않습니다.
        
        from services.project_executor import get_project_executor
        executor = get_project_executor()
        
        execution_id = executor.start_project(config_data)
        return {
            "success": True, 
            "execution_id": execution_id,
            "message": "예약확정처리 프로젝트가 시작되었습니다"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# 프로젝트 중단 API
@app.post("/api/stop")
async def stop_project(force: bool = False):
    """프로젝트 중단"""
    try:
        from services.project_executor import get_project_executor
        executor = get_project_executor()
        
        success = executor.stop_project(force)
        if success:
            return {
                "success": True,
                "message": "프로젝트가 중단되었습니다"
            }
        else:
            return {
                "success": False,
                "error": "프로젝트를 중단할 수 없습니다"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

# 프로젝트 상태 확인 API
@app.get("/api/status")
async def get_status():
    """프로젝트 상태 확인"""
    try:
        from services.project_executor import get_project_executor
        executor = get_project_executor()
        
        status = executor.get_status()
        return {"success": True, "status": status}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 실행 이력 조회 API
@app.get("/api/history")
async def get_history(limit: int = 10):
    """실행 이력 조회"""
    try:
        from services.project_executor import get_project_executor
        executor = get_project_executor()
        
        history = executor.get_history(limit)
        return {"success": True, "history": history}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ===== 공통 데이터 API =====

# 채널 데이터 API
@app.get("/api/channels")
async def get_channels():
    """채널 데이터 반환"""
    try:
        from services.excel_manager import get_excel_manager
        excel_manager = get_excel_manager()
        channels = excel_manager.get_channels()
        return {"success": True, "channels": channels}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 채널 검색 API
@app.get("/api/channels/search")
async def search_channels(q: str = ""):
    """채널 검색"""
    try:
        from services.excel_manager import get_excel_manager
        excel_manager = get_excel_manager()
        channels = excel_manager.search_channels(q)
        return {"success": True, "channels": channels}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 주문 상태 데이터 API
@app.get("/api/order-statuses")
async def get_order_statuses():
    """주문 상태 데이터 반환"""
    try:
        from services.excel_manager import get_excel_manager
        excel_manager = get_excel_manager()
        statuses = excel_manager.get_order_statuses()
        return {"success": True, "statuses": statuses}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 변경할 상태 데이터 API
@app.get("/api/change-statuses")
async def get_change_statuses():
    """변경할 상태 데이터 반환"""
    try:
        from services.excel_manager import get_excel_manager
        excel_manager = get_excel_manager()
        change_statuses = excel_manager.get_change_statuses()
        return {"success": True, "change_statuses": change_statuses}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 검색 조건용 상태 데이터 API (변경 전 상태)
@app.get("/api/search-statuses")
async def get_search_statuses():
    """검색 조건용 상태 데이터 반환 (변경 전 상태)"""
    try:
        from services.excel_manager import get_excel_manager
        excel_manager = get_excel_manager()
        search_statuses = excel_manager.get_search_statuses()
        return {"success": True, "search_statuses": search_statuses}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 판매 유형 데이터 API
@app.get("/api/sale-types")
async def get_sale_types():
    """판매 유형 데이터 반환"""
    try:
        from services.excel_manager import get_excel_manager
        excel_manager = get_excel_manager()
        sale_types = excel_manager.get_sale_types()
        return {"success": True, "sale_types": sale_types}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 날짜 유형 데이터 API
@app.get("/api/date-types")
async def get_date_types():
    """날짜 유형 데이터 반환"""
    try:
        from services.excel_manager import get_excel_manager
        excel_manager = get_excel_manager()
        date_types = excel_manager.get_date_types()
        return {"success": True, "date_types": date_types}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 예약일 유형 데이터 API
@app.get("/api/appoint-day-types")
async def get_appoint_day_types():
    """예약일 유형 데이터 반환"""
    try:
        from services.excel_manager import get_excel_manager
        excel_manager = get_excel_manager()
        appoint_types = excel_manager.get_appoint_day_types()
        return {"success": True, "appoint_types": appoint_types}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 검색 유형 데이터 API
@app.get("/api/search-types")
async def get_search_types():
    """검색어 입력 유형 데이터 반환"""
    try:
        from services.excel_manager import get_excel_manager
        excel_manager = get_excel_manager()
        search_types = excel_manager.get_search_types()
        return {"success": True, "search_types": search_types}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 모든 데이터 API
@app.get("/api/excel-data")
async def get_excel_data():
    """모든 Excel 데이터 반환"""
    try:
        from services.excel_manager import get_excel_manager
        excel_manager = get_excel_manager()
        data = excel_manager.get_all_data()
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ===== 파일 업로드/다운로드 API =====

# Excel 파일 업로드 API
@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    """Excel 파일 업로드"""
    try:
        # 파일 확장자 검증
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            return {
                "success": False, 
                "error": f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(allowed_extensions)}"
            }
        
        # 파일 크기 검증 (10MB)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            return {
                "success": False,
                "error": "파일 크기가 10MB를 초과합니다."
            }
        
        # 파일명 생성 (중복 방지)
        original_filename = Path(file.filename).stem
        file_extension = Path(file.filename).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{original_filename}_{timestamp}{file_extension}"
        
        # 파일 저장
        file_path = UPLOAD_DIR / new_filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 설정 파일 업데이트
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            config = {}
        
        # 파일 경로 업데이트 (상대 경로로 저장)
        if 'file_paths' not in config:
            config['file_paths'] = {}
        # 상대 경로로 저장 (프로젝트 폴더 기준)
        relative_path = f"uploads/{new_filename}"
        config['file_paths']['excel_file'] = relative_path
        
        # 설정 파일 저장
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        file_stat = file_path.stat()
        return {
            "success": True,
            "filename": new_filename,
            "file_size": file_stat.st_size,
            "upload_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "path": relative_path
        }
        
    except Exception as e:
        return {"success": False, "error": f"파일 업로드 실패: {str(e)}"}

# 업로드된 파일 정보 조회 API
@app.get("/api/uploaded-files")
async def get_uploaded_files():
    """업로드된 파일 정보 조회"""
    try:
        files_info = []
        
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                excel_file_path = config.get('file_paths', {}).get('excel_file', '')
                if excel_file_path:
                    # 상대 경로인 경우 절대 경로로 변환
                    if not Path(excel_file_path).is_absolute():
                        excel_file_path = Path(__file__).parent / excel_file_path
                    else:
                        excel_file_path = Path(excel_file_path)
                    
                    if excel_file_path.exists():
                        file_stat = excel_file_path.stat()
                        files_info.append({
                            "type": "excel",
                            "filename": excel_file_path.name,
                            "file_size": file_stat.st_size,
                            "upload_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            "path": str(excel_file_path)
                        })
        except:
            pass
        
        return {"success": True, "files": files_info}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# 서버 실행
if __name__ == "__main__":
    print("🚀 예약확정처리 시스템 v2.0 서버 시작")
    print("📱 브라우저에서 http://localhost:8001 접속하세요")
    print("🔧 API 문서: http://localhost:8001/docs")
    print("=" * 50)
    
    # 포트 설정 (환경변수 우선, 기본값 8001)
    port = int(os.getenv('PORT', 8001))
    host = os.getenv('HOST', '0.0.0.0')
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False
    )
