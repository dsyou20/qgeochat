import os
import json
import requests
import shutil
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QPushButton, QLineEdit, QLabel, QListWidget,
                           QCheckBox, QMessageBox, QGroupBox, QInputDialog,
                           QFileDialog)
from qgis.core import QgsSettings
import sys
import subprocess

class QShareWidget(QWidget):
    """QShare 탭 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.handler = SyncHandler()
        self.setup_ui()
        
    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 로그인 그룹
        login_group = QGroupBox("로그인")
        login_layout = QGridLayout()
        login_group.setLayout(login_layout)
        
        # 아이디/비밀번호 입력
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        # 로그인 정보 저장 체크박스
        self.save_login_checkbox = QCheckBox("로그인 정보 저장")
        
        # 로그인 버튼
        self.login_button = QPushButton("로그인")
        self.login_button.clicked.connect(self.handle_login)
        
        # 로그인 상태 라벨
        self.login_status_label = QLabel()
        
        # 위젯 배치
        login_layout.addWidget(QLabel("아이디:"), 0, 0)
        login_layout.addWidget(self.username_input, 0, 1)
        login_layout.addWidget(QLabel("비밀번호:"), 1, 0)
        login_layout.addWidget(self.password_input, 1, 1)
        login_layout.addWidget(self.save_login_checkbox, 2, 0, 1, 2)
        login_layout.addWidget(self.login_button, 3, 0, 1, 2)
        login_layout.addWidget(self.login_status_label, 4, 0, 1, 2)
        
        # 서버측 스크립트 그룹
        server_group = QGroupBox("서버 스크립트")
        server_layout = QVBoxLayout()
        server_group.setLayout(server_layout)
        
        # 서버 스크립트 목록
        self.server_script_list = QListWidget()
        self.server_script_list.setSelectionMode(QListWidget.ExtendedSelection)
        
        # 서버 버튼 영역
        server_button_layout = QHBoxLayout()
        self.download_button = QPushButton("다운로드")
        self.server_refresh_button = QPushButton("새로고침")
        
        self.download_button.clicked.connect(self.handle_download)
        self.server_refresh_button.clicked.connect(self.refresh_server_scripts)
        
        server_button_layout.addWidget(self.download_button)
        server_button_layout.addWidget(self.server_refresh_button)
        
        server_layout.addWidget(self.server_script_list)
        server_layout.addLayout(server_button_layout)
        
        # 로컬측 스크립트 그룹
        local_group = QGroupBox("로컬 스크립트")
        local_layout = QVBoxLayout()
        local_group.setLayout(local_layout)
        
        # 로컬 스크립트 목록
        self.local_script_list = QListWidget()
        self.local_script_list.setSelectionMode(QListWidget.ExtendedSelection)
        
        # 로컬 버튼 영역
        local_button_layout = QHBoxLayout()
        self.upload_button = QPushButton("업로드")
        self.local_refresh_button = QPushButton("새로고침")
        self.edit_script_button = QPushButton("편집")
        self.delete_script_button = QPushButton("삭제")
        
        self.upload_button.clicked.connect(self.handle_upload)
        self.local_refresh_button.clicked.connect(self.refresh_local_scripts)
        self.edit_script_button.clicked.connect(self.handle_edit_script)
        self.delete_script_button.clicked.connect(self.handle_delete_script)
        
        local_button_layout.addWidget(self.upload_button)
        local_button_layout.addWidget(self.local_refresh_button)
        local_button_layout.addWidget(self.edit_script_button)
        local_button_layout.addWidget(self.delete_script_button)
        
        local_layout.addWidget(self.local_script_list)
        local_layout.addLayout(local_button_layout)
        
        # 메인 레이아웃에 추가
        layout.addWidget(login_group)
        layout.addWidget(server_group)
        layout.addWidget(local_group)
        
        # 시그널 연결
        self.handler.login_status_changed.connect(self.update_login_status)
        self.handler.script_changed.connect(self.refresh_local_scripts)
        
        # 초기화
        self.load_saved_credentials()
        self.update_ui_state(False)
        self.refresh_local_scripts()
        
    def load_saved_credentials(self):
        """저장된 로그인 정보 로드"""
        username, password = self.handler.load_credentials()
        if username and password:
            self.username_input.setText(username)
            self.password_input.setText(password)
            self.save_login_checkbox.setChecked(True)
            
    def handle_login(self):
        """로그인 처리"""
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "경고", "아이디와 비밀번호를 입력해주세요.")
            return
        
        # 로그인 시도
        success, message = self.handler.login(username, password)
        
        if success:
            # 로그인 정보 저장
            if self.save_login_checkbox.isChecked():
                self.handler.save_credentials(username, password)
            
            # UI 상태 업데이트
            self.update_ui_state(True)
            self.refresh_server_scripts()
        
        QMessageBox.information(self, "로그인", message)
        
    def update_login_status(self, success, message):
        """로그인 상태 업데이트"""
        if success:
            self.login_status_label.setText("로그인 됨")
            self.login_status_label.setStyleSheet("color: green")
        else:
            self.login_status_label.setText("로그인 필요")
            self.login_status_label.setStyleSheet("color: red")
            
    def update_ui_state(self, is_logged_in):
        """UI 상태 업데이트"""
        # 서버 관련 버튼
        self.upload_button.setEnabled(is_logged_in)
        self.download_button.setEnabled(is_logged_in)
        self.server_refresh_button.setEnabled(is_logged_in)
        self.server_script_list.setEnabled(is_logged_in)
        
        # 로컬 관련 버튼 (로그인 상태와 관계없이 항상 활성화)
        self.local_refresh_button.setEnabled(True)
        self.edit_script_button.setEnabled(True)
        self.delete_script_button.setEnabled(True)
        self.local_script_list.setEnabled(True)
        
        if not is_logged_in:
            self.server_script_list.clear()
            
    def refresh_server_scripts(self):
        """서버 스크립트 목록 새로고침"""
        success, message, scripts = self.handler.list_available_scripts()
        
        if success:
            self.server_script_list.clear()
            self.server_script_list.addItems(scripts)
        else:
            QMessageBox.warning(self, "오류", message)
            
    def refresh_local_scripts(self):
        """로컬 스크립트 목록 새로고침"""
        success, message, scripts = self.handler.get_local_scripts()
        
        if success:
            self.local_script_list.clear()
            for script in scripts:
                self.local_script_list.addItem(script['name'])
        else:
            QMessageBox.warning(self, "오류", message)
            
    def handle_edit_script(self):
        """선택된 스크립트 편집"""
        selected_items = self.local_script_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "편집할 스크립트를 선택해주세요.")
            return
        
        script_name = selected_items[0].text()
        script_path = os.path.join(self.handler.scripts_dir, script_name)
        
        if os.path.exists(script_path):
            self.handler.open_in_editor(script_path)
        else:
            QMessageBox.warning(self, "오류", "스크립트 파일을 찾을 수 없습니다.")
            
    def handle_delete_script(self):
        """선택된 스크립트 삭제"""
        selected_items = self.local_script_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "삭제할 스크립트를 선택해주세요.")
            return
        
        # 확인 메시지
        if len(selected_items) == 1:
            msg = f"'{selected_items[0].text()}'를 삭제하시겠습니까?"
        else:
            msg = f"선택한 {len(selected_items)}개의 스크립트를 삭제하시겠습니까?"
            
        if QMessageBox.question(
            self, "삭제 확인", msg,
            QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        
        # 선택된 모든 스크립트 삭제
        for item in selected_items:
            success, message = self.handler.delete_script(item.text())
            if not success:
                QMessageBox.warning(self, "오류", message)
                
    def handle_upload(self):
        """선택된 로컬 스크립트 업로드"""
        selected_items = self.local_script_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "업로드할 스크립트를 선택해주세요.")
            return
        
        for item in selected_items:
            script_name = item.text()
            script_path = os.path.join(self.handler.scripts_dir, script_name)
            
            if os.path.exists(script_path):
                success, message = self.handler.upload_script(script_path)
                QMessageBox.information(self, "업로드", f"{script_name}: {message}")
                
                if success:
                    self.refresh_server_scripts()
            else:
                QMessageBox.warning(self, "오류", f"'{script_name}' 파일을 찾을 수 없습니다.")
                
    def handle_download(self):
        """선택된 서버 스크립트 다운로드"""
        selected_items = self.server_script_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "다운로드할 스크립트를 선택해주세요.")
            return
        
        for item in selected_items:
            script_name = item.text()
            save_path = os.path.join(self.handler.scripts_dir, script_name)
            
            success, message = self.handler.download_script(script_name, save_path)
            QMessageBox.information(self, "다운로드", f"{script_name}: {message}")
            
        self.refresh_local_scripts()  # 로컬 스크립트 목록 갱신

class SyncHandler(QObject):
    """QShare 동기화 처리를 위한 클래스"""
    
    # 시그널 정의
    login_status_changed = pyqtSignal(bool, str)  # (성공 여부, 메시지)
    sync_status_changed = pyqtSignal(bool, str)   # (성공 여부, 메시지)
    script_changed = pyqtSignal()  # 스크립트 변경 알림
    
    def __init__(self):
        super().__init__()
        self.settings = QgsSettings()
        self.base_url = "http://ect2.iptime.org:16001/api"  # QShare API 서버 주소
        self.session = requests.Session()
        self.access_token = None
        self.is_logged_in = False
        
        # 스크립트 디렉토리 초기화
        plugin_dir = os.path.dirname(__file__)
        self.scripts_dir = os.path.join(plugin_dir, 'myscripts')
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir)
            
    def _get_headers(self):
        """인증 헤더 반환"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        } if self.access_token else {}

    def open_in_editor(self, file_path):
        """파일을 기본 편집기로 열기"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            raise Exception(f"파일 열기 실패: {str(e)}")
            
    def get_local_scripts(self):
        """로컬 스크립트 목록 조회"""
        try:
            if not os.path.exists(self.scripts_dir):
                os.makedirs(self.scripts_dir)
                
            scripts = []
            for file_name in os.listdir(self.scripts_dir):
                if file_name.endswith('.py'):
                    file_path = os.path.join(self.scripts_dir, file_name)
                    stats = os.stat(file_path)
                    scripts.append({
                        'name': file_name,
                        'path': file_path,
                        'size': stats.st_size,
                        'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
            return True, "스크립트 목록 조회 성공", scripts
        except Exception as e:
            return False, f"스크립트 목록 조회 실패: {str(e)}", []
            
    def add_script(self, source_path=None, script_name=None, content=None):
        """스크립트 추가
        
        Args:
            source_path (str, optional): 복사할 스크립트 파일 경로
            script_name (str, optional): 새로 만들 스크립트 이름
            content (str, optional): 스크립트 내용
        """
        try:
            if source_path:
                # 파일 복사
                file_name = os.path.basename(source_path)
                dest_path = os.path.join(self.scripts_dir, file_name)
                shutil.copy2(source_path, dest_path)
                
            elif script_name:
                # 새 파일 생성
                if not script_name.endswith('.py'):
                    script_name += '.py'
                    
                file_path = os.path.join(self.scripts_dir, script_name)
                with open(file_path, 'w', encoding='utf-8') as f:
                    if content:
                        f.write(content)
                    else:
                        f.write("# -*- coding: utf-8 -*-\n\n")
                        
            self.script_changed.emit()
            return True, "스크립트가 추가되었습니다."
            
        except Exception as e:
            return False, f"스크립트 추가 실패: {str(e)}"
            
    def delete_script(self, script_name):
        """스크립트 삭제"""
        try:
            file_path = os.path.join(self.scripts_dir, script_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                self.script_changed.emit()
                return True, "스크립트가 삭제되었습니다."
            else:
                return False, "스크립트 파일을 찾을 수 없습니다."
        except Exception as e:
            return False, f"스크립트 삭제 실패: {str(e)}"
            
    def read_script(self, script_name):
        """스크립트 내용 읽기"""
        try:
            file_path = os.path.join(self.scripts_dir, script_name)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return True, "스크립트 읽기 성공", content
            else:
                return False, "스크립트 파일을 찾을 수 없습니다.", None
        except Exception as e:
            return False, f"스크립트 읽기 실패: {str(e)}", None
            
    def write_script(self, script_name, content):
        """스크립트 내용 쓰기"""
        try:
            file_path = os.path.join(self.scripts_dir, script_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.script_changed.emit()
            return True, "스크립트가 저장되었습니다."
        except Exception as e:
            return False, f"스크립트 저장 실패: {str(e)}"
            
    def rename_script(self, old_name, new_name):
        """스크립트 이름 변경"""
        try:
            if not new_name.endswith('.py'):
                new_name += '.py'
                
            old_path = os.path.join(self.scripts_dir, old_name)
            new_path = os.path.join(self.scripts_dir, new_name)
            
            if not os.path.exists(old_path):
                return False, "원본 스크립트 파일을 찾을 수 없습니다."
                
            if os.path.exists(new_path):
                return False, "같은 이름의 스크립트가 이미 존재합니다."
                
            os.rename(old_path, new_path)
            self.script_changed.emit()
            return True, "스크립트 이름이 변경되었습니다."
            
        except Exception as e:
            return False, f"스크립트 이름 변경 실패: {str(e)}"
            
    def get_script_info(self, script_name):
        """스크립트 정보 조회"""
        try:
            file_path = os.path.join(self.scripts_dir, script_name)
            if os.path.exists(file_path):
                stats = os.stat(file_path)
                info = {
                    'name': script_name,
                    'path': file_path,
                    'size': stats.st_size,
                    'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'created': datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                }
                return True, "스크립트 정보 조회 성공", info
            else:
                return False, "스크립트 파일을 찾을 수 없습니다.", None
        except Exception as e:
            return False, f"스크립트 정보 조회 실패: {str(e)}", None
            
    def save_credentials(self, email, password):
        """로그인 정보 저장"""
        try:
            self.settings.setValue("QShare/email", email)
            self.settings.setValue("QShare/password", password)  # 실제 구현시 암호화 필요
            return True, "로그인 정보가 저장되었습니다."
        except Exception as e:
            return False, f"로그인 정보 저장 실패: {str(e)}"
            
    def load_credentials(self):
        """저장된 로그인 정보 로드"""
        email = self.settings.value("QShare/email", "")
        password = self.settings.value("QShare/password", "")
        return email, password
        
    def login(self, email, password):
        """QShare 로그인"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password}
            )
            
            
            if response.status_code == 201:
                data = response.json()
                self.access_token = data.get('access_token')
                self.is_logged_in = True
                self.login_status_changed.emit(True, "로그인 성공")
                return True, "로그인 성공"
            else:
                return False, f"로그인 실패:{response.status_code} {response.json()}"
                
        except Exception as e:
            return False, f"로그인 중 오류 발생: {str(e)}"
            
    def upload_script(self, script_path):
        """스크립트 업로드"""
        if not self.is_logged_in:
            return False, "로그인이 필요합니다."
            
        try:
            script_name = os.path.basename(script_path)
            
            # 기존 스크립트 검색
            response = self.session.get(
                f"{self.base_url}/scripts/my",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                return False, f"스크립트 목록 조회 실패: {response.json().get('message', '알 수 없는 오류')}"
                
            scripts = response.json()
            existing_script = None
            
            # 동일한 이름의 스크립트 찾기
            for script in scripts:
                if script['title'] == script_name:
                    existing_script = script
                    break
                    
            # 기존 스크립트가 있으면 삭제
            if existing_script:
                delete_response = self.session.delete(
                    f"{self.base_url}/scripts/{existing_script['id']}",
                    headers=self._get_headers()
                )
                
                if delete_response.status_code != 200:
                    return False, f"기존 스크립트 삭제 실패: {delete_response.json().get('message', '알 수 없는 오류')}"
            
            # 새 스크립트 업로드
            with open(script_path, 'r', encoding='utf-8') as f:
                code = f.read()
                
            data = {
                "title": script_name,
                "description": f"{script_name} - QGIS 스크립트",
                "code": code,
                "isPublic": False
            }
            
            response = self.session.post(
                f"{self.base_url}/scripts",
                json=data,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                return True, "스크립트 업로드 성공"
            else:
                return False, f"스크립트 업로드 실패: {response.json().get('message', '알 수 없는 오류')}"
                
        except Exception as e:
            return False, f"업로드 중 오류 발생: {str(e)}"
            
    def get_unique_filename(self, base_path):
        """중복되지 않는 파일명 생성"""
        if not os.path.exists(base_path):
            return base_path
            
        directory = os.path.dirname(base_path)
        filename = os.path.basename(base_path)
        name, ext = os.path.splitext(filename)
        
        counter = 1
        while os.path.exists(base_path):
            new_filename = f"{name}({counter}){ext}"
            base_path = os.path.join(directory, new_filename)
            counter += 1
            
        return base_path
        
    def download_script(self, script_name, save_path):
        """스크립트 다운로드"""
        if not self.is_logged_in:
            return False, "로그인이 필요합니다."
            
        try:
            # 스크립트 목록 조회
            response = self.session.get(
                f"{self.base_url}/scripts/my",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                return False, f"스크립트 목록 조회 실패: {response.json().get('message', '알 수 없는 오류')}"
                
            scripts = response.json()
            target_script = None
            
            # 스크립트 찾기
            for script in scripts:
                if script['title'] == script_name:
                    target_script = script
                    break
                    
            if not target_script:
                return False, "스크립트를 찾을 수 없습니다."
                
            # 스크립트 상세 정보 조회
            response = self.session.get(
                f"{self.base_url}/scripts/{target_script['id']}",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                return False, f"스크립트 다운로드 실패: {response.json().get('message', '알 수 없는 오류')}"
                
            script_data = response.json()
            
            # 중복 파일명 처리
            actual_save_path = self.get_unique_filename(save_path)
            
            # 스크립트 저장
            with open(actual_save_path, 'w', encoding='utf-8') as f:
                f.write(script_data['content'])
                
            self.script_changed.emit()
            return True, f"스크립트가 '{os.path.basename(actual_save_path)}'로 다운로드되었습니다."
            
        except Exception as e:
            return False, f"다운로드 중 오류 발생: {str(e)}"
            
    def list_available_scripts(self):
        """서버에서 사용 가능한 스크립트 목록 조회"""
        if not self.is_logged_in:
            return False, "로그인이 필요합니다.", []
            
        try:
            response = self.session.get(
                f"{self.base_url}/scripts/my",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                scripts = response.json()
                script_names = [script['title'] for script in scripts]
                return True, "스크립트 목록 조회 성공", script_names
            else:
                return False, f"스크립트 목록 조회 실패: {response.json().get('message', '알 수 없는 오류')}", []
                
        except Exception as e:
            return False, f"스크립트 목록 조회 중 오류 발생: {str(e)}", []
            
    def share_script(self, script_name, share_with_all=False):
        """스크립트 공유"""
        if not self.is_logged_in:
            return False, "로그인이 필요합니다."
            
        try:
            # 스크립트 ID 찾기
            response = self.session.get(
                f"{self.base_url}/scripts/my",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                return False, f"스크립트 목록 조회 실패: {response.json().get('message', '알 수 없는 오류')}"
                
            scripts = response.json()
            script_id = None
            
            for script in scripts:
                if script['title'] == script_name:
                    script_id = script['id']
                    break
                    
            if not script_id:
                return False, "스크립트를 찾을 수 없습니다."
                
            # 공유 설정
            data = {"shareWithAll": share_with_all}
            response = self.session.post(
                f"{self.base_url}/scripts/{script_id}/share",
                json=data,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return True, "스크립트 공유 설정이 완료되었습니다."
            else:
                return False, f"스크립트 공유 설정 실패: {response.json().get('message', '알 수 없는 오류')}"
                
        except Exception as e:
            return False, f"스크립트 공유 중 오류 발생: {str(e)}"
            
    def get_shared_scripts(self):
        """공유받은 스크립트 목록 조회"""
        if not self.is_logged_in:
            return False, "로그인이 필요합니다.", []
            
        try:
            response = self.session.get(
                f"{self.base_url}/scripts/shared-with-me",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                scripts = response.json()
                script_names = [script['title'] for script in scripts]
                return True, "공유받은 스크립트 목록 조회 성공", script_names
            else:
                return False, f"공유받은 스크립트 목록 조회 실패: {response.json().get('message', '알 수 없는 오류')}", []
                
        except Exception as e:
            return False, f"공유받은 스크립트 목록 조회 중 오류 발생: {str(e)}", []
            
    def get_script_shares(self, script_name):
        """스크립트 공유 상태 조회"""
        if not self.is_logged_in:
            return False, "로그인이 필요합니다.", None
            
        try:
            # 스크립트 ID 찾기
            response = self.session.get(
                f"{self.base_url}/scripts/my",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                return False, f"스크립트 목록 조회 실패: {response.json().get('message', '알 수 없는 오류')}", None
                
            scripts = response.json()
            script_id = None
            
            for script in scripts:
                if script['title'] == script_name:
                    script_id = script['id']
                    break
                    
            if not script_id:
                return False, "스크립트를 찾을 수 없습니다.", None
                
            # 공유 상태 조회
            response = self.session.get(
                f"{self.base_url}/scripts/{script_id}/shares",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return True, "스크립트 공유 상태 조회 성공", response.json()
            else:
                return False, f"스크립트 공유 상태 조회 실패: {response.json().get('message', '알 수 없는 오류')}", None
                
        except Exception as e:
            return False, f"스크립트 공유 상태 조회 중 오류 발생: {str(e)}", None 