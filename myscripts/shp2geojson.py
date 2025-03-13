from qgis.core import *
from qgis.utils import iface
import os
from datetime import datetime

def run_script():
    """현재 활성화된 Shapefile 레이어를 날짜별 디렉토리에 GeoJSON으로 변환하여 저장 (좌표계 설정 포함)"""
    try:
        # 현재 활성화된 레이어 가져오기
        layer = iface.activeLayer()
        if not layer:
            return "활성화된 레이어가 없습니다."

        # 기본 저장 경로 설정 (예: C:/temp/)
        base_directory = "C:/temp"

        # 현재 날짜 및 시간 가져오기 (YYYYMMDD_HHMMSS)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 저장할 디렉토리 경로 생성
        save_directory = os.path.join(base_directory, f"geojson_{current_time}")
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        # 저장할 파일명 자동 설정 (레이어 이름 기반)
        layer_name = layer.name()
        output_path = os.path.join(save_directory, f"{layer_name}.geojson")

        # 레이어의 좌표계 가져오기 (EPSG 코드 확인)
        crs = layer.crs()
        epsg_code = crs.authid()  # "EPSG:5186" 같은 형식으로 반환됨

        # GeoJSON 저장 옵션 설정 (좌표계 포함)
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GeoJSON"
        options.fileEncoding = "utf-8"
        options.ct = QgsCoordinateTransform(layer.crs(), QgsCoordinateReferenceSystem(epsg_code), QgsProject.instance())

        # GeoJSON 형식으로 저장 (좌표계 유지)
        QgsVectorFileWriter.writeAsVectorFormatV2(layer, output_path, QgsCoordinateTransformContext(), options)

        return f"GeoJSON 파일이 저장되었습니다: {output_path} (좌표계: {epsg_code})"
        
    except Exception as e:
        return f"오류 발생: {str(e)}"

if __name__ == '__main__':
    print(run_script())
