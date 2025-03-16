QGeoChat 플러그인 설치 가이드

시스템 요구사항

필수 요구사항

QGIS 3.x 이상 (OSGeo4W Network Installer로 설치)
Python 3.x (OSGeo4W에 포함)
OpenAI API 키
설치 방법

OSGeo4W Network Installer 설치

OSGeo4W Network Installer 다운로드
'Advanced Install' 선택
QGIS Desktop 패키지 선택 후 설치
플러그인 설치

이 저장소를 다운로드합니다.
QGeoChat 폴더를 QGIS 플러그인 디렉토리에 복사합니다:
C:\Users[사용자이름]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\
의존성 패키지 설치

OSGeo4W Shell을 사용한 설치 (권장)

시작 메뉴에서 OSGeo4W Shell을 실행합니다.
다음 명령어를 실행합니다:
플러그인 디렉토리로 이동:
cd %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\QGeoChat\install_packages
의존성 패키지 설치:
python -m pip install -r requirements.txt
OpenAI API 키 설정

QGIS를 실행합니다.
QGeoChat 플러그인을 실행합니다.
'설정' 탭으로 이동합니다.
OpenAI API 키를 입력합니다.
'저장' 버튼을 클릭하여 설정을 저장합니다.
설치 확인

설치가 완료된 후, 플러그인이 정상적으로 작동하는지 확인합니다. 플러그인을 실행하여 설정된 OpenAI API 키를 통해 정상적으로 작동하는지 점검하십시오.


[맥]
/Applications/QGIS.app/Contents/MacOS/bin/python3.9 -m pip install -r /QGIS/QGIS3/profiles/default/python/plugins Support/QGIS/QGIS3/profiles/default/python/plugins/qgeochat/install_packages/requirements.txt

--> cd /Users/dsyou20/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins 
