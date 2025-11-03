# admin_confirm_rpa_v2.0.py - 예약확정처리 시스템 v2.0 RPA 스크립트
# 웹 인터페이스 연동 버전 - 기존 v1.7 로직 유지 + 웹 연동 기능 추가

import os
import time
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ✅ 1. [설정 파일 로드] - 웹 인터페이스 연동 지원
# 환경변수에서 설정 파일 경로 확인 (웹 인터페이스에서 전달)
config_file = os.environ.get('CONFIG_FILE_PATH')
execution_mode = os.environ.get('EXECUTION_MODE', 'standalone')
execution_id = os.environ.get('EXECUTION_ID', 'unknown')

if not config_file:
    # 환경변수가 없으면 기본 설정 파일 사용
    config_file = os.path.join(os.path.dirname(__file__), 'admin_confirm_config.json')

print(f"=== 예약확정처리 시스템 v2.0 시작 ===")
print(f"실행 모드: {execution_mode}")
print(f"실행 ID: {execution_id}")
print(f"설정 파일 경로: {config_file}")

try:
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"설정 파일 로드 완료: {config_file}")
except FileNotFoundError:
    print(f"오류: {config_file} 파일을 찾을 수 없습니다.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"오류: {config_file} 파일 형식이 잘못되었습니다. {e}")
    exit(1)

# ✅ URL 설정 자동 동기화: login.url을 기반으로 base_url 설정
if 'login' in config and 'url' in config['login']:
    login_url = config['login']['url']
    # base_url이 없거나 개발서버 URL인 경우 login.url을 기반으로 설정
    if 'urls' not in config:
        config['urls'] = {}
    
    if 'base_url' not in config['urls'] or 'dev.allmytour.com' in config['urls'].get('base_url', ''):
        # login.url에서 기본 URL 추출 (포트 번호 제거)
        from urllib.parse import urlparse
        parsed = urlparse(login_url)
        # 포트가 있는 경우와 없는 경우 모두 처리
        if parsed.port:
            base_url = f"{parsed.scheme}://{parsed.netloc.split(':')[0]}"
        else:
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        config['urls']['base_url'] = base_url
        print(f"✅ base_url 자동 설정: {base_url} (login.url 기반)")

# ✅ 2. [초기화] 상대 경로를 절대 경로로 변환하는 함수
def resolve_path(path_str):
    """상대 경로를 절대 경로로 변환 (프로젝트 폴더 기준)"""
    if not path_str:
        return None
    
    # 이미 절대 경로인 경우 그대로 반환
    if os.path.isabs(path_str):
        return path_str
    
    # 상대 경로인 경우 프로젝트 루트 기준으로 변환
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = Path(script_dir)
    path = Path(path_str)
    
    return str(project_root / path)

# ✅ 로그 및 결과 디렉토리 생성 (상대 경로 지원)
today = datetime.now().strftime('%Y%m%d')
log_dir = resolve_path(config['file_paths']['log_directory']) or os.path.join(os.path.dirname(__file__), 'logs')
result_dir = resolve_path(config['file_paths']['result_directory']) or os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(log_dir, exist_ok=True)
os.makedirs(result_dir, exist_ok=True)

# 🔥 상태 매핑 테이블 동적 로드 (master_data.xlsx에서 읽어오기)
def load_status_mapping():
    """master_data.xlsx의 order_status 시트에서 상태 매핑 로드"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        master_data_path = Path(script_dir) / "data" / "master_data.xlsx"
        
        if not master_data_path.exists():
            print(f"⚠️ 경고: master_data.xlsx 파일을 찾을 수 없습니다: {master_data_path}")
            print("기본 상태 매핑을 사용합니다.")
            return get_default_status_mapping()
        
        # Excel 파일에서 order_status 시트 읽기
        df = pd.read_excel(master_data_path, sheet_name='order_status')
        
        status_mapping = {}
        
        # 영문 → 한글 매핑
        for _, row in df.iterrows():
            status_en = str(row['status_en']).strip() if pd.notna(row['status_en']) else ''
            status_kr = str(row['status_kr']).strip() if pd.notna(row['status_kr']) else ''
            
            if status_en and status_kr:
                status_mapping[status_en] = status_kr  # 영문 → 한글
                status_mapping[status_kr] = status_en  # 한글 → 영문 (역매핑)
        
        print(f"✅ 상태 매핑 로드 완료: {len(status_mapping) // 2}개 상태")
        return status_mapping
        
    except Exception as e:
        print(f"⚠️ 경고: 상태 매핑 로드 실패: {e}")
        print("기본 상태 매핑을 사용합니다.")
        return get_default_status_mapping()

def get_default_status_mapping():
    """기본 상태 매핑 (fallback)"""
    return {
        # 영문 → 한글
        "addpay": "추가결제대기중",
        "cancel": "취소",
        "cancelWait": "취소 확인필요",
        "cancelWip": "취소처리중",
        "cancelRequest": "취소요청",
        "complete": "완료",
        "confirm": "확정",
        "confirmWait": "확정 확인필요",
        "confirmWip": "확정처리중",
        "noshow": "노쇼",
        "fail": "결제실패",
        "pending": "대기",
        # 한글 → 영문 (역매핑)
        "추가결제대기중": "addpay",
        "취소": "cancel",
        "취소 확인필요": "cancelWait",
        "취소처리중": "cancelWip",
        "취소요청": "cancelRequest",
        "완료": "complete",
        "확정": "confirm",
        "확정 확인필요": "confirmWait",
        "확정처리중": "confirmWip",
        "노쇼": "noshow",
        "결제실패": "fail",
        "대기": "pending"
    }

STATUS_MAPPING = load_status_mapping()

# 전역 변수
main_window = None
log_file = None
result_file = None

# 프로젝트별 독립적인 Lock 파일 (동시 실행 방지)
try:
    script_dir = os.path.dirname(__file__)
except NameError:
    script_dir = os.getcwd()
lock_file = os.path.join(script_dir, 'admin_confirm_v2.0.lock')

# ✅ Lock 파일 관리 (동시 실행 방지)
def check_lock_file():
    """Lock 파일 확인 (동시 실행 방지)"""
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                lock_time = f.read().strip()
            print(f"⚠️ 다른 프로세스가 실행 중입니다. Lock 시간: {lock_time}")
            return False
        except:
            # Lock 파일이 손상된 경우 삭제
            os.remove(lock_file)
            return True
    return True

def create_lock_file():
    """Lock 파일 생성"""
    try:
        with open(lock_file, 'w') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (v2.0)")
        return True
    except:
        return False

def remove_lock_file():
    """Lock 파일 제거"""
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
    except:
        pass

# ✅ 자동 인덱스 파일명 생성 함수
def generate_log_filename(base_dir, prefix, today):
    index = 1
    while True:
        file_name = f"{prefix}_{index:03}_{today}.txt"
        full_path = os.path.join(base_dir, file_name)
        if not os.path.exists(full_path):
            return full_path
        index += 1

# ✅ 로그 및 결과 파일명 자동 생성
log_file = generate_log_filename(log_dir, "로그_v2.0", today)
result_file = generate_log_filename(result_dir, "전송여부결과_v2.0", today)

# ✅ 안전한 타이밍 접근자 (config에 키가 없어도 동작)
def get_timing(name, default_seconds):
    try:
        return float(config.get('timing', {}).get(name, default_seconds))
    except Exception:
        return float(default_seconds)

def get_timing_adv(name, default_seconds):
    """고급 타이밍 설정 (timing에서 가져오고, 없으면 timing_advanced 확인)"""
    try:
        # 먼저 timing에서 찾기
        if 'timing' in config and name in config['timing']:
            return float(config['timing'][name])
        # 없으면 timing_advanced 확인
        return float(config.get('timing_advanced', {}).get(name, default_seconds))
    except Exception:
        return float(default_seconds)

# ✅ 로그 파일에 기록 (디버깅, 오류, 처리 과정)
def log_debug(message, order_number=None):
    """로그 메시지 기록 (주문번호 포함 가능)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if order_number:
        log_content = f"[{timestamp}] [주문번호: {order_number}] {message}"
    else:
        log_content = f"[{timestamp}] {message}"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_content + '\n')
    print(message)  # 콘솔에도 출력

# ✅ 결과 파일에 기록 (최종 처리 결과)
def log_result(order_number, confirm_number, status_result, lms_result, timestamp):
    result_content = f"{order_number}\t{confirm_number}\t{status_result}\t{lms_result}\t{timestamp}"
    with open(result_file, 'a', encoding='utf-8') as f:
        f.write(result_content + '\n')
    log_debug(f"결과 기록: {result_content}")

# ✅ 실행 시작 로그
def log_start():
    log_debug("=" * 60)
    log_debug(f"실행 파일: admin_confirm_rpa_v2.0.py")
    log_debug(f"실행 모드: {execution_mode}")
    log_debug(f"실행 ID: {execution_id}")
    log_debug(f"실행 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_debug(f"로그 파일: {log_file}")
    log_debug(f"결과 파일: {result_file}")
    log_debug("=" * 60)

# ✅ 3. [드라이버 실행 및 로그인]
try:
    print("ChromeDriver 자동 다운로드 및 설정 중...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    print("ChromeDriver 설정 완료!")
except Exception as e:
    print(f"ChromeDriver 설정 실패: {e}")
    exit(1)

driver.maximize_window()
driver.set_window_position(0, 0)
driver.set_window_size(1920, 1080)

# 3-1. 로그인
try:
    driver.get(config['login']['url'])
    time.sleep(2)
    driver.find_element(By.NAME, "userId").send_keys(config['login']['user_id'])
    driver.find_element(By.NAME, "userPasswd").send_keys(config['login']['password'])
    driver.find_element(By.XPATH, "//input[@type='submit']").click()
    time.sleep(2)
    print("로그인 완료!")
except Exception as e:
    print(f"로그인 실패: {e}")
    driver.quit()
    exit(1)

# ✅ 4. [1단계: 엑셀 파일 업로드]
def upload_excel_file():
    try:
        print("1단계: 엑셀 파일 업로드 시작...")
        
        # 1. 로그인 완료 후 예약목록 페이지 이동
        orders_url = config['urls']['base_url'] + config['urls']['orders_page']
        print(f"1-1. 예약목록 페이지 이동: {orders_url}")
        driver.get(orders_url)
        time.sleep(get_timing('page_load_wait', 2))
        print(f"1-1-1. 현재 페이지 URL: {driver.current_url}")
        print(f"1-1-2. 페이지 제목: {driver.title}")
        
        # 예약목록 페이지 안정화 대기
        print("1-1-3. 예약목록 페이지 안정화 대기 (2초)...")
        time.sleep(2)
        
        # 2. 새창을 열고 업로드 페이지 접속
        upload_url = config['urls']['base_url'] + config['urls']['upload_page']
        print(f"1-2. 새창에서 업로드 페이지 접속: {upload_url}")
        driver.execute_script(f"window.open('{upload_url}', '_blank');")
        time.sleep(1)  # 새창 열기 시간 단축
        
        # 새창으로 전환
        windows = driver.window_handles
        if len(windows) > 1:
            driver.switch_to.window(windows[-1])
            time.sleep(get_timing('page_load_wait', 2))
            print(f"1-3. 새창으로 전환 완료")
        
        # 3. 파일 업로드 요소 찾기 및 파일 선택
        print("1-4. 파일 업로드 요소 찾기...")
        file_input = driver.find_element(By.ID, "excelFile")
        excel_path = resolve_path(config['file_paths']['excel_file'])
        if not excel_path:
            excel_path = config['file_paths']['excel_file']
        print(f"1-5. 엑셀 파일 선택: {excel_path}")
        file_input.send_keys(excel_path)
        time.sleep(1)
        
        # 4. 업로드 버튼 클릭
        print("1-6. 업로드 버튼 클릭...")
        upload_button = driver.find_element(By.XPATH, "//button[text()='업로드']")
        upload_button.click()
        time.sleep(get_timing('upload_wait', 2))
        
        # 5. 업로드 성공 시스템 알럿 처리
        print("1-7. 시스템 알럿 처리...")
        try:
            alert = Alert(driver)
            alert.accept()
            print("업로드 성공 알럿 확인 완료")
        except:
            print("알럿이 없거나 이미 처리됨")
        
        # 6. 새창 닫기
        print("1-8. 새창 닫기...")
        driver.close()
        driver.switch_to.window(windows[0])
        print("1단계: 엑셀 파일 업로드 완료!")
        
        # 창 상태 확인
        print(f"업로드 후 창 개수: {len(driver.window_handles)}")
        print(f"현재 페이지 URL: {driver.current_url}")
        
        return True
        
    except Exception as e:
        print(f"1단계: 엑셀 파일 업로드 실패 - {e}")
        # 창 상태 복구
        try:
            windows = driver.window_handles
            if len(windows) > 1:
                driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except:
            pass
        return False

# ✅ 5. [2단계: 엑셀 파일 읽기]
def read_excel_data(excel_file_path, sheet_name, test_mode=None):
    """엑셀 파일에서 주문번호와 확정번호 데이터를 읽어옵니다."""
    try:
        # 엑셀 파일 경로 처리 (상대 경로 지원)
        resolved_path = resolve_path(excel_file_path)
        if not resolved_path:
            resolved_path = excel_file_path
        
        print(f"2-0. 엑셀 파일 읽기: {resolved_path}")
        
        # 엑셀 파일 읽기 (header=None으로 모든 행을 데이터로 읽기)
        df = pd.read_excel(resolved_path, sheet_name=sheet_name, header=None)
        print(f"2-0-1. 엑셀 파일 읽기 완료: {len(df)}개 행")
        print(f"2-0-2. 컬럼명: {list(df.columns)}")
        print(f"2-0-3. 첫 5행 데이터:")
        for i in range(min(5, len(df))):
            print(f"  행 {i+1}: {df.iloc[i].tolist()}")
        
        # 4행부터 데이터 시작 (인덱스 3부터) - 1행:제목, 2행:빈행, 3행:컬럼명
        data_start_index = 3  # 4행부터 시작
        if len(df) <= data_start_index:
            print("2-0-4. 데이터가 없습니다 (4행부터 시작해야 함)")
            return []
        
        # 4행부터 데이터 추출
        data_df = df.iloc[data_start_index:].copy()
        print(f"2-0-4. 4행부터 데이터 추출: {len(data_df)}개 행")
        
        # 테스트 모드 적용 (4행 기준으로 계산)
        if test_mode and test_mode.get('enabled', False):
            start_row = test_mode.get('start_row', 4) - 4  # 4행을 0으로 하는 상대 인덱스
            end_row = test_mode.get('end_row', len(data_df) + 3) - 3  # 4행 기준 상대 인덱스
            data_df = data_df.iloc[start_row:end_row]
            print(f"2-0-5. 테스트 모드 적용: {test_mode['start_row']}~{test_mode['end_row']}행 ({len(data_df)}개)")
        
        # 데이터 추출
        excel_data = []
        for index, row in data_df.iterrows():
            order_number = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            confirm_number = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            
            if order_number and order_number != 'nan':  # 주문번호가 있고 'nan'이 아닌 경우만 처리
                excel_data.append({
                    'order_number': order_number,
                    'confirm_number': confirm_number,
                    'original_order': order_number
                })
                print(f"2-0-6. 데이터 {len(excel_data)}: 주문번호={order_number}, 확정번호={confirm_number}")
        
        print(f"2-0-7. 최종 처리 데이터: {len(excel_data)}개")
        return excel_data
        
    except Exception as e:
        print(f"2-0. 엑셀 파일 읽기 실패: {e}")
        return []

# ✅ 6. [2단계: 주문번호로 검색]
def search_order_by_number(order_number):
    """주문번호로 검색하여 검색결과 페이지로 이동하고 검색 결과를 확인합니다."""
    try:
        log_debug(f"주문번호 검색 시작", order_number)
        
        # 검색 URL 생성 (config의 search_settings 사용)
        search_settings = config['search_settings']
        
        # search_status 지원 (하위 호환성을 위해 change_status도 지원)
        search_status = search_settings.get('search_status') or search_settings.get('change_status', '')
        
        search_url = (
            f"{config['urls']['base_url']}/orders?"
            f"appointDayType={search_settings.get('appoint_day_type', '')}&"
            f"exChannelId=&"
            f"nationIdx=&"
            f"addr1Idx=&"
            f"gradeType=&"
            f"perPage={search_settings.get('per_page', 100)}&"
            f"orderChannelIdx={search_settings.get('orderChannelIdx', '')}&"
            f"ratepalnSaleType=&"
            f"saleType={search_settings.get('saleType', '')}&"
            f"payStatus=&"
            f"orderProductStatus={search_status}&"
            f"orderRateplanType=&"
            f"dateType={search_settings.get('dateType', '')}&"
            f"startDate={search_settings.get('startDate', '')}&"
            f"endDate={search_settings.get('endDate', '')}&"
            f"searchType=orderNum&"
            f"keyword={order_number}"
        )
        log_debug(f"검색 URL 생성 완료", order_number)
        log_debug(f"생성된 검색 URL: {search_url}", order_number)
        log_debug(f"검색 조건 - 변경 전 상태: {search_status}, 주문번호: {order_number}", order_number)
        
        # 검색 페이지로 이동
        driver.get(search_url)
        time.sleep(get_timing('page_load_wait', 2))  # 페이지 로딩 대기
        
        # 검색 결과 페이지 안정화 대기 (더 긴 대기 시간)
        time.sleep(3)
        
        # 현재 URL 확인 (디버그용)
        current_url = driver.current_url
        log_debug(f"검색 후 현재 URL: {current_url}", order_number)
        
        # 검색 결과 확인 (여러 방법 시도)
        try:
            # 방법 1: 기본 선택자 시도 (order_link > blue_link 구조)
            links = driver.find_elements(By.CSS_SELECTOR, f"a.blue_link[href='/orders/{order_number}']")
            log_debug(f"방법1 - 기본 선택자로 찾은 링크: {len(links)}개", order_number)
            
            # 방법 1-1: order_link 내부의 blue_link도 확인
            if len(links) == 0:
                try:
                    links = driver.find_elements(By.CSS_SELECTOR, f"div.order_link a.blue_link[href='/orders/{order_number}']")
                    log_debug(f"방법1-1 - order_link 내부 선택자로 찾은 링크: {len(links)}개", order_number)
                except:
                    pass
            
            if len(links) == 0:
                # 방법 2: 부분 href 매칭 시도
                all_links = driver.find_elements(By.CSS_SELECTOR, "a.blue_link")
                log_debug(f"방법2 - 전체 blue_link 개수: {len(all_links)}개", order_number)
                
                matching_links = [link for link in all_links if order_number in link.get_attribute('href') or order_number in link.text]
                log_debug(f"방법2 - 주문번호 {order_number}가 포함된 링크: {len(matching_links)}개", order_number)
                
                if len(matching_links) == 0:
                    # 방법 3: 페이지 소스에서 주문번호 확인
                    page_source = driver.page_source
                    if order_number in page_source:
                        log_debug(f"방법3 - 페이지 소스에 주문번호 {order_number} 발견됨", order_number)
                        # 페이지 소스에는 있지만 링크를 찾지 못한 경우, 다시 시도
                        time.sleep(2)
                        links = driver.find_elements(By.CSS_SELECTOR, f"a.blue_link[href='/orders/{order_number}']")
                        if len(links) == 0:
                            # XPath로 시도
                            try:
                                links = driver.find_elements(By.XPATH, f"//a[contains(@href, '/orders/{order_number}')]")
                                log_debug(f"방법3 - XPath로 찾은 링크: {len(links)}개", order_number)
                            except:
                                pass
                    else:
                        log_debug(f"방법3 - 페이지 소스에 주문번호 {order_number} 없음", order_number)
                else:
                    links = matching_links
            
            if len(links) == 0:
                log_debug(f"검색 결과가 없습니다. 다음 주문번호로 진행합니다.", order_number)
                # 디버그: 페이지 제목과 URL 저장
                page_title = driver.title
                log_debug(f"페이지 제목: {page_title}", order_number)
                return False  # 검색 결과 없음
            else:
                log_debug(f"검색 결과 확인: 주문번호 링크 {len(links)}개 발견", order_number)
                return True
        except Exception as e:
            log_debug(f"검색 결과 확인 중 오류 발생: {e}", order_number)
            return False
        
    except Exception as e:
        log_debug(f"주문번호 검색 실패: {e}", order_number)
        return False

# ✅ 7. [2단계: 상세페이지 열기 및 상태 변경]
def change_reservation_status(order_number):
    """주문번호 링크를 클릭하여 상세페이지를 열고 예약상태를 확정으로 변경합니다."""
    try:
        log_debug(f"상세페이지 열기 및 상태 변경 시작", order_number)
        
        # 주문번호 링크 클릭
        try:
            link_element = driver.find_element(By.CSS_SELECTOR, f"a.blue_link[href='/orders/{order_number}']")
            link_element.click()
            time.sleep(get_timing_adv('detail_page_wait', 2))
        except Exception as e:
            log_debug(f"주문번호 링크를 찾을 수 없습니다: {e}", order_number)
            return False, "링크찾기실패"
        
        # 새창으로 전환
        windows = driver.window_handles
        if len(windows) > 1:
            new_window = [w for w in windows if w != main_window][0]
            driver.switch_to.window(new_window)
            time.sleep(get_timing_adv('detail_page_wait', 2))
            log_debug(f"상세페이지 새창으로 전환 완료", order_number)
        else:
            log_debug(f"새창이 열리지 않았습니다", order_number)
            return False, "새창열기실패"
        
        # 예약상태 드롭다운 찾기 및 변경
        try:
            select_element = driver.find_element(By.ID, "orderProductStatus")
            select = Select(select_element)
            previous_text = select.first_selected_option.text.strip()  # 한글 텍스트 (예: "대기")
            
            # 현재 상태의 영문 코드 가져오기 (한글 → 영문 변환)
            previous_value = STATUS_MAPPING.get(previous_text, previous_text)  # "대기" → "pending"
            
            # 상태 변경 목표값 처리
            target_status_from_config = config['status_change']['change_to_status']  # "cancel" 또는 "취소" 등
            
            # 디버그 로그: 설정 파일에서 읽은 원본 값 확인
            log_debug(f"설정 파일에서 읽은 change_to_status 원본 값: {target_status_from_config}", order_number)
            
            # 설정 파일의 값이 한글인지 영문인지 판단
            # STATUS_MAPPING의 값(한글)에 있는지 확인
            # 매핑 구조: {영문: 한글, 한글: 영문}
            # 따라서 값이 한글 매핑 키에 있으면 한글, 없으면 영문으로 간주
            target_value = target_status_from_config  # 기본값: 그대로 사용
            
            # 한글 키로 매핑되어 있는지 확인 (한글 → 영문 변환)
            if target_status_from_config in STATUS_MAPPING:
                mapped_value = STATUS_MAPPING[target_status_from_config]
                # 매핑된 값이 영문 코드 형태인지 확인 (소문자만 있는지, 한글이 아닌지)
                if isinstance(mapped_value, str) and mapped_value.isascii() and not any('\uAC00' <= c <= '\uD7A3' for c in mapped_value):
                    # 영문 코드로 변환됨 = 원본이 한글이었음
                    target_value = mapped_value
                else:
                    # 한글로 변환됨 = 원본이 영문이었음, 그대로 사용
                    target_value = target_status_from_config
            else:
                # STATUS_MAPPING에 없으면 영문 코드로 간주
                target_value = target_status_from_config
            
            # 영문 코드로 한글 표시명 가져오기 (로그용)
            # 영문 코드 → 한글 변환 (영문 키로 조회)
            target_text = STATUS_MAPPING.get(target_value, target_value)  # "cancel" → "취소"
            
            log_debug(f"현재 상태: {previous_text}({previous_value}), 목표 상태: {target_text}({target_value})", order_number)
            
            # 이미 목표 상태면 건너뜀 (영문 코드로 비교)
            if previous_value == target_value:
                log_debug(f"이미 {target_text}({target_value}) 상태입니다. 건너뜁니다.", order_number)
                driver.close()
                driver.switch_to.window(main_window)
                return (True, "이미확정", "미처리")
            
            # 상태 변경 (영문 코드 사용)
            select.select_by_value(target_value)
            time.sleep(2)  # 상태 변경 후 대기
            
            # 변경 확인
            select_element_after = driver.find_element(By.ID, "orderProductStatus")
            select_after = Select(select_element_after)
            current_text = select_after.first_selected_option.text.strip()  # 한글 텍스트
            current_value = STATUS_MAPPING.get(current_text, current_text)  # 영문 코드로 변환
            
            # 변경 확인 (영문 코드로 비교)
            if current_value == target_value:
                log_debug(f"상태 변경 성공: {previous_text}({previous_value}) → {current_text}({current_value})", order_number)
                status_changed = True
                
                # 상태 변경 후 LMS 전송 (상세페이지가 열린 상태에서)
                lms_success = send_lms(order_number)
                lms_result = "성공" if lms_success else "실패"
                log_debug(f"LMS 전송 결과: {lms_result}", order_number)
            else:
                log_debug(f"상태 변경 실패: 현재 {current_text}({current_value}), 목표 {target_text}({target_value})", order_number)
                status_changed = False
                lms_result = "미처리"
            
            # 창 닫기 및 메인창으로 복귀
            driver.close()
            driver.switch_to.window(main_window)
            time.sleep(get_timing_adv('refresh_wait', 2))
            
            # LMS 결과를 함께 반환하기 위해 튜플로 변경
            return (status_changed, current_value, lms_result)
            
        except Exception as e:
            log_debug(f"상태 변경 중 오류 발생: {e}", order_number)
            driver.close()
            driver.switch_to.window(main_window)
            return (False, f"상태변경오류: {str(e)}", "미처리")
        
    except Exception as e:
        log_debug(f"상태 변경 실패: {e}", order_number)
        # 창 상태 복구
        try:
            windows = driver.window_handles
            if len(windows) > 1:
                driver.close()
            driver.switch_to.window(main_window)
        except:
            pass
        return (False, f"오류: {str(e)}", "미처리")

# ✅ 8. [2단계: LMS 전송]
def send_lms(order_number=None):
    """LMS 전송 버튼을 클릭하고 팝업을 처리합니다."""
    try:
        log_debug(f"LMS 전송 시작", order_number)
        
        # LMS 전송 버튼 클릭
        lms_button = driver.find_element(By.CSS_SELECTOR, "input.send_lms.square_btn[value='LMS 전송']")
        lms_button.click()
        time.sleep(get_timing_adv('lms_popup_wait', 2))
        log_debug(f"LMS 전송 버튼 클릭 완료", order_number)
        
        # 팝업 처리 - 알럿 2개 처리
        try:
            # 알럿1: "구매확인 LMS 발송 요청 하시겠습니까?"
            alert1 = driver.switch_to.alert
            alert1_text = alert1.text
            log_debug(f"알럿1 메시지: {alert1_text}", order_number)
            alert1.accept()  # 확인 버튼 클릭
            time.sleep(1)  # 1초 대기
            log_debug(f"알럿1 확인 버튼 클릭 완료", order_number)
            
            # 알럿2: "구매확인 LMS 발송 요청 하였습니다."
            alert2 = driver.switch_to.alert
            alert2_text = alert2.text
            log_debug(f"알럿2 메시지: {alert2_text}", order_number)
            alert2.accept()  # 확인 버튼 클릭
            time.sleep(2)  # 2초 대기 (화면 새로고침 대기)
            log_debug(f"알럿2 확인 버튼 클릭 완료 - 팝업 닫힘", order_number)
            
            return True
        except Exception as e:
            log_debug(f"팝업이 나타나지 않았습니다: {e}", order_number)
            return False
        
    except Exception as e:
        log_debug(f"LMS 전송 실패: {e}", order_number)
        return False

# ✅ 9. [2단계: 메인 처리]
def process_confirm_numbers():
    """2단계: 엑셀 파일을 읽고 확정번호를 처리합니다."""
    try:
        print("2단계: 확정번호 처리 시작...")
        
        # 엑셀 파일 경로 처리 (상대 경로 지원)
        excel_file_path = resolve_path(config['file_paths']['excel_file'])
        if not excel_file_path:
            excel_file_path = config['file_paths']['excel_file']
        
        # 엑셀 파일 읽기
        excel_data = read_excel_data(
            excel_file_path,
            "list",  # 시트명 고정
            config['excel_settings'].get('test_mode')
        )
        
        if not excel_data:
            print("2단계: 처리할 데이터가 없습니다.")
            return
        
        print(f"2단계: {len(excel_data)}개 데이터 처리 시작")
        
        # 각 데이터 처리
        for i, data in enumerate(excel_data, 1):
            order_number = data['order_number']
            confirm_number = data['confirm_number']  # 로그용으로만 사용
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"\n--- {i}/{len(excel_data)} 처리 시작: 주문번호 {order_number} ---")
            
            # 1. 주문번호로 검색
            if not search_order_by_number(order_number):
                log_debug(f"검색 실패로 다음 주문번호로 진행합니다.", order_number)
                log_result(order_number, confirm_number, "검색결과없음", "미처리", timestamp)
                continue
            
            # 2. 상세페이지 열기 및 상태 변경 (LMS 전송 포함)
            status_success, status_result, lms_result = change_reservation_status(order_number)
            
            # 3. 결과 로그 기록
            log_result(order_number, confirm_number, status_result, lms_result, timestamp)
            
            log_debug(f"처리 완료: 상태={status_result}, LMS={lms_result}", order_number)
        
        print("2단계: 모든 데이터 처리 완료!")
        
    except Exception as e:
        print(f"2단계: 처리 중 오류 발생: {e}")

# ✅ 10. [메인 실행]
def main():
    global main_window
    try:
        # Lock 파일 확인
        if not check_lock_file():
            print("다른 프로세스가 실행 중입니다. 종료합니다.")
            return
        
        # Lock 파일 생성
        if not create_lock_file():
            print("Lock 파일 생성 실패. 종료합니다.")
            return
        
        # 실행 시작 로그
        log_start()
        
        # 1단계: 엑셀 파일 업로드
        upload_success = upload_excel_file()
        
        if not upload_success:
            print("엑셀 파일 업로드 실패로 작업을 중단합니다.")
            return
        
        print("1단계 완료! 2단계 시작...")
        
        # 메인창 핸들 저장
        main_window = driver.current_window_handle
        print(f"메인창 핸들 저장: {main_window}")
        
        # 2단계: 확정번호 처리
        process_confirm_numbers()
        
        print("모든 작업 완료!")
        
    except Exception as e:
        print(f"메인 실행 중 오류 발생: {e}")
    finally:
        # Lock 파일 제거
        remove_lock_file()
        
        # 브라우저 종료
        print("브라우저를 종료합니다.")
        driver.quit()

if __name__ == "__main__":
    main()
