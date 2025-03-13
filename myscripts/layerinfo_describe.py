from qgis.core import *
from qgis.utils import iface
import pandas as pd
import geopandas as gpd

def run_script():
    """활성 레이어의 파일 경로를 출력하고 열 값의 통계치를 출력합니다."""
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
                print(f"\n파일 경로: {data_provider.dataSourceUri()}")
                print(f"레이어 이름: {layer.name()}")
                
                # 피쳐 개수를 세는 방법 수정 (QgsFeatureIterator에 대해 len()을 사용할 수 없음)
                features = list(layer.getFeatures())  # QgsFeatureIterator를 리스트로 변환
                print(f"피쳐 수: {len(features)}")  # 이제 피쳐 개수를 셀 수 있음

                print(f"좌표계: {layer.crs().authid()}")
                print(f"열 이름: {', '.join(layer.fields().names())}")

                path = data_provider.dataSourceUri()

                gdf = gpd.read_file(path)

                # 수치형 열에 대한 기본 통계 출력
                print("\n수치형 열 값의 통계치:")
                numeric_columns = gdf.select_dtypes(include=['number']).columns
                if numeric_columns.any():
                    print(gdf[numeric_columns].describe())  # 수치형 열에 대한 통계 출력
                else:
                    print("수치형 열이 없습니다.")

                # 문자형 열에 대한 상위 5개 빈도 출력
                print("\n문자형 열에 대한 상위 5개 빈도수:")
                for column in gdf.select_dtypes(include=['object']).columns:
                    print(f"\n{column} 값의 상위 5개 빈도수:")
                    top_5 = gdf[column].value_counts().head(5)
                    if not top_5.empty:
                        print(top_5)
                    else:
                        print("빈도수가 없습니다.")
                    print("-" * 30)  # 구분선

            else:
                print("데이터 제공자를 찾을 수 없습니다.")
        else:
            print("지원되지 않는 레이어 타입입니다.")

    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == '__main__':
    run_script()
