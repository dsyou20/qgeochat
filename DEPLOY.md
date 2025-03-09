


C:\Users\[사용자이름]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\


패키지 설치

OSGWP.shell에서 패키지 설치치

3. QGIS 재시작

#### 방법 2: ZIP 파일로 설치
1. 이 저장소를 ZIP 파일로 다운로드
2. QGIS 메뉴에서 `플러그인 > 플러그인 관리 및 설치 > ZIP으로 설치` 선택
3. 다운로드한 ZIP 파일 선택
4. '설치' 버튼 클릭

### 3. 의존성 패키지 설치

#### OSGeo4W Shell을 사용한 설치 (권장)
1. 시작 메뉴에서 'OSGeo4W Shell' 실행
2. 다음 명령어 실행:
```bash
# Python 환경 활성화
py3_env

# 플러그인 디렉토리로 이동
cd %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\QOllama

# 패키지 설치 스크립트 실행
python install_packages.py
```

#### 문제 발생 시 수동 설치
OSGeo4W Shell에서:
```bash
py3_env
python -m pip install openai>=0.27.0 markdown>=3.0.0
```

### 4. OpenAI API 키 설정
1. QGIS 실행
2. QOllama 플러그인 실행
3. '설정' 탭으로 이동
4. OpenAI API 키 입력
5. '저장' 버튼 클릭

## 설치 확인

### OSGeo4W Shell에서 확인
1. OSGeo4W Shell 실행
2. 다음 명령어 실행:
```bash
py3_env
python -c "import openai; import markdown; print('패키지 설치 완료!')"
```

### QGIS에서 확인
1. QGIS 재시작
2. 메뉴에서 `플러그인 > QOllama` 확인
3. QOllama 아이콘이 도구 모음에 표시되는지 확인

## 문제 해결

### 일반적인 문제

#### 패키지 설치 오류
1. OSGeo4W Shell을 관리자 권한으로 실행
2. 인터넷 연결 상태 확인
3. pip 업그레이드 시도:
```bash
py3_env
python -m pip install --upgrade pip
```

#### 플러그인이 로드되지 않는 경우
1. QGIS 로그 패널 확인 (보기 > 패널 > 로그 메시지)
2. OSGeo4W Shell에서 패키지 설치 상태 확인:
```bash
py3_env
python -m pip list | findstr "openai markdown"
```

#### OpenAI API 연결 오류
1. API 키가 올바르게 입력되었는지 확인
2. 인터넷 연결 상태 확인
3. OpenAI 서비스 상태 확인

### 로그 파일 위치