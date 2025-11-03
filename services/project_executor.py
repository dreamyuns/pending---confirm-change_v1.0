# project_executor.py - 예약확정처리 시스템 v2.0 프로젝트 실행기
import os
import json
import uuid
import time
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class AdminConfirmExecutor:
    """예약확정처리 프로젝트 실행 관리자 v2.0"""
    
    def __init__(self):
        self.running_process = None
        self.execution_history = []
        self.current_execution_id = None
        self.script_path = Path(__file__).parent.parent / "admin_confirm_rpa_v2.0.py"
        self.config_path = Path(__file__).parent.parent / "admin_confirm_config.json"
        self.temp_configs_dir = Path(__file__).parent.parent / "temp_configs"
        
        # temp_configs 디렉토리 생성
        self.temp_configs_dir.mkdir(exist_ok=True)
        
        print("예약확정처리 실행기 v2.0 초기화 완료")
        print(f"스크립트 경로: {self.script_path}")
        print(f"설정 파일 경로: {self.config_path}")
    
    def can_start_project(self) -> bool:
        """프로젝트 시작 가능 여부 확인"""
        # running_process가 있지만 stopped 상태인 경우는 새 프로젝트 시작 가능
        if self.running_process is not None:
            # stopped 상태가 아닌 경우에만 시작 불가
            if self.running_process.get("status") != "stopped":
                return False
            # stopped 상태인 경우 running_process 초기화하고 시작 가능
            self.running_process = None
        
        if not self.script_path.exists():
            print(f"스크립트 파일이 존재하지 않음: {self.script_path}")
            return False
            
        return True
    
    def start_project(self, config_data: Dict) -> str:
        """프로젝트 시작"""
        if not self.can_start_project():
            raise Exception("프로젝트 시작 불가: 이미 실행 중이거나 스크립트 파일이 없습니다")
        
        try:
            execution_id = str(uuid.uuid4())
            temp_config_path = self._create_runtime_config(config_data, execution_id)
            
            # 환경변수 설정
            env = os.environ.copy()
            env['CONFIG_FILE_PATH'] = str(temp_config_path)
            env['EXECUTION_MODE'] = 'web_interface'  # 웹 인터페이스에서 실행
            env['EXECUTION_ID'] = execution_id
            
            print(f"프로젝트 시작: 예약확정처리")
            print(f"실행 ID: {execution_id}")
            print(f"스크립트 경로: {self.script_path}")
            print(f"임시 설정 파일: {temp_config_path}")
            
            # 프로세스 시작
            process = subprocess.Popen(
                ["python", str(self.script_path)],
                stdout=None,  # 실시간 출력
                stderr=None,  # 실시간 출력
                text=True,
                cwd=str(self.script_path.parent),
                env=env
            )
            
            # 실행 정보 저장
            execution_info = {
                "execution_id": execution_id,
                "process": process,
                "start_time": datetime.now(),
                "status": "running",
                "config": config_data
            }
            
            self.running_process = execution_info
            self.current_execution_id = execution_id
            
            # 실행 이력에 추가
            self.execution_history.append({
                "execution_id": execution_id,
                "start_time": execution_info["start_time"],
                "status": "running",
                "config": config_data
            })
            
            # 모니터링 스레드 시작
            monitor_thread = threading.Thread(
                target=self._monitor_execution,
                args=(execution_id, process),
                daemon=False
            )
            monitor_thread.start()
            
            print(f"프로젝트 시작 완료: 예약확정처리 (실행 ID: {execution_id})")
            return execution_id
            
        except Exception as e:
            print(f"프로젝트 시작 실패: {e}")
            raise e
    
    def stop_project(self, force: bool = False) -> bool:
        """프로젝트 중지"""
        if self.running_process is None:
            return False
        
        try:
            process = self.running_process.get("process")
            execution_id = self.running_process.get("execution_id")  # 실행 ID 미리 저장
            start_time = self.running_process.get("start_time")
            
            if process:
                if force:
                    # 강제 종료
                    process.kill()
                    print("프로젝트 강제 중지: 예약확정처리")
                else:
                    # 정상 종료
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                        print("프로젝트 정상 중지: 예약확정처리")
                    except subprocess.TimeoutExpired:
                        process.kill()
                        print("프로젝트 강제 중지 (타임아웃): 예약확정처리")
            
            end_time = datetime.now()
            
            # 실행 이력 업데이트 (실행 ID를 미리 저장한 값 사용)
            for history_item in reversed(self.execution_history):
                if history_item["execution_id"] == execution_id and history_item["status"] == "running":
                    history_item["status"] = "stopped"
                    history_item["end_time"] = end_time
                    if start_time:
                        duration = end_time - start_time
                        history_item["duration"] = str(duration).split('.')[0]
                    break
            
            # 실행 중인 프로젝트 정보를 stopped 상태로 설정 (한 번만 반환하기 위해)
            stopped_info = {
                "execution_id": execution_id,
                "start_time": start_time,
                "end_time": end_time,
                "status": "stopped",
                "duration": str(end_time - start_time).split('.')[0] if start_time else "0:00:00",
                "_returned": False  # 한 번만 반환하기 위한 플래그
            }
            self.running_process = stopped_info
            self.current_execution_id = None
            
            return True
            
        except Exception as e:
            print(f"프로젝트 중지 실패: {e}")
            return False
    
    def get_status(self) -> Optional[Dict]:
        """프로젝트 상태 반환"""
        if self.running_process is None:
            return None
        
        info = self.running_process
        
        # stopped 상태인 경우 (stop_project에서 설정)
        if info.get("status") == "stopped" and "process" not in info:
            # 한 번만 반환하고 이후에는 None 반환 (새 프로젝트 시작 가능하도록)
            if not info.get("_returned", False):
                info["_returned"] = True
                return {
                    "execution_id": info["execution_id"],
                    "start_time": info["start_time"].isoformat() if isinstance(info["start_time"], datetime) else info["start_time"],
                    "end_time": info["end_time"].isoformat() if isinstance(info["end_time"], datetime) else info["end_time"],
                    "status": "stopped",
                    "duration": info.get("duration", "0:00:00")
                }
            else:
                # 이미 반환했으면 None으로 설정하여 새 프로젝트 시작 가능하도록
                self.running_process = None
                return None
        
        process = info.get("process")
        
        if process:
            return_code = process.poll()
            if return_code is not None:
                # 프로세스가 완료됨
                info["status"] = "completed" if return_code == 0 else "failed"
                info["end_time"] = datetime.now()
                info["return_code"] = return_code
                
                # 실행 시간 계산
                duration = info["end_time"] - info["start_time"]
                duration_str = str(duration).split('.')[0]
                
                # 실행 이력 업데이트
                for history_item in reversed(self.execution_history):
                    if history_item["execution_id"] == info["execution_id"]:
                        history_item["status"] = info["status"]
                        history_item["end_time"] = info["end_time"]
                        history_item["return_code"] = return_code
                        history_item["duration"] = duration_str
                        break
                
                # 실행 중인 프로젝트에서 제거
                self.running_process = None
                self.current_execution_id = None
                
                # 임시 설정 파일 정리
                self._cleanup_temp_config(info["execution_id"])
                
                return {
                    "execution_id": info["execution_id"],
                    "start_time": info["start_time"].isoformat(),
                    "end_time": info["end_time"].isoformat(),
                    "status": info["status"],
                    "duration": duration_str,
                    "return_code": return_code
                }
            else:
                # 프로세스가 아직 실행 중
                return {
                    "execution_id": info["execution_id"],
                    "start_time": info["start_time"].isoformat(),
                    "status": "running",
                    "duration": str(datetime.now() - info["start_time"]).split('.')[0]
                }
        
        return None
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """실행 이력 반환"""
        return self.execution_history[-limit:]
    
    def _monitor_execution(self, execution_id: str, process: subprocess.Popen):
        """실행 상태 모니터링"""
        try:
            print(f"모니터링 시작: {execution_id}")
            
            # 프로세스 완료까지 대기
            while True:
                return_code = process.poll()
                if return_code is not None:
                    print(f"프로세스 완료 감지: {execution_id}, 반환 코드: {return_code}")
                    break
                
                time.sleep(1)  # 1초마다 확인
            
            # 프로세스 완료 시 상태 업데이트
            self._update_project_status_from_monitor(execution_id, return_code)
            
        except Exception as e:
            print(f"모니터링 오류 ({execution_id}): {e}")
            self._update_project_status_from_monitor(execution_id, -1)
    
    def _update_project_status_from_monitor(self, execution_id: str, return_code: int):
        """모니터링에서 프로젝트 상태 업데이트"""
        try:
            if self.running_process and self.running_process["execution_id"] == execution_id:
                print(f"모니터링에서 프로젝트 상태 업데이트: {execution_id}")
                
                # 실행 정보 업데이트
                self.running_process["status"] = "completed" if return_code == 0 else "failed"
                self.running_process["end_time"] = datetime.now()
                self.running_process["return_code"] = return_code
                
                # 실행 시간 계산
                duration = self.running_process["end_time"] - self.running_process["start_time"]
                duration_str = str(duration).split('.')[0]
                
                # 실행 이력 업데이트
                for history_item in reversed(self.execution_history):
                    if history_item["execution_id"] == execution_id:
                        history_item["status"] = self.running_process["status"]
                        history_item["end_time"] = self.running_process["end_time"]
                        history_item["return_code"] = return_code
                        history_item["duration"] = duration_str
                        break
                
                # 실행 중인 프로젝트에서 제거
                self.running_process = None
                self.current_execution_id = None
                
                # 임시 설정 파일 정리
                self._cleanup_temp_config(execution_id)
                
                print(f"모니터링 완료: 예약확정처리 -> {self.running_process['status'] if self.running_process else 'completed'}")
                
        except Exception as e:
            print(f"상태 업데이트 실패 ({execution_id}): {e}")
    
    def _create_runtime_config(self, config_data: Dict, execution_id: str) -> str:
        """런타임 설정 파일 생성"""
        try:
            # 기본 설정 파일 로드
            with open(self.config_path, 'r', encoding='utf-8') as f:
                base_config = json.load(f)
            
            # 프론트엔드 설정과 병합
            merged_config = self._merge_configs(base_config, config_data)
            
            # 임시 설정 파일 생성
            temp_config_path = self.temp_configs_dir / f"admin_confirm_{execution_id}.json"
            
            with open(temp_config_path, 'w', encoding='utf-8') as f:
                json.dump(merged_config, f, ensure_ascii=False, indent=2)
            
            print(f"런타임 설정 파일 생성: {temp_config_path}")
            return str(temp_config_path)
            
        except Exception as e:
            print(f"런타임 설정 파일 생성 실패: {e}")
            raise e
    
    def _merge_configs(self, base_config: Dict, frontend_config: Dict) -> Dict:
        """설정 병합"""
        merged = base_config.copy()
        
        # 프론트엔드 설정을 기본 설정에 병합
        for key, value in frontend_config.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key].update(value)
            else:
                merged[key] = value
        
        return merged
    
    def _cleanup_temp_config(self, execution_id: str):
        """임시 설정 파일 정리"""
        try:
            for config_file in self.temp_configs_dir.glob(f"admin_confirm_{execution_id}.json"):
                config_file.unlink()
                print(f"임시 설정 파일 삭제: {config_file}")
        except Exception as e:
            print(f"임시 설정 파일 정리 실패: {e}")

# 전역 인스턴스
admin_confirm_executor = AdminConfirmExecutor()

def get_project_executor() -> AdminConfirmExecutor:
    """프로젝트 실행기 인스턴스 반환"""
    return admin_confirm_executor
