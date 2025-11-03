# GitHub 업로드 가이드

이 문서는 예약확정처리 시스템 v2.0을 GitHub에 업로드하는 방법을 안내합니다.

## 📋 사전 준비

### 1. GitHub 계정 생성 (없는 경우)

1. [GitHub](https://github.com) 접속
2. "Sign up" 클릭하여 계정 생성

### 2. Git 설치 확인

터미널(또는 PowerShell)에서 다음 명령어로 Git 설치 여부 확인:

```bash
git --version
```

설치되지 않은 경우:
- [Git 다운로드](https://git-scm.com/downloads)
- 설치 후 컴퓨터 재시작 권장

## 🚀 GitHub 업로드 방법

### 방법 1: GitHub 웹사이트에서 새 저장소 생성 (추천)

#### 1단계: GitHub에서 새 저장소 생성

1. GitHub에 로그인
2. 우측 상단의 **+** 버튼 클릭 → **New repository** 선택
3. 저장소 정보 입력:
   - **Repository name**: `admin-reservation-confirm` (또는 원하는 이름)
   - **Description**: `예약확정처리 자동화 시스템 v2.0`
   - **Public** 또는 **Private** 선택
   - **Initialize this repository with**: 체크하지 않기 (README, .gitignore 등은 로컬에 이미 있음)
4. **Create repository** 클릭

#### 2단계: 로컬 프로젝트를 Git 저장소로 초기화

PowerShell 또는 명령 프롬프트를 열고 프로젝트 폴더로 이동:

```bash
cd "C:\Users\윤성균\Documents\python_study\admin_예약확정처리_v1.0"
```

Git 저장소 초기화:

```bash
git init
```

#### 3단계: 파일 추가 및 커밋

```bash
# 모든 파일 추가
git add .

# 첫 번째 커밋
git commit -m "Initial commit: 예약확정처리 시스템 v2.0"
```

#### 4단계: GitHub 저장소와 연결

GitHub에서 생성한 저장소의 URL을 복사 (예: `https://github.com/your-username/admin-reservation-confirm.git`)

```bash
# 원격 저장소 추가 (URL은 본인의 저장소 URL로 변경)
git remote add origin https://github.com/your-username/admin-reservation-confirm.git

# 기본 브랜치 이름 설정
git branch -M main

# GitHub에 업로드
git push -u origin main
```

#### 5단계: 인증

- GitHub에 로그인하라는 창이 나타날 수 있습니다
- 또는 Personal Access Token이 필요할 수 있습니다 (아래 참조)

---

### 방법 2: GitHub CLI 사용 (고급)

GitHub CLI가 설치되어 있는 경우:

```bash
# GitHub CLI로 로그인
gh auth login

# 저장소 생성 및 업로드
cd "C:\Users\윤성균\Documents\python_study\admin_예약확정처리_v1.0"
gh repo create admin-reservation-confirm --public --source=. --remote=origin --push
```

---

## 🔐 Personal Access Token 생성 (필요한 경우)

Git이 인증을 요구하는 경우:

### 1. GitHub에서 토큰 생성

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. **Generate new token** → **Generate new token (classic)** 클릭
3. 토큰 정보 입력:
   - **Note**: `Local Git Access`
   - **Expiration**: 원하는 기간 선택
   - **Scopes**: `repo` 체크
4. **Generate token** 클릭
5. 생성된 토큰을 복사 (다시 볼 수 없으니 안전하게 보관)

### 2. Git에 토큰 사용

```bash
# 사용자 이름과 토큰 입력 요청 시
# Username: GitHub 사용자 이름
# Password: 생성한 Personal Access Token
```

또는 토큰을 URL에 포함:

```bash
git remote set-url origin https://YOUR_TOKEN@github.com/your-username/admin-reservation-confirm.git
```

---

## 📝 업로드 후 파일 업데이트

### 파일을 수정한 후 GitHub에 반영하기

```bash
# 변경된 파일 확인
git status

# 변경된 파일 추가
git add .

# 커밋 메시지와 함께 커밋
git commit -m "설명: 변경 내용 요약"

# GitHub에 업로드
git push
```

### 예시

```bash
# URL 자동 동기화 기능 추가
git add .
git commit -m "feat: URL 자동 동기화 기능 추가"
git push

# localStorage 기능 추가
git add .
git commit -m "feat: localStorage 자동 저장 기능 추가"
git push

# 버그 수정
git add .
git commit -m "fix: 프로젝트 중단 기능 개선"
git push
```

---

## ⚠️ 주의사항

### 민감한 정보 제외

`.gitignore` 파일에 다음이 포함되어 있습니다:
- `admin_confirm_config.json` - 설정 파일 (로그인 정보 포함 가능)
- `uploads/` - 업로드된 Excel 파일
- `logs/` - 로그 파일
- `results/` - 결과 파일

**중요**: GitHub에 업로드하기 전에 설정 파일에 실제 로그인 정보가 없는지 확인하세요!

### 설정 파일 예제 만들기

GitHub에 업로드할 예제 설정 파일 생성:

```bash
# admin_confirm_config.example.json 파일 생성
# 실제 로그인 정보 대신 예제 값 사용
```

---

## 📦 완료 확인

1. GitHub 저장소 페이지에서 파일이 올라갔는지 확인
2. `README.md` 파일이 제대로 표시되는지 확인
3. `.gitignore`가 작동하여 민감한 파일이 제외되었는지 확인

---

## 🔄 추후 업데이트

프로젝트를 수정한 후:

```bash
# 1. 변경 사항 확인
git status

# 2. 변경된 파일 추가
git add .

# 3. 커밋
git commit -m "변경 내용 설명"

# 4. GitHub에 업로드
git push
```

---

## 🆘 문제 해결

### 오류: "remote origin already exists"

```bash
# 기존 원격 저장소 제거
git remote remove origin

# 새로운 원격 저장소 추가
git remote add origin https://github.com/your-username/admin-reservation-confirm.git
```

### 오류: "fatal: refusing to merge unrelated histories"

```bash
# 강제 병합 허용
git pull origin main --allow-unrelated-histories
```

### 오류: 인증 실패

- Personal Access Token을 다시 생성
- Git Credential Manager 사용 고려
- GitHub CLI 사용 고려 (`gh auth login`)

---

## 📚 추가 자료

- [Git 공식 문서](https://git-scm.com/doc)
- [GitHub 가이드](https://guides.github.com/)
- [GitHub CLI 문서](https://cli.github.com/manual/)

