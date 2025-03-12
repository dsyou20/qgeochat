from qgis.core import *
from qgis.utils import iface
import geopandas as gpd

def run_script():
    """활성 레이어의 파일 경로를 출력합니다."""
    try:
        # 활성 레이어 가져오기
        layer = iface.activeLayer()
        if not layer:
            print("활성화된 레이어가 없습니다.")
            return

        # 레이어 파일 경로 출력
        if layer.type() == QgsMapLayer.VectorLayer or layer.type() == QgsMapLayer.RasterLayer:
            data_provider = layer.dataProvider()
            if data_provider:
                print(f"파일 경로: {data_provider.dataSourceUri()}")

                path = data_provider.dataSourceUri()

                gdf = gpd.read_file(path)

                # 레이어 정보 출력
                print(f"레이어 이름: {layer.name()}")
                print(f"피처 수: {len(gdf)}")
                print(f"좌표계: {gdf.crs}")
                print(f"열 이름: {gdf.columns.tolist()}")

            else:
                print("데이터 제공자를 찾을 수 없습니다.")
        else:
            print("지원되지 않는 레이어 타입입니다.")

    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == '__main__':
    run_script()