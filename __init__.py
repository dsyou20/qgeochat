# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGeoChat
                                 A QGIS plugin
 QGIS Ollama
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2025-03-02
        copyright            : (C) 2025 by dsyou / elcomtech
        email                : dsyou20@gmail,com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

import subprocess
import sys
from qgis.PyQt.QtWidgets import QMessageBox, QProgressDialog
from qgis.PyQt.QtCore import Qt
import pkg_resources
import importlib



from .QGeoChat import QGeoChat

def install_package(package, version):
    """패키지 설치"""
    try:
        python_exe = sys.executable
        subprocess.check_call(
            [python_exe, "-m", "pip", "install", version],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # 설치 후 모듈 리로드 시도
        if package in sys.modules:
            importlib.reload(sys.modules[package])
        return True
    except Exception as e:
        return str(e)

def check_dependencies():
    """필요한 패키지들을 확인하고 설치"""
    required_packages = {
        'openai': {'version': 'openai>=1.0.0', 'display_name': 'OpenAI API'},
        'pypdf': {'version': 'pypdf', 'display_name': 'PDF 처리'},
        'langchain': {'version': 'langchain>=0.1.0', 'display_name': 'LangChain'},
        'langchain-openai': {'version': 'langchain-openai', 'display_name': 'LangChain OpenAI'},
        'faiss-cpu': {'version': 'faiss-cpu', 'display_name': '벡터 데이터베이스'},
        'reportlab': {'version': 'reportlab', 'display_name': 'PDF 생성'},
        'geopandas': {'version': 'geopandas', 'display_name': 'GeoPandas'}
    }
    
    missing_packages = []
    for package, info in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append((package, info))
    
    if not missing_packages:
        return True
        
    # 사용자에게 설치 확인
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("패키지 설치 필요")
    msg.setText("QGIS Ollama 플러그인을 사용하기 위해 필요한 패키지를 설치해야 합니다.")
    
    details = "설치할 패키지:\n"
    for package, info in missing_packages:
        details += f"- {info['display_name']} ({package})\n"
    msg.setDetailedText(details)
    
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.Yes)
    
    if msg.exec_() != QMessageBox.Yes:
        raise Exception("사용자가 패키지 설치를 취소했습니다.")
    
    # 패키지 설치
    error_messages = []
    for package, info in missing_packages:
        result = install_package(package, info['version'])
        if result is not True:
            error_messages.append(f"{package}: {result}")
    
    if error_messages:
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setWindowTitle("설치 오류")
        error_msg.setText("일부 패키지 설치에 실패했습니다.")
        error_msg.setDetailedText("\n".join(error_messages))
        error_msg.exec_()
        raise Exception("패키지 설치 실패")
    
    return True

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load QGeoChat class from file QGeoChat.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    try:
        #if check_dependencies():
        if True:
            from .QGeoChat import QGeoChat
            return QGeoChat(iface)
    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("QGIS Ollama 플러그인 오류")
        msg.setText("플러그인을 로드할 수 없습니다.")
        msg.setInformativeText(str(e))
        msg.exec_()
        # 플러그인 클래스 대신 더미 클래스 반환
        return DummyPlugin()

class DummyPlugin:
    """패키지 설치 실패 시 사용할 더미 플러그인 클래스"""
    def __init__(self):
        self.iface = None
        
    def initGui(self):
        """더미 initGui 메서드"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("QGIS Ollama 플러그인")
        msg.setText("필요한 패키지가 설치되지 않아 플러그인을 사용할 수 없습니다.")
        msg.setInformativeText("플러그인을 다시 활성화하여 패키지 설치를 시도해주세요.")
        msg.exec_()
        
    def unload(self):
        """더미 unload 메서드"""
        pass

# 필수 패키지 정의
REQUIRED_PACKAGES = {
    'langchain': {'version': 'langchain', 'display_name': 'LangChain'},
    'langchain_openai': {'version': 'langchain-openai', 'display_name': 'LangChain OpenAI'},
    'openai': {'version': 'openai', 'display_name': 'OpenAI'},
    'faiss-cpu': {'version': 'faiss-cpu', 'display_name': 'FAISS-CPU'},
    'geopandas': {'version': 'geopandas', 'display_name': 'GeoPandas'},
    'pandas': {'version': 'pandas', 'display_name': 'Pandas'},
    'numpy': {'version': 'numpy', 'display_name': 'NumPy'}
}

# 의존성 정의
dependencies = {
    'PyPDF2': {'module': 'PyPDF2', 'version': 'PyPDF2'}
}

# 의존성 체크 함수
def check_dependencies():
    try:
        import pkg_resources
        
        for package_name, details in dependencies.items():
            try:
                pkg_resources.require(details['version'])
            except pkg_resources.DistributionNotFound:
                return False, f"{package_name} 모듈이 설치되어 있지 않습니다."
            except pkg_resources.VersionConflict:
                return False, f"{package_name} 모듈의 버전이 맞지 않습니다."
                
        return True, "모든 의존성이 설치되어 있습니다."
    except Exception as e:
        return False, str(e)
