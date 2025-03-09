from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QComboBox, QTextEdit, QMessageBox, QLineEdit)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QTextCursor  # QTextCursor는 QtGui에서 import
from qgis.utils import iface
from qgis.core import Qgis
from datetime import datetime
import os
from .work_handler import WorkHandler

class WorkWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.work_handler = WorkHandler()
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 상단 도구 모음
        top_toolbar = QHBoxLayout()
        
        # 스크립트 목록 콤보박스
        self.script_combo = QComboBox()
        self.script_combo.currentTextChanged.connect(self.load_script)
        top_toolbar.addWidget(self.script_combo)
        
        # 새로고침 버튼
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.setFixedWidth(80)
        self.refresh_btn.clicked.connect(self.refresh_scripts)
        top_toolbar.addWidget(self.refresh_btn)
        
        # 새 스크립트 버튼
        self.new_btn = QPushButton("N")
        self.new_btn.setFixedWidth(80)
        self.new_btn.clicked.connect(self.show_new_script_input)
        top_toolbar.addWidget(self.new_btn)
        
        layout.addLayout(top_toolbar)
        
        # 새 스크립트 입력 영역 (기본적으로 숨김)
        self.new_script_layout = QHBoxLayout()
        
        self.new_script_input = QLineEdit()
        self.new_script_input.setPlaceholderText("새 스크립트 파일 이름을 입력하세요")
        self.new_script_input.returnPressed.connect(self.create_new_script)
        self.new_script_layout.addWidget(self.new_script_input)
        
        self.create_btn = QPushButton("생성")
        self.create_btn.setFixedWidth(60)
        self.create_btn.clicked.connect(self.create_new_script)
        self.new_script_layout.addWidget(self.create_btn)
        
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setFixedWidth(60)
        self.cancel_btn.clicked.connect(self.hide_new_script_input)
        self.new_script_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(self.new_script_layout)
        
        # 새 스크립트 입력 영역 초기에 숨기기
        self.new_script_input.hide()
        self.create_btn.hide()
        self.cancel_btn.hide()
        
        # 에디터
        self.editor = QTextEdit()
        layout.addWidget(self.editor)
        
        # 하단 도구 모음
        bottom_toolbar = QHBoxLayout()
        
        # 저장 버튼
        self.save_btn = QPushButton("저장")
        self.save_btn.setFixedWidth(80)
        self.save_btn.clicked.connect(self.save_script)
        bottom_toolbar.addWidget(self.save_btn)
        
        # 실행 버튼
        self.run_btn = QPushButton("실행")
        self.run_btn.setFixedWidth(80)
        self.run_btn.clicked.connect(self.run_script)
        bottom_toolbar.addWidget(self.run_btn)
        
        layout.addLayout(bottom_toolbar)
        
        # 실행 결과 표시
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setMaximumHeight(100)
        layout.addWidget(self.result_display)
        
        # 초기 스크립트 목록 로드
        self.refresh_scripts()
        
    def show_new_script_input(self):
        """새 스크립트 입력 영역 표시"""
        self.new_script_input.show()
        self.create_btn.show()
        self.cancel_btn.show()
        self.new_script_input.setFocus()
        self.new_script_input.clear()
        
    def hide_new_script_input(self):
        """새 스크립트 입력 영역 숨기기"""
        self.new_script_input.hide()
        self.create_btn.hide()
        self.cancel_btn.hide()
        
    def create_new_script(self):
        """새 스크립트 생성"""
        try:
            filename = self.new_script_input.text().strip()
            if filename:
                filepath = self.work_handler.create_new_script(filename)
                self.refresh_scripts()
                self.script_combo.setCurrentText(filepath)
                self.hide_new_script_input()
            else:
                iface.messageBar().pushMessage("알림", "파일 이름을 입력해주세요.", 
                                             level=Qgis.Warning)
                
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))
            
    def refresh_scripts(self):
        """스크립트 목록 새로고침"""
        try:
            current = self.script_combo.currentText()
            self.script_combo.clear()
            
            scripts = self.work_handler.get_scripts_list()
            self.script_combo.addItems(scripts)
            
            if current in scripts:
                self.script_combo.setCurrentText(current)
                
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))
            
    def load_script(self, filename):
        """스크립트 내용 로드"""
        if not filename:
            return
            
        try:
            content = self.work_handler.load_script_content(filename)
            self.editor.setText(content)
            
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))
            
    def save_script(self):
        """스크립트 내용 저장"""
        filename = self.script_combo.currentText()
        if not filename:
            return
            
        try:
            content = self.editor.toPlainText()
            self.work_handler.save_script_content(filename, content)
            iface.messageBar().pushMessage("성공", "스크립트가 저장되었습니다.", level=Qgis.Success)
            
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))
            
    def run_script(self):
        """스크립트 실행"""
        filename = self.script_combo.currentText()
        if not filename:
            return
            
        try:
            # 먼저 저장
            self.save_script()
            
            # 실행
            result = self.work_handler.run_script(filename)
            
            # 결과 표시
            self.result_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] {result}")
            self.result_display.moveCursor(QTextCursor.End)
            
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e)) 