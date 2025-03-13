from qgis.core import *
from qgis.utils import iface
import pandas as pd
import geopandas as gpd
from mgwr.gwr import GWR   # pip install mgwr
from mgwr.sel_bw import Sel_BW
from shapely.geometry import Point

def run_script():
    """GWR 모델을 적용하여 결과를 메모리 레이어로 저장하고 프로젝트에 추가하는 코드"""
    try:
        # 활성화된 레이어 가져오기
        layer = iface.activeLayer()
        if not layer:
            return "활성화된 레이어가 없습니다."

        # 레이어를 GeoDataFrame으로 변환
        features = [feat for feat in layer.getFeatures()]
        attributes = [feat.attributes() for feat in features]
        columns = [field.name() for field in layer.fields()]
        gdf = gpd.GeoDataFrame(attributes, columns=columns, 
                               geometry=[Point(feat.geometry().asPoint()) for feat in features])

        print("xx")

        # 종속변수와 독립변수 설정        
        # 2. 필요한 열 선택 (가격을 종속 변수로 사용)
        y = gdf['price'].values.reshape((-1, 1))  # 종속 변수 (가격)

        print("xx")

        # 3. 독립 변수 설정
        X = gdf[['review_sco', 'bedrooms', 'bathrooms', 'beds']].values  # 독립 변수들 (리뷰 점수, 침실 수, 욕실 수, 침대 수)

        print("xx")

        # 좌표 추출 (QgsPointXY -> tuple로 변환)
        coords = [(geom.x, geom.y) for geom in gdf.geometry]

        print("xx4")

        # 대역폭 선택
        selector = Sel_BW(coords, y, X)
        bw = selector.search()

        # GWR 모델 적합
        model = GWR(coords, y, X, bw)
        results = model.fit()

        # 결과 출력
        print(results.summary())

        # GWR 결과 (예: 예측값) 추출
        gwr_predictions = results.predictions.flatten()

        # 메모리 레이어 생성
        crs = layer.crs()  # 원본 레이어의 CRS 사용
        new_layer = QgsVectorLayer("Point?crs=" + crs.toWkt(), "GWR Predictions", "memory")
        provider = new_layer.dataProvider()

        # 필드 추가 (기존 필드 + GWR 예측값)
        provider.addAttributes(layer.fields())  # 기존 필드 추가
        provider.addAttributes([QgsField("GWR_predictions", QVariant.Double)])  # GWR 예측값 필드 추가
        new_layer.updateFields()

        # 피쳐 추가 (기존 피쳐 + GWR 예측값)
        for i, feature in enumerate(features):
            new_feature = QgsFeature()
            new_feature.setGeometry(feature.geometry())  # 기존 기하정보
            new_feature.setAttributes(feature.attributes() + [gwr_predictions[i]])  # 기존 속성 + GWR 예측값
            provider.addFeature(new_feature)

        # 프로젝트에 메모리 레이어 추가
        QgsProject.instance().addMapLayer(new_layer)

        return f"GWR 분석 완료 및 메모리 레이어로 결과 저장: {new_layer.name()}"

    except Exception as e:
        return f"오류 발생: {str(e)}"

if __name__ == '__main__':
    print(run_script())
