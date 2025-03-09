from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QComboBox, QTextEdit, QLineEdit)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.core import Qgis
from qgis.utils import iface
import os

from qgis.PyQt.QtCore import Qt, QEvent  # QEvent 추가
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings, Qt, QUrl, QEvent
from qgis.PyQt.QtWidgets import QStyle

class KnowHowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        plugin_dir = os.path.dirname(__file__)
        self.knowhow_dir = os.path.join(plugin_dir, 'myknowhow')
        
        self.current_file = None
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 상단 도구 모음
        top_toolbar = QHBoxLayout()
        
        # 목록 갱신 버튼
        self.refresh_btn = QPushButton("목록갱신")
        self.refresh_btn.setFixedWidth(100)
        self.refresh_btn.clicked.connect(self.refresh_knowhow_list)
        top_toolbar.addWidget(self.refresh_btn)
        
        # 지식 목록 콤보박스
        self.knowhow_combo = QComboBox()
        self.knowhow_combo.currentTextChanged.connect(self.load_knowhow_content)
        top_toolbar.addWidget(self.knowhow_combo)
        
        # 저장 버튼
        self.save_btn = QPushButton("저장")
        self.save_btn.setFixedWidth(80)
        self.save_btn.clicked.connect(self.save_knowhow)
        top_toolbar.addWidget(self.save_btn)
        
        # 새 지식 버튼 (아이콘)
        self.new_btn = QPushButton("N")
        self.new_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        self.new_btn.setToolTip("새 지식")
        self.new_btn.setFixedSize(24, 24)
        self.new_btn.clicked.connect(self.show_new_file_input)
        top_toolbar.addWidget(self.new_btn)
        
        # 삭제 버튼 (아이콘)
        self.delete_btn = QPushButton("D")
        self.delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.delete_btn.setToolTip("삭제")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.clicked.connect(self.delete_knowhow)
        top_toolbar.addWidget(self.delete_btn)
        
        main_layout.addLayout(top_toolbar)
        
        # 새 파일 입력 영역 (기본적으로 숨김)
        self.new_file_layout = QHBoxLayout()
        
        self.new_file_input = QLineEdit()
        self.new_file_input.setPlaceholderText("새 파일 이름을 입력하세요")
        self.new_file_input.returnPressed.connect(self.create_new_knowhow)
        self.new_file_layout.addWidget(self.new_file_input)
        
        self.create_btn = QPushButton("생성")
        self.create_btn.setFixedWidth(60)
        self.create_btn.clicked.connect(self.create_new_knowhow)
        self.new_file_layout.addWidget(self.create_btn)
        
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setFixedWidth(60)
        self.cancel_btn.clicked.connect(self.hide_new_file_input)
        self.new_file_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(self.new_file_layout)
        
        # 새 파일 입력 영역 초기에 숨기기
        self.new_file_input.hide()
        self.create_btn.hide()
        self.cancel_btn.hide()
        
        # 에디터
        self.editor = QTextEdit()
        self.editor.setMinimumHeight(400)
        main_layout.addWidget(self.editor)
        
        # 초기 목록 로드
        if not os.path.exists(self.knowhow_dir):
            os.makedirs(self.knowhow_dir)
        self.refresh_knowhow_list()
        
    def show_new_file_input(self):
        """새 파일 입력 영역 표시"""
        self.new_file_input.show()
        self.create_btn.show()
        self.cancel_btn.show()
        self.new_file_input.setFocus()
        self.new_file_input.clear()
        
    def hide_new_file_input(self):
        """새 파일 입력 영역 숨기기"""
        self.new_file_input.hide()
        self.create_btn.hide()
        self.cancel_btn.hide()
        
    def create_new_knowhow(self):
        """새 지식 파일 생성"""
        filename = self.new_file_input.text().strip()
        
        if not filename:
            iface.messageBar().pushMessage("알림", "파일 이름을 입력해주세요.", level=Qgis.Warning)
            return
            
        if not filename.endswith('.txt'):
            filename += '.txt'
            
        filepath = os.path.join(self.knowhow_dir, filename)
        
        if os.path.exists(filepath):
            iface.messageBar().pushMessage("오류", "이미 존재하는 파일 이름입니다.", level=Qgis.Warning)
            return
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('')
                
            self.current_file = filepath
            self.editor.clear()
            self.refresh_knowhow_list()
            
            # 새로 생성된 파일 선택
            index = self.knowhow_combo.findText(filename)
            if index >= 0:
                self.knowhow_combo.setCurrentIndex(index)
            
            # 입력 영역 숨기기
            self.hide_new_file_input()
            
            iface.messageBar().pushMessage("성공", "새 파일이 생성되었습니다.", level=Qgis.Success)
            
        except Exception as e:
            iface.messageBar().pushMessage("오류", f"파일 생성 중 오류가 발생했습니다: {str(e)}", level=Qgis.Critical)
        
    def refresh_knowhow_list(self):
        """지식 목록 새로고침"""
        current_text = self.knowhow_combo.currentText()
        self.knowhow_combo.clear()
        
        files = [f for f in os.listdir(self.knowhow_dir) if f.endswith('.txt')]
        if files:
            self.knowhow_combo.addItems(sorted(files))
            
            # 이전에 선택된 파일이 여전히 존재하면 다시 선택
            if current_text in files:
                self.knowhow_combo.setCurrentText(current_text)
            else:
                # 삭제된 경우 첫 번째 파일 선택
                self.knowhow_combo.setCurrentIndex(0)
        else:
            self.editor.clear()
            self.current_file = None
        
    def load_knowhow_content(self, filename):
        """선택한 지식 파일 내용 로드"""
        if not filename:
            return
            
        try:
            self.current_file = os.path.join(self.knowhow_dir, filename)
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setText(content)
        except Exception as e:
            QMessageBox.warning(self, "오류", f"파일을 읽는 중 오류가 발생했습니다: {str(e)}")
            
    def save_knowhow(self):
        """현재 편집 중인 지식 저장"""
        if not self.current_file:
            iface.messageBar().pushMessage("알림", "저장할 파일이 선택되지 않았습니다.", level=Qgis.Warning)
            return
            
        try:
            content = self.editor.toPlainText()
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            iface.messageBar().pushMessage("성공", "파일이 저장되었습니다.", level=Qgis.Success)
        except Exception as e:
            iface.messageBar().pushMessage("오류", f"파일 저장 중 오류가 발생했습니다: {str(e)}", level=Qgis.Critical)

    def delete_knowhow(self):
        """선택한 지식 파일 삭제"""
        current_file = self.knowhow_combo.currentText()
        if not current_file:
            iface.messageBar().pushMessage("알림", "삭제할 파일을 선택해주세요.", level=Qgis.Warning)
            return
        
        try:
            filepath = os.path.join(self.knowhow_dir, current_file)
            
            # 파일이 존재하는지 확인
            if not os.path.exists(filepath):
                iface.messageBar().pushMessage("오류", "파일을 찾을 수 없습니다.", level=Qgis.Warning)
                return
            
            # 파일 삭제
            os.remove(filepath)
            
            # 현재 파일 초기화
            if self.current_file == filepath:
                self.current_file = None
                self.editor.clear()
            
            # 목록 새로고침
            self.refresh_knowhow_list()
            
            iface.messageBar().pushMessage("성공", f"'{current_file}' 파일이 삭제되었습니다.", level=Qgis.Success)
            
        except Exception as e:
            iface.messageBar().pushMessage("오류", f"파일 삭제 중 오류가 발생했습니다: {str(e)}", level=Qgis.Critical) 