from qgis.core import *
from qgis.utils import iface
from PyQt5.QtCore import QVariant
import math

def run_script():
    """활성 레이어의 선택된 객체에 맞춰 레벨 18 격자를 생성하여 신규 레이어를 추가합니다."""
    try:
        # 활성 레이어 가져오기
        layer = iface.activeLayer()
        if not layer:
            print("활성화된 레이어가 없습니다.")
            return

        # 벡터 레이어인지 확인
        if layer.type() != QgsMapLayer.VectorLayer:
            print("벡터 레이어가 아닙니다.")
            return

        print( layer )

        # 선택된 객체가 있는지 확인
        selected_features = layer.selectedFeatures()
        if not selected_features:
            print("선택된 객체가 없습니다.")
            return

        # 선택된 객체의 경계 정보 가져오기
        bounding_box = selected_features[0].geometry().boundingBox()

        # 격자 크기 
        grid_size = 30  # meter

        # 새로운 레이어 생성
        fields = QgsFields()
        fields.append(QgsField("ID", QVariant.Int))
        fields.append(QgsField("geometry", QVariant.String))

        grid_layer = QgsVectorLayer("Polygon?crs=EPSG:5186", "Grid Layer", "memory")
        grid_layer.dataProvider().addAttributes(fields)
        grid_layer.updateFields()

        # 격자 생성
        grid_features = []
        x_start = math.floor(bounding_box.xMinimum() / grid_size) * grid_size
        y_start = math.floor(bounding_box.yMinimum() / grid_size) * grid_size
        x_end = math.ceil(bounding_box.xMaximum() / grid_size) * grid_size
        y_end = math.ceil(bounding_box.yMaximum() / grid_size) * grid_size

        # 격자 생성 및 피처 추가
        x = x_start
        while x < x_end:
            y = y_start
            while y < y_end:
                # 격자 사각형 생성
                points = [
                    QgsPointXY(x, y),
                    QgsPointXY(x + grid_size, y),
                    QgsPointXY(x + grid_size, y + grid_size),
                    QgsPointXY(x, y + grid_size),
                    QgsPointXY(x, y)
                ]
                polygon = QgsGeometry.fromPolygonXY([points])
                feature = QgsFeature()
                feature.setGeometry(polygon)
                feature.setAttributes([len(grid_features), f"({x},{y})"])
                grid_features.append(feature)
                y += grid_size
            x += grid_size

        # 격자 피처 레이어에 추가
        grid_layer.dataProvider().addFeatures(grid_features)

        # 맵에 새로운 레이어 추가
        QgsProject.instance().addMapLayer(grid_layer)

        print("격자 레이어가 생성되어 추가되었습니다.")

    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == '__main__':
    run_script()

