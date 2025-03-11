from qgis.core import *
from qgis.utils import iface

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY
)
from PyQt5.QtCore import QVariant

def run_script():
    # 도시 이름과 위도, 경도 정보
    cities = {
        '서울': (37.5665, 126.9780),   # 서울 (위도, 경도)
        '부산': (35.1796, 129.0756),   # 부산
        '대전': (36.3504, 127.3845),   # 대전
        '광주': (35.1595, 126.8526),   # 광주
        '대구': (35.8704, 128.5916)    # 대구
    }

    # 포인트 벡터 레이어 생성 (단일 지오메트리 포인트 레이어)
    layer = QgsVectorLayer('Point?crs=EPSG:4326', 'City Points', 'memory')
    
    # 속성 테이블 정의
    provider = layer.dataProvider()
    provider.addAttributes([QgsField('City', QVariant.String)])
    layer.updateFields()
    
    # 각 도시 포인트에 대한 피처 생성
    for city, (lat, lon) in cities.items():
        feature = QgsFeature()
        point = QgsPointXY(lon, lat)  # 위도, 경도 순서로 포인트 생성
        feature.setGeometry(QgsGeometry.fromPointXY(point))
        feature.setAttributes([city])  # 도시 이름을 속성으로 추가
        provider.addFeature(feature)
    
    # 레이어 프로젝트에 추가
    QgsProject.instance().addMapLayer(layer)
    
    # 레이어 스타일 (포인트 마커 설정)
    symbol = layer.renderer().symbol()
    symbol.setColor('red')  # 빨간색으로 포인트 표시
    symbol.setSize(5)  # 포인트 크기 설정
    
    return layer



if __name__ == '__main__':
    print(run_script())
