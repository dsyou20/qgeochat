import os
import sys
import importlib
from qgis.PyQt.QtWidgets import QMessageBox



def check(required_packages):
    # 필요한 패키지 설치 여부 확인
    missing_packages = []
    for package_req in required_packages:
        # 버전 정보가 있는 경우 패키지명만 추출
        package_name = package_req.split('>=')[0].split('==')[0].strip()
        try:
            module = importlib.import_module(package_name)
        except ImportError:
            missing_packages.append(package_req)

    if missing_packages:
        message = "QGeoChat 플러그인을 사용하기 위해 다음 Python 패키지가 필요합니다:\n\n"
        message += "\n".join(missing_packages)
        message += "\n\n지금 설치하시겠습니까? 설치 후 QGIS를 다시 시작해야 합니다."

        reply = QMessageBox.question(None, '필요한 종속성', message,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.No:
            return

        # requirements.txt 파일 경로
        requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
        
        try:
            # pip install -r requirements.txt 실행
            import subprocess
            subprocess.check_call([
                'python3', '-m', 'pip', 'install', '-r', requirements_path
            ])
        except Exception as e:
            # 패키지 설치 실패 메시지 표시
            error_msg = "패키지 설치 중 오류가 발생했습니다.\n\n"
            error_msg += "다음 패키지들을 수동으로 설치해주세요:\n"
            # requirements.txt 파일에서 패키지 목록 읽기
            with open(requirements_path, 'r') as f:
                packages = f.readlines()
            
            # 주석이나 빈 줄 제외하고 패키지 목록 추가
            for package in packages:
                package = package.strip()
                if package and not package.startswith('#'):
                    error_msg += f"{package}\n"
                    
                    
            error_msg = error_msg.rstrip()  # 마지막 줄바꿈 제거
            error_msg += "\n\n설치 방법:\n"
            error_msg += "1. 명령 프롬프트(cmd)를 관리자 권한으로 실행\n"
            error_msg += "2. 각 패키지를 다음 명령어로 설치:\n"
            error_msg += "   pip install <패키지명>\n"
            error_msg += "\n설치 후 QGIS를 다시 시작해주세요."
            
            QMessageBox.critical(None, '패키지 설치 실패', error_msg)
            raise Exception(f"패키지 설치 실패: {str(e)}")

   