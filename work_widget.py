from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QComboBox, QTextEdit, QMessageBox, QLineEdit, QSplitter,
                                QScrollBar)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QTextCursor, QTextCharFormat, QColor
from qgis.utils import iface
from qgis.core import Qgis
from datetime import datetime
import os
from .work_handler import WorkHandler
import re

class WorkWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.work_handler = WorkHandler()
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 다크 모드 스타일 적용
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #4f4f4f;
                color: #8f8f8f;
            }
            QComboBox {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox:drop-down {
                border: none;
            }
            QComboBox:down-arrow {
                background-color: #3f3f3f;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #ffffff;
                selection-background-color: #3f3f3f;
            }
            QLineEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        
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
        self.new_btn = QPushButton("새 스크립트")
        self.new_btn.setFixedWidth(80)
        self.new_btn.clicked.connect(self.show_new_script_input)
        top_toolbar.addWidget(self.new_btn)
        
        layout.addLayout(top_toolbar)
        
        # 새 스크립트 입력 영역
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
        
        # 스플리터 생성
        splitter = QSplitter(Qt.Vertical)
        
        # 에디터
        self.editor = QTextEdit()
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.editor.setLineWrapMode(QTextEdit.NoWrap)  # 자동 줄바꿈 비활성화
        
        # 에디터 폰트 설정
        font = self.editor.font()
        font.setFamily("Consolas")  # 고정폭 폰트
        font.setPointSize(10)
        self.editor.setFont(font)
        
        splitter.addWidget(self.editor)
        
        # 하단 영역 (실행 버튼과 결과 창)
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # 실행 버튼
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("저장")
        self.save_btn.setFixedWidth(80)
        self.save_btn.clicked.connect(self.save_script)
        button_layout.addWidget(self.save_btn)
        
        self.run_btn = QPushButton("실행")
        self.run_btn.setFixedWidth(80)
        self.run_btn.clicked.connect(self.run_script)
        button_layout.addWidget(self.run_btn)
        
        bottom_layout.addLayout(button_layout)
        
        # 실행 결과 표시
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.result_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.result_display.setLineWrapMode(QTextEdit.NoWrap)  # 자동 줄바꿈 비활성화
        
        # 결과 창 폰트 설정
        self.result_display.setFont(font)  # 에디터와 동일한 폰트 사용
        
        # 결과 창 스타일 설정
        self.result_display.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                padding: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: #1f1f1f;
                width: 12px;
                margin: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #1f1f1f;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #3f3f3f;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #4f4f4f;
            }
        """)
        
        # 결과 창 클릭 이벤트 연결
        self.result_display.mousePressEvent = self.handle_result_click
        
        bottom_layout.addWidget(self.result_display)
        
        # 에디터 스타일 설정
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                padding: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: #1f1f1f;
                width: 12px;
                margin: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #1f1f1f;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #3f3f3f;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #4f4f4f;
            }
        """)
        
        splitter.addWidget(bottom_widget)
        
        # 스플리터 비율 설정 (7:3)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter)
        
        # 에러 라인 하이라이트를 위한 포맷 설정
        self.error_format = QTextCharFormat()
        self.error_format.setBackground(QColor("#FFE4E1"))  # 연한 빨간색 배경
        self.error_format.setForeground(QColor("#FF0000"))  # 빨간색 텍스트
        
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
            iface.messageBar().pushMessage("성공", "스크립트가 실행되었습니다.", level=Qgis.Success)
            
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))
            
    def handle_result_click(self, event):
        """실행 결과 창 클릭 이벤트 처리"""
        cursor = self.result_display.cursorForPosition(event.pos())
        clicked_line = cursor.block().text()
        
        # 에러 메시지에서 라인 번호 추출
        line_match = re.search(r'line (\d+)', clicked_line)
        if line_match:
            try:
                error_line = int(line_match.group(1))
                self.highlight_error_line(error_line)
            except ValueError:
                pass
        
        # 기본 마우스 이벤트 처리
        QTextEdit.mousePressEvent(self.result_display, event)
        
    def highlight_error_line(self, line_number):
        """에디터에서 에러 라인 하이라이트"""
        # 이전 하이라이트 제거
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(QTextCharFormat())
        
        # 해당 라인으로 이동
        block = self.editor.document().findBlockByLineNumber(line_number - 1)  # 라인 번호는 0부터 시작
        if block.isValid():
            cursor = QTextCursor(block)
            self.editor.setTextCursor(cursor)
            
            # 라인 선택 및 하이라이트
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            cursor.setCharFormat(self.error_format)
            
            # 해당 라인이 보이도록 스크롤
            self.editor.ensureCursorVisible()
            
            # 에디터에 포커스
            self.editor.setFocus()
            
    def run_script(self):
        """스크립트 실행"""
        filename = self.script_combo.currentText()
        if not filename:
            return
            
        try:
            # 먼저 저장
            self.save_script()
            
            # 실행 전에 이전 하이라이트 제거
            cursor = self.editor.textCursor()
            cursor.select(QTextCursor.Document)
            cursor.setCharFormat(QTextCharFormat())
            
            # 실행 결과 창 초기화
            self.result_display.clear()
            
            # 실행
            result = self.work_handler.run_script(filename)
            
            # 타임스탬프
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # print 출력 내용이 있으면 먼저 표시
            if result['printed']:
                printed_lines = result['printed'].split('\n')
                for line in printed_lines:
                    if line.strip():
                        self.result_display.append(f"[{timestamp}] >>> {line}")
            
            # 실행 결과 표시
            if isinstance(result['result'], str):
                result_lines = result['result'].split('\n')
                for line in result_lines:
                    if line.strip():  # 빈 줄 제외
                        self.result_display.append(f"[{timestamp}] {line}")
            else:
                self.result_display.append(f"[{timestamp}] {result['result']}")
            
            # 커서를 맨 아래로 이동
            cursor = self.result_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.result_display.setTextCursor(cursor)
            
        except Exception as e:
            timestamp = datetime.now().strftime('%H:%M:%S')
            error_msg = f"[{timestamp}] 스크립트 실행 중 오류: {str(e)}"
            self.result_display.append(error_msg)