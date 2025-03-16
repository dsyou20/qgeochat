# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGeoChatDockWidget
                                 A QGIS plugin
 QGIS Ollama
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2025-03-02
        git sha              : $Format:%H$
        copyright            : (C) 2025 by dsyou / elcomtech
        email                : dsyou20@gmail,com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import re
from datetime import datetime
import sys
import subprocess

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from qgis.PyQt.QtCore import Qt, QEvent, QSize
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings, Qt, QUrl, QEvent
from qgis.core import QgsProject, Qgis, QgsVectorLayer, QgsWkbTypes, QgsRasterLayer, QgsSettings, QgsMapLayer
from openai import OpenAI
from .rag_handler import RAGHandler
from qgis.PyQt.QtGui import QDesktopServices, QTextCharFormat, QColor, QTextCursor, QIcon
from qgis.PyQt.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
                                QPushButton, QLineEdit, QTextEdit, QLabel,
                                QTabWidget, QListWidget, QComboBox, QCheckBox,
                                QProgressBar, QMessageBox, QGroupBox, QSizePolicy,
                                QToolButton, QStyle, QTextBrowser)
from .work_widget import WorkWidget  # 임시로 제거
from .knowhow_widget import KnowHowWidget

from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'QGeoChat_dockwidget_base.ui'))


class QGeoChatDockWidget(QDockWidget):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """초기화"""
        super().__init__("QGeoChat", parent)
        
        # QSettings 초기화
        self.settings = QSettings()
        
        # RAG 핸들러 초기화
        self.rag_handler = RAGHandler()
        
        # UI 설정
        self.setupUi()
        
        # 도킹 위젯 특성 설정 - 기본 기능 활성화
        self.setFeatures(QDockWidget.DockWidgetClosable | 
                        QDockWidget.DockWidgetMovable | 
                        QDockWidget.DockWidgetFloatable)
        
        # 크기 정책 설정
        self.setMinimumSize(QSize(300, 400))  # 최소 크기 설정
        
        # 초기 크기 설정
        if parent:
            self.resize(parent.width() // 3, parent.height())
            
        # 닫기 이벤트 처리를 위한 플래그
        self.is_closing = False
        
    def setupUi(self):
        """UI 초기 설정"""
        # 메인 위젯 생성
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        
        # 다크 모드 스타일 적용
        self.main_widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #3f3f3f;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #2b2b2b;
                color: #ffffff;
                padding: 8px 12px;
                border: 1px solid #3f3f3f;
            }
            QTabBar::tab:selected {
                background-color: #3f3f3f;
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
        """)
        
        # 메인 레이아웃 설정
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거
        self.main_layout.setSpacing(0)  # 위젯 간 간격 제거
        self.main_widget.setLayout(self.main_layout)
        
        # 도킹 위젯 설정
        self.setFeatures(QDockWidget.DockWidgetClosable | 
                        QDockWidget.DockWidgetMovable | 
                        QDockWidget.DockWidgetFloatable)
        self.setMinimumSize(QSize(300, 400))  # 최소 크기 설정
        
        # 탭 위젯 설정
        self.setup_tabs()
        self.main_layout.addWidget(self.tab_widget)
        
        # 크기 정책 설정
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def resizeEvent(self, event):
        """크기 조절 이벤트 처리"""
        super().resizeEvent(event)
        
        # 플로팅 상태일 때 내부 위젯들의 크기 조절
        if self.isFloating():
            new_size = event.size()
            self.main_widget.resize(new_size)
            self.tab_widget.resize(new_size)
            
            # 각 탭의 내용도 크기 조절
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                tab.resize(new_size)
            
    def showEvent(self, event):
        """표시 이벤트 처리"""
        super().showEvent(event)
        if self.parent():
            # 초기 표시 시 부모 위젯 너비의 1/3 사용
            self.resize(self.parent().width() // 3, self.parent().height())

    def setup_tabs(self):
        """탭 위젯 설정"""
        self.tab_widget = QTabWidget()
        
        # 레이어 정보 탭
        self.layer_info_tab = QWidget()
        self.setup_layer_info_ui()
        self.tab_widget.addTab(self.layer_info_tab, "지오챗")
        
        # 내 작업 탭
        self.my_job_tab = WorkWidget()
        self.tab_widget.addTab(self.my_job_tab, "내 작업")
        
        
        # 내 노하우 탭
        self.my_knowhow_tab = KnowHowWidget()
        self.tab_widget.addTab(self.my_knowhow_tab, "내 노하우")
        

        
        # 설정 탭
        self.settings_tab = QWidget()
        self.setup_settings_ui()
        self.tab_widget.addTab(self.settings_tab, "설정")
        
        # 정보 탭
        self.info_tab = QWidget()
        self.setup_info_ui()
        self.tab_widget.addTab(self.info_tab, "정보")

    def setup_layer_info_ui(self):
        """레이어 정보 탭 UI 설정"""
        layout = QVBoxLayout()
        self.layer_info_tab.setLayout(layout)
        
        # 상단 버튼 영역
        button_layout = QHBoxLayout()
        
        # 버튼 컨테이너 위젯 생성
        button_container = QWidget()
        button_container_layout = QHBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.setSpacing(5)
        
        # 레이어 정보 갱신 버튼 (70%)
        self.refresh_button = QPushButton("지식 갱신하기")
        self.refresh_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.refresh_button.clicked.connect(self.process_all_layers)
        button_container_layout.addWidget(self.refresh_button, 70)
        
        # 외부 에디터로 보기 버튼 (30%)
        self.view_text_button = QPushButton("지식 보기")
        self.view_text_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.view_text_button.clicked.connect(self.view_reference_text)
        self.view_text_button.setEnabled(False)  # 초기에는 비활성화
        button_container_layout.addWidget(self.view_text_button, 30)
        
        button_layout.addWidget(button_container)
        button_layout.addStretch()  # 나머지 공간을 채움
        
        layout.addLayout(button_layout)
        
        # 채팅 표시 영역
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(False)
        self.chat_display.anchorClicked.connect(self.open_file_from_link)
        self.chat_display.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse
        )
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: Arial;
                font-size: 10pt;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
            }
            QTextBrowser:disabled {
                background-color: #1f1f1f;
                color: #8f8f8f;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # 입력 영역
        input_layout = QHBoxLayout()
        
        self.input_text = QTextEdit()
        self.input_text.setMinimumHeight(60)
        self.input_text.setMaximumHeight(100)
        self.input_text.setAcceptRichText(False)
        self.input_text.installEventFilter(self)
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: Arial;
                font-size: 10pt;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                padding: 4px;
            }
            QTextEdit:disabled {
                background-color: #1f1f1f;
                color: #8f8f8f;
            }
        """)
        
        input_layout.addWidget(self.input_text)
        
        # 전송 버튼
        self.send_button = QPushButton("전송")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # 레이아웃의 크기 정책 설정
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

    def eventFilter(self, obj, event):
        """이벤트 필터 처리"""
        # if obj == self.input_text and event.type() == QEvent.KeyPress:
        #     if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
        #         if event.modifiers() == Qt.ControlModifier:
        #             # Ctrl+Enter: 줄바꿈
        #             cursor = self.input_text.textCursor()
        #             cursor.insertText('\n')
        #             return True
        #         else:
        #             # Enter: 메시지 전송
        #             self.send_message()
        #             return True
        return super().eventFilter(obj, event)

    def format_ai_response(self, text):
        """AI 응답 텍스트 포맷팅"""
        formatted_lines = []
        
        # 줄 단위로 처리
        lines = text.split('\n')
        for line in lines:
            #공백이나 텝을 &nbsp 로치환
            line = line.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')    
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)

    def send_message(self):
        """메시지 전송"""
        text = self.input_text.toPlainText().strip()
        if text:
            # 사용자 메시지 - 빨간색
            lines = text.split('\n')
            for line in lines:
                self.chat_display.append(f'<span style="color: #FF0000;">[사용자] {line}</span>')
            self.input_text.clear()
            
            try:
                # API 키 확인
                api_key = self.get_api_key()
                if not api_key:
                    self.chat_display.append('[시스템] OpenAI API 키가 설정되지 않았습니다.')
                    return
                    
                # RAG 핸들러로 응답 생성
                response = self.rag_handler.query(text)
                
                if False:
                    # 파일로 저장하기
                    # 응답을 파일로 저장
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f'response_{timestamp}.txt'
                    filepath = os.path.join(os.path.dirname(__file__), 'responses', filename)
                
                    # responses 디렉토리가 없으면 생성
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    
                    # 파일 저장
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(response)
                        
                    # 외부 편집기로 열기
                    if os.name == 'nt':  # Windows
                        os.startfile(filepath)
                    else:  # Linux/Mac
                        os.system(f'xdg-open "{filepath}"')
                    
                # AI 응답 포맷팅 및 표시
                formatted_response = self.format_ai_response(response)
                first = True
                for line in formatted_response.split('\n'):
                    if first:
                        self.chat_display.append(f'<span style="color: #008000;">[AI] {line.strip()}</span>')
                        first = False
                    else:
                        self.chat_display.append(f'<span style="color: #008000;">{line}</span>')
            except Exception as e:
                error_msg = f"메시지 처리 중 오류가 발생했습니다: {str(e)}"
                self.chat_display.append(f"[시스템] {error_msg}")
                QMessageBox.warning(self, "오류", error_msg)

    def setup_settings_ui(self):
        """설정 탭 UI 설정"""
        layout = QVBoxLayout()
        self.settings_tab.setLayout(layout)
        
        # API 키 입력 그룹
        api_group = QGroupBox("OpenAI API 설정")
        api_layout = QVBoxLayout()
        api_group.setLayout(api_layout)
        
        # API 키 입력 필드
        api_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)  # 입력 값 숨김
        
        # 저장된 API 키 불러오기
        saved_api_key = self.settings.value("QGeoChat/api_key", "", type=str)
        self.api_key_input.setText(saved_api_key)
        
        # API 키 저장 체크박스
        self.save_api_checkbox = QCheckBox("API 키 저장")
        self.save_api_checkbox.setChecked(bool(saved_api_key))  # 저장된 키가 있으면 체크
        
        # API 키 저장 버튼
        save_button = QPushButton("저장")
        save_button.clicked.connect(self.save_api_key)
        
        # 레이아웃에 위젯 추가
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_input)
        api_layout.addWidget(self.save_api_checkbox)
        api_layout.addWidget(save_button)
        
        layout.addWidget(api_group)
        layout.addStretch()
        
        # 레이아웃의 크기 정책 설정
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

    def setup_connections(self):
        """시그널-슬롯 연결"""
        self.api_key_input.textChanged.connect(self.update_api_key)
        self.save_api_checkbox.stateChanged.connect(self.handle_save_api_setting)
        self.refresh_button.clicked.connect(self.process_all_layers)
        self.input_text.returnPressed.connect(self.send_message)

    def load_api_key(self):
        """저장된 API 키 로드"""
        if self.settings.value("QGeoChat/save_api_key", False, type=bool):
            saved_key = self.settings.value("QGeoChat/api_key", "")
            if saved_key:
                self.api_key_input.setText(saved_key)
                self.update_api_key()
                self.append_message("[시스템] 저장된 API 키를 불러왔습니다.")

    def handle_save_api_setting(self, state):
        """API 키 저장 설정 처리"""
        self.settings.setValue("QGeoChat/save_api_key", bool(state))
        if state:
            if self.api_key:
                self.settings.setValue("QGeoChat/api_key", self.api_key)
                self.append_message("[시스템] API 키가 저장되었습니다.")
        else:
            self.settings.remove("QGeoChat/api_key")
            self.append_message("[시스템] 저장된 API 키가 삭제되었습니다.")

    def update_api_key(self):
        """API 키 업데이트 및 상태 표시"""
        api_key = self.api_key_input.text().strip()
        if api_key:
            try:
                self.api_key = api_key
                self.rag_handler = RAGHandler()
                self.api_status_label.setText("API 키가 설정되었습니다")
                self.api_status_label.setStyleSheet("color: green")
                
                # API 키 저장 처리
                if self.save_api_checkbox.isChecked():
                    self.settings.setValue("QGeoChat/api_key", api_key)
                    self.append_message("[시스템] API 키가 저장되었습니다.")
                
            except Exception as e:
                self.api_status_label.setText(f"API 키 설정 실패: {str(e)}")
                self.api_status_label.setStyleSheet("color: red")
                self.process_button.setEnabled(False)
                self.rag_handler = None
                self.api_key = None
        else:
            self.process_button.setEnabled(False)
            self.api_status_label.setText("API 키를 입력해주세요")
            self.api_status_label.setStyleSheet("color: red")
            self.rag_handler = None
            self.api_key = None

    def get_knowhow_text(self):
        """myknowhow 폴더에서 문서 텍스트 읽기"""
        # myknowhow 폴더 경로
        plugin_dir = os.path.dirname(__file__)
        knowhow_dir = os.path.join(plugin_dir, 'myknowhow')
        
        if not os.path.exists(knowhow_dir):
            os.makedirs(knowhow_dir)
            return ""
        
        self.knowhow_dir = knowhow_dir
        
        all_text = ""
        
        print( "knowhow_dir: ", knowhow_dir )
        
        # 텍스트 파일 읽기
        for file in os.listdir(knowhow_dir):
            file_path = os.path.join(knowhow_dir, file)
            if file.endswith('.txt'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            all_text += f"\n## {file}\n{content}\n"
                            
                        self.chat_display.append(f"[시스템] {file} 지식화 완료 ")
                        
                except Exception as e:
                    self.chat_display.append(f"[시스템] {file} 읽기 실패: {str(e)}")
                    
            elif file.endswith('.pdf'):
                try:
                    # PyPDF2가 설치되어 있는지 확인
                    try:
                        import PyPDF2
                    except ImportError:
                        self.chat_display.append("[시스템] PDF 파일을 읽기 위해서는 PyPDF2 모듈이 필요합니다.")
                        continue
                        
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        content = ""
                        for page in reader.pages:
                            content += page.extract_text()
                        if content.strip():
                            all_text += f"\n## {file}\n{content.strip()}\n"
                            
                        self.chat_display.append(f"[시스템] {file_path} 지식화 완료 ")
                        
                except Exception as e:
                    self.chat_display.append(f"[시스템] {file} 읽기 실패: {str(e)}")
                    
        return all_text

    def get_script_text(self):
        """myscripts 폴더에서 문서 텍스트 읽기"""
        # myscripts 폴더 경로
        plugin_dir = os.path.dirname(__file__)
        script_dir = os.path.join(plugin_dir, 'myscripts')
        
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
            return ""
        
        self.script_dir = script_dir
        
        all_text = ""
        
        print( "script_dir: ", script_dir )
        
        # 텍스트 파일 읽기
        for file in os.listdir(script_dir):
            file_path = os.path.join(script_dir, file)
            if file.endswith('.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            all_text += f"\n## {file}\n{content}\n"
                            
                        self.chat_display.append(f"[시스템] {file} 스크립트 로드 완료")
                        
                except Exception as e:
                    self.chat_display.append(f"[시스템] {file} 읽기 실패: {str(e)}")
                    
        return all_text

    def process_all_layers(self):
        """모든 레이어 처리"""
        try:
            info = "# 레이어 정보\n\n"
            layers = QgsProject.instance().mapLayers().values()
            
            for layer in layers:
                info += f"## {layer.name()}\n"
                
                # 레이어 타입 확인
                if isinstance(layer, QgsVectorLayer):
                    # 벡터 레이어
                    info += f"- 타입: 벡터\n"
                    info += f"- 도형 유형: {self.get_geometry_type_name(layer.geometryType())}\n"
                    info += f"- 피처 수: {layer.featureCount()}\n"
                    info += f"- 필드 수: {len(layer.fields())}\n"
                    info += f"- 좌표계: {layer.crs().authid()}\n"
                    
                    # 상세 분석 추가
                    info += self.analyze_vector_layer(layer)
                
                elif isinstance(layer, QgsRasterLayer):
                    # 래스터 레이어
                    info += f"- 타입: 래스터\n"
                    info += f"- 밴드 수: {layer.bandCount()}\n"
                    info += f"- 너비: {layer.width()} 픽셀\n"
                    info += f"- 높이: {layer.height()} 픽셀\n"
                    info += f"- 좌표계: {layer.crs().authid()}\n"
                    
                    # 래스터 통계 추가
                    stats = self.get_raster_statistics(layer)
                    if stats:
                        info += f"\n{stats}\n"
                
                info += "\n"
                

            
            # 채팅 창에 메시지 표시
            self.chat_display.append("[시스템] 레이어 정보가 갱신되었습니다.")
            
            # 노하우 텍스트 자동 추가
            knowhow_text = self.get_knowhow_text()
            self.chat_display.append("[시스템] 노하우 정보가 갱신되었습니다.")
            
            # 스크립트 텍스트 자동 추가
            script_text = self.get_script_text()
            self.chat_display.append("[시스템] 스크립트 정보가 갱신되었습니다.")
            
            text = info + knowhow_text + script_text
            
            self.rag_handler.create_vector_store( text )
            
            # 텍스트 파일로 저장
            self.save_reference_text()
            
            # 버튼 활성화
            self.view_text_button.setEnabled(True)
                
                
        except Exception as e:
            error_msg = f"레이어 처리 중 오류가 발생했습니다: {str(e)}"
            self.chat_display.append(f"[시스템] {error_msg}")
            iface.messageBar().pushMessage("오류", error_msg, level=Qgis.Critical)

    def get_geometry_type_name(self, geom_type):
        """도형 유형 이름 반환"""
        types = {
            0: "포인트",
            1: "라인",
            2: "폴리곤",
            3: "알 수 없음",
            4: "NULL",
            5: "복합 도형"
        }
        return types.get(geom_type, "정의되지 않음")

    def analyze_vector_layer(self, layer):
        """벡터 레이어 분석"""
        try:
            analysis = f"### 벡터 레이어 분석\n"
            
            # 레이어 정보   
            analysis += f"- 레이어 이름: {layer.name()}\n"
            analysis += f"- 도형 유형: {self.get_geometry_type_name(layer.geometryType())}\n"
            analysis += f"- 좌표계: {layer.crs().authid()}\n"
            
            # 피처 수 추가
            analysis += f"- 피처 수: {layer.featureCount()}\n"
            
            # 필드 정보 추가
            fields = layer.fields()
            analysis += f"- 필드 수: {len(fields)}\n"
            for field in fields:
                analysis += f"  - 필드 이름: {field.name()}, 유형: {field.type()}\n"
                
            # GeoPandas로 기초 통계 추가
            try:
                # 레이어를 GeoDataFrame으로 변환
                gdf = gpd.GeoDataFrame.from_features([feat for feat in layer.getFeatures()])
                
                # 수치형 컬럼에 대한 기초 통계
                numeric_cols = gdf.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    analysis += "\n#### 수치 데이터 통계\n"
                    for col in numeric_cols:
                        if col != 'geometry':
                            stats = gdf[col].describe()
                            analysis += f"\n{col} 통계:\n"
                            analysis += f"  - 평균: {stats['mean']:.2f}\n"
                            analysis += f"  - 중앙값: {stats['50%']:.2f}\n"
                            analysis += f"  - 표준편차: {stats['std']:.2f}\n"
                            analysis += f"  - 최소값: {stats['min']:.2f}\n"
                            analysis += f"  - 최대값: {stats['max']:.2f}\n"
                
                # 도형 면적/길이 통계 (도형 유형에 따라)
                if layer.geometryType() == 2:  # 폴리곤
                    areas = gdf.geometry.area
                    analysis += "\n#### 면적 통계\n"
                    analysis += f"  - 평균 면적: {areas.mean():.2f}\n"
                    analysis += f"  - 최소 면적: {areas.min():.2f}\n"
                    analysis += f"  - 최대 면적: {areas.max():.2f}\n"
                elif layer.geometryType() == 1:  # 라인
                    lengths = gdf.geometry.length
                    analysis += "\n#### 길이 통계\n"
                    analysis += f"  - 평균 길이: {lengths.mean():.2f}\n"
                    analysis += f"  - 최소 길이: {lengths.min():.2f}\n"
                    analysis += f"  - 최대 길이: {lengths.max():.2f}\n"
                    
            except Exception as e:
                analysis += f"\n[GeoPandas 통계 계산 중 오류 발생: {str(e)}]\n"

            return analysis
        except Exception as e:
            return f"벡터 레이어 분석 중 오류 발생: {str(e)}"   

    def get_raster_statistics(self, layer):
        """래스터 레이어 통계 정보 반환"""
        try:
            stats = "### 래스터 통계\n"
            
            for band in range(1, layer.bandCount() + 1):
                stats += f"\n#### 밴드 {band}\n"
                
                # 밴드 통계 가져오기
                provider = layer.dataProvider()
                min_val = provider.bandStatistics(band).minimumValue
                max_val = provider.bandStatistics(band).maximumValue
                mean = provider.bandStatistics(band).mean
                std_dev = provider.bandStatistics(band).stdDev
                
                stats += f"- 최소값: {min_val:.2f}\n"
                stats += f"- 최대값: {max_val:.2f}\n"
                stats += f"- 평균값: {mean:.2f}\n"
                stats += f"- 표준편차: {std_dev:.2f}\n"
                
                # 픽셀 타입 정보
                data_type = provider.dataType(band)
                stats += f"- 데이터 타입: {self.get_raster_data_type(data_type)}\n"
                
            return stats
        except Exception as e:
            return f"래스터 통계 계산 중 오류 발생: {str(e)}"

    def get_raster_data_type(self, data_type):
        """래스터 데이터 타입 이름 반환"""
        types = {
            0: "알 수 없음",
            1: "Byte",
            2: "UInt16",
            3: "Int16",
            4: "UInt32",
            5: "Int32",
            6: "Float32",
            7: "Float64",
            8: "CInt16",
            9: "CInt32",
            10: "CFloat32",
            11: "CFloat64"
        }
        return types.get(data_type, "정의되지 않음")

    def append_message(self, message):
        """채팅 메시지 추가 (색상 적용)"""
        self.chat_history.append(message)
        
        # 이전 텍스트 지우기
        self.chat_display.clear()
        
        # 메시지 색상 적용하여 추가
        cursor = self.chat_display.textCursor()
        for msg in self.chat_history:
            format = QTextCharFormat()
            
            # 메시지 타입에 따른 색상 설정
            for prefix, color in self.message_colors.items():
                if msg.startswith(prefix):
                    format.setForeground(color)
                    break
            
            cursor.insertText(msg + '\n', format)
        
        # 스크롤을 최하단으로 이동
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def closeEvent(self, event):
        """도킹 위젯 닫기 이벤트 처리"""
        if self.isFloating():
            event.ignore()
            self.setFloating(False)
            self.show()
        else:
            event.ignore()
            self.hide()
            
    def show_dockwidget(self):
        """도킹 위젯 표시"""
        self.show()
        self.setFloating(False)
        iface.addDockWidget(Qt.RightDockWidgetArea, self)

    def setup_chat_ui(self):
        """채팅 UI 설정"""
        # 채팅 표시 영역 설정
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: white;
                color: black;
                font-family: Arial;
                font-size: 10pt;
                line-height: 1.5;
            }
        """)
        self.chat_display.setAcceptRichText(True)  # HTML 형식 허용
        self.chat_display.setReadOnly(True)  # 읽기 전용

    def clear_chat_history(self):
        """대화 기록 초기화"""
        try:
            self.rag_handler.clear_chat_history()
            self.chat_display.clear()
            self.chat_display.append("대화 기록이 초기화되었습니다.")
        except Exception as e:
            QMessageBox.warning(self, "오류", f"대화 기록 초기화 중 오류가 발생했습니다: {str(e)}")

    def load_changelog(self):
        """업데이트 내역 로드"""
        try:
            # 플러그인 디렉토리 내의 CHANGELOG.md 파일 경로
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            changelog_path = os.path.join(plugin_dir, 'CHANGELOG.md')
            
            if os.path.exists(changelog_path):
                with open(changelog_path, 'r', encoding='utf-8') as f:
                    changelog_text = f.read()
                self.changelog_display.setPlainText(changelog_text)
            else:
                self.changelog_display.setPlainText("업데이트 내역 파일을 찾을 수 없습니다.")
                
        except Exception as e:
            self.changelog_display.setPlainText(f"업데이트 내역을 불러오는 중 오류가 발생했습니다: {str(e)}")

    def style_markdown(self, text):
        """마크다운 텍스트를 HTML로 변환"""
        html = text
        
        # 제목 변환
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # 목록 변환
        html = re.sub(r'^\- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*?</li>\n)+', r'<ul>\g<0></ul>', html, flags=re.DOTALL)
        
        # 강조 변환
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # 코드 블록 변환
        html = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
        
        # 스타일 추가
        html = f"""
        <style>
            h1 {{ color: #2c3e50; font-size: 18pt; margin-top: 20px; }}
            h2 {{ color: #34495e; font-size: 14pt; margin-top: 15px; }}
            h3 {{ color: #7f8c8d; font-size: 12pt; margin-top: 10px; }}
            ul {{ margin-left: 20px; }}
            li {{ margin: 5px 0; }}
            pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 4px; }}
        </style>
        {html}
        """
        
        return html

    def clear_chat(self):
        """대화 내용 초기화"""
        try:
            # 채팅 디스플레이 초기화
            self.chat_display.clear()
            
            # RAG 핸들러의 대화 기록 초기화
            if hasattr(self, 'rag_handler'):
                self.rag_handler.clear_chat_history()
            
            # 시스템 메시지 표시
            self.chat_display.append("[시스템] 대화 내용이 초기화되었습니다.")
            
        except Exception as e:
            QMessageBox.warning(self, "오류", f"대화 내용 초기화 중 오류가 발생했습니다: {str(e)}")

    def setup_rag_handler(self):
        """RAG 핸들러 설정"""
        try:
            # API 키 가져오기
            api_key = self.api_key_input.text().strip()
            
            # RAG 핸들러 초기화
            self.rag_handler = RAGHandler(api_key=api_key)
            
        except Exception as e:
            QMessageBox.warning(self, "오류", f"RAG 핸들러 초기화 중 오류가 발생했습니다: {str(e)}")

    def toggle_api_key_view(self):
        """API 키 표시/숨김 토글"""
        if self.api_key_input.echoMode() == QLineEdit.Password:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)

    def apply_settings(self):
        """설정 적용"""
        try:
            api_key = self.api_key_input.text().strip()
            
            # API 키 저장 여부 확인
            if self.save_api_checkbox.isChecked():
                self.settings.setValue("QGeoChat/api_key", api_key)
            else:
                self.settings.remove("QGeoChat/api_key")
            
            # RAG 핸들러 재초기화
            self.setup_rag_handler()
            
            QMessageBox.information(self, "성공", "설정이 적용되었습니다.")
            
        except Exception as e:
            QMessageBox.warning(self, "오류", f"설정 적용 중 오류가 발생했습니다: {str(e)}")

    def save_api_key(self):
        """API 키 저장"""
        api_key = self.api_key_input.text()
        if self.save_api_checkbox.isChecked():
            self.settings.setValue("QGeoChat/api_key", api_key)
            QMessageBox.information(self, "저장 완료", "API 키가 저장되었습니다.")
        else:
            self.settings.remove("QGeoChat/api_key")
            QMessageBox.information(self, "저장 해제", "저장된 API 키가 제거되었습니다.")

    def get_api_key(self):
        """저장된 API 키 반환"""
        if hasattr(self, 'api_key_input'):
            return self.api_key_input.text()
        return self.settings.value("QGeoChat/api_key", "", type=str)

    def open_file_from_link(self, url):
        """링크 클릭 시 파일 열기 (채팅 내용 유지)"""
        try:
            file_path = url.toLocalFile()
            self.open_file_with_default_editor(file_path)
        except Exception as e:
            QMessageBox.warning(self, "오류", f"파일 열기 실패: {str(e)}")

    def open_file_with_default_editor(self, file_path):
        """기본 편집기로 파일 열기"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            else:  # macOS, Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.call(('open', file_path))
                else:  # Linux
                    subprocess.call(('xdg-open', file_path))
        except Exception as e:
            QMessageBox.warning(self, "오류", f"파일 열기 실패: {str(e)}")

    def save_reference_text(self):
        """참조 텍스트를 파일로 저장"""
        try:
            # 저장 디렉토리 확인/생성
            save_dir = os.path.join(os.path.expanduser('~'), 'QGeoChat_Analysis')
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # 파일 저장
            self.text_file_path = os.path.join(save_dir, 'reference_text.txt')
            with open(self.text_file_path, 'w', encoding='utf-8') as f:
                f.write(self.rag_handler.reference_text)
                
        except Exception as e:
            iface.messageBar().pushMessage("오류", f"텍스트 파일 저장 중 오류: {str(e)}", level=Qgis.Critical)

    def view_reference_text(self):
        """저장된 텍스트 파일을 외부 에디터로 열기"""
        try:
            if hasattr(self, 'text_file_path') and os.path.exists(self.text_file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.text_file_path))
            else:
                iface.messageBar().pushMessage("알림", "텍스트 파일이 아직 생성되지 않았습니다.", 
                                             level=Qgis.Warning)
        except Exception as e:
            iface.messageBar().pushMessage("오류", f"파일 열기 중 오류: {str(e)}", 
                                         level=Qgis.Critical)

    def setup_info_ui(self):
        """정보 탭 UI 설정"""
        layout = QVBoxLayout()
        self.info_tab.setLayout(layout)
        
        # README 내용을 표시할 텍스트 브라우저
        self.info_display = QTextBrowser()
        self.info_display.setOpenExternalLinks(True)  # 외부 링크 클릭 가능
        layout.addWidget(self.info_display)
        
        # README.md 파일 로드
        self.load_readme()

    def load_readme(self):
        """README.md 파일 로드 및 표시"""
        try:
            # README.md 파일 경로
            readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
            
            if os.path.exists(readme_path):
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 마크다운을 HTML로 변환 (선택사항)
                try:
                    import markdown
                    html_content = markdown.markdown(content)
                    self.info_display.setHtml(html_content)
                except ImportError:
                    # markdown 모듈이 없는 경우 텍스트로 표시
                    self.info_display.setPlainText(content)
                    
            else:
                self.info_display.setPlainText("README.md 파일을 찾을 수 없습니다.")
                
        except Exception as e:
            self.info_display.setPlainText(f"README.md 파일 로드 중 오류 발생: {str(e)}")
