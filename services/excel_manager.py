# excel_manager.py - Excel 데이터 관리 모듈
import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Optional

class ExcelDataManager:
    """Excel 데이터를 관리하는 클래스"""
    
    def __init__(self, excel_file_path: str):
        """
        Excel 데이터 매니저 초기화
        
        Args:
            excel_file_path: master_data.xlsx 파일 경로
        """
        self.excel_file_path = excel_file_path
        self._data_cache = {}
        self._last_modified = None
        
    def _check_file_exists(self) -> bool:
        """Excel 파일 존재 여부 확인"""
        return os.path.exists(self.excel_file_path)
    
    def _is_file_modified(self) -> bool:
        """파일이 수정되었는지 확인"""
        if not self._check_file_exists():
            return False
        
        current_modified = os.path.getmtime(self.excel_file_path)
        if self._last_modified != current_modified:
            self._last_modified = current_modified
            return True
        return False
    
    def _load_excel_data(self) -> Dict[str, pd.DataFrame]:
        """Excel 파일에서 모든 시트 데이터 로드"""
        if not self._check_file_exists():
            raise FileNotFoundError(f"Excel 파일을 찾을 수 없습니다: {self.excel_file_path}")
        
        try:
            # 모든 시트 읽기
            excel_data = pd.read_excel(self.excel_file_path, sheet_name=None)
            return excel_data
        except Exception as e:
            raise Exception(f"Excel 파일 읽기 실패: {e}")
    
    def _update_cache(self):
        """캐시 업데이트"""
        if self._is_file_modified() or not self._data_cache:
            self._data_cache = self._load_excel_data()
    
    def get_channels(self) -> List[Dict[str, str]]:
        """채널 데이터 반환"""
        self._update_cache()
        
        if 'channels' not in self._data_cache:
            return []
        
        channels_df = self._data_cache['channels']
        channels = []
        
        for _, row in channels_df.iterrows():
            channels.append({
                'id': str(row['ID']) if pd.notna(row['ID']) else '',
                'name': str(row['channels']) if pd.notna(row['channels']) else '',
                'display': f"{row['ID']}_{row['channels']}" if pd.notna(row['ID']) and pd.notna(row['channels']) else ''
            })
        
        return channels
    
    def get_order_statuses(self) -> List[Dict[str, str]]:
        """주문 상태 데이터 반환"""
        self._update_cache()
        
        if 'order_status' not in self._data_cache:
            return []
        
        status_df = self._data_cache['order_status']
        statuses = []
        
        for _, row in status_df.iterrows():
            statuses.append({
                'code': str(row['status_en']) if pd.notna(row['status_en']) else '',
                'name': str(row['status_kr']) if pd.notna(row['status_kr']) else '',
                'display': f"{row['status_en']}({row['status_kr']})" if pd.notna(row['status_en']) and pd.notna(row['status_kr']) else ''
            })
        
        return statuses
    
    def get_change_statuses(self) -> List[Dict[str, str]]:
        """변경할 상태 데이터 반환 (주문 상태와 동일)"""
        return self.get_order_statuses()
    
    def get_search_statuses(self) -> List[Dict[str, str]]:
        """검색 조건용 상태 데이터 반환 (변경 전 상태, 주문 상태와 동일)"""
        return self.get_order_statuses()
    
    def get_sale_types(self) -> List[Dict[str, str]]:
        """판매 유형 데이터 반환"""
        self._update_cache()
        
        if 'sale_type' not in self._data_cache:
            return []
        
        sale_df = self._data_cache['sale_type']
        sale_types = []
        
        for _, row in sale_df.iterrows():
            sale_types.append({
                'code': str(row['sale_type_en']) if pd.notna(row['sale_type_en']) else '',
                'name': str(row['sale_type_kr']) if pd.notna(row['sale_type_kr']) else '',
                'display': str(row['sale_type_kr']) if pd.notna(row['sale_type_kr']) else ''
            })
        
        return sale_types
    
    def get_date_types(self) -> List[Dict[str, str]]:
        """날짜 유형 데이터 반환"""
        self._update_cache()
        
        if 'date_types' not in self._data_cache:
            return []
        
        date_df = self._data_cache['date_types']
        date_types = []
        
        for _, row in date_df.iterrows():
            date_types.append({
                'code': str(row['date_types_en']) if pd.notna(row['date_types_en']) else '',
                'name': str(row['date_types_kr']) if pd.notna(row['date_types_kr']) else '',
                'display': f"{row['date_types_en']}({row['date_types_kr']})" if pd.notna(row['date_types_en']) and pd.notna(row['date_types_kr']) else ''
            })
        
        return date_types
    
    def get_appoint_day_types(self) -> List[Dict[str, str]]:
        """예약일 유형 데이터 반환"""
        self._update_cache()
        
        if 'appoint_day' not in self._data_cache:
            return []
        
        appoint_df = self._data_cache['appoint_day']
        appoint_types = []
        
        for _, row in appoint_df.iterrows():
            appoint_types.append({
                'code': str(row['appoint_day_en']) if pd.notna(row['appoint_day_en']) else '',
                'name': str(row['appoint_day_kr']) if pd.notna(row['appoint_day_kr']) else '',
                'display': f"{row['appoint_day_en']}({row['appoint_day_kr']})" if pd.notna(row['appoint_day_en']) and pd.notna(row['appoint_day_kr']) else ''
            })
        
        return appoint_types
    
    def get_search_types(self) -> List[Dict[str, str]]:
        """검색어 입력 유형 데이터 반환"""
        self._update_cache()
        
        if 'search_type' not in self._data_cache:
            return []
        
        search_df = self._data_cache['search_type']
        search_types = []
        
        for _, row in search_df.iterrows():
            search_types.append({
                'code': str(row['searchtype_en']) if pd.notna(row['searchtype_en']) else '',
                'name': str(row['searchtype_kr']) if pd.notna(row['searchtype_kr']) else '',
                'display': str(row['searchtype_kr']) if pd.notna(row['searchtype_kr']) else ''
            })
        
        return search_types
    
    def get_all_data(self) -> Dict[str, List[Dict[str, str]]]:
        """모든 데이터 반환"""
        return {
            'channels': self.get_channels(),
            'order_statuses': self.get_order_statuses(),
            'change_statuses': self.get_change_statuses(),  # 변경할 상태 추가
            'search_statuses': self.get_search_statuses(),  # 검색 조건용 상태 추가
            'sale_types': self.get_sale_types(),
            'date_types': self.get_date_types(),
            'appoint_day_types': self.get_appoint_day_types(),
            'search_types': self.get_search_types()
        }
    
    def search_channels(self, query: str) -> List[Dict[str, str]]:
        """채널 검색"""
        channels = self.get_channels()
        if not query:
            return channels[:20]  # 처음 20개만 반환
        
        query_lower = query.lower()
        filtered_channels = [
            channel for channel in channels
            if query_lower in channel['name'].lower() or query_lower in channel['id'].lower()
        ]
        
        return filtered_channels[:20]  # 최대 20개 반환

# 전역 인스턴스
excel_manager = None

def get_excel_manager() -> ExcelDataManager:
    """Excel 매니저 인스턴스 반환"""
    global excel_manager
    if excel_manager is None:
        # 현재 스크립트가 있는 디렉토리 기준으로 Excel 파일 경로 설정
        # services/excel_manager.py -> admin_예약확정처리_v2.0 -> data
        current_dir = Path(__file__).parent.parent
        excel_file_path = current_dir / "data" / "master_data.xlsx"
        excel_manager = ExcelDataManager(str(excel_file_path))
    return excel_manager
