from qgis.core import *
from qgis.utils import iface
import os
import processing
from datetime import datetime
from PyQt5.QtCore import QVariant  # Import QVariant for fields

def run_script():
    """현재 활성화된 SHP의 피처를 기준으로 다른 레이어들의 피쳐 개수만큼 클립하여 GeoTIFF와 GeoJSON으로 저장하는 기능"""
    try:
        # 현재 활성화된 레이어 가져오기
        active_layer = iface.activeLayer()

        if active_layer is None:
            return "활성화된 레이어가 없습니다."

        # 현재 날짜와 시간 구하기 (년, 월, 일, 시, 분, 초)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 저장할 폴더 경로 지정
        target_root = "C:/temp"
        storage_folder = os.path.join(target_root, f"clipped_{current_time}")

        # 폴더가 존재하지 않으면 생성
        if not os.path.exists(storage_folder):
            os.makedirs(storage_folder)

        # 활성화된 레이어가 벡터 레이어인 경우
        if active_layer.type() == QgsMapLayer.VectorLayer:
            # 피쳐 개수만큼 반복하여 클립 처리
            for idx, feature in enumerate(active_layer.getFeatures(), start=1):
                # 각 피쳐의 경계 가져오기 (geometry를 사용하여 피쳐의 경계 추출)
                geometry = feature.geometry()

                # 다른 벡터 및 래스터 레이어를 클립하여 저장
                for other_layer in QgsProject.instance().mapLayers().values():
                    # 현재 체크된 레이어만 처리 (isVisible() 체크)
                    if other_layer != active_layer:
                        # 레이어가 현재 보이는 상태인지 확인
                        layer_node = QgsProject.instance().layerTreeRoot().findLayer(other_layer.id())
                        if layer_node is not None and layer_node.isVisible():
                            # 벡터 레이어 처리
                            if other_layer.type() == QgsMapLayer.VectorLayer:
                                # 피쳐 번호를 4자리로 표시
                                output_geojson = os.path.join(storage_folder, f"{other_layer.name()}_clipped_{idx:04d}.geojson")

                                # 공간 인덱스 생성
                                spatial_index = QgsSpatialIndex(active_layer.getFeatures())

                                # other_layer의 각 피쳐에 대해 클립 수행
                                clipped_features = []

                                for other_feature in other_layer.getFeatures():
                                    # active_layer의 각 피쳐와 교차 여부 확인
                                    intersecting_ids = spatial_index.intersects(other_feature.geometry().boundingBox())

                                    for feature_id in intersecting_ids:
                                        active_feature = active_layer.getFeature(feature_id)
                                        clipped_geom = other_feature.geometry().intersection(geometry)  # Feature geometry of active_layer used
                                        if not clipped_geom.isEmpty():
                                            clipped_features.append({
                                                'geometry': clipped_geom,
                                                'attributes': other_feature.attributes()
                                            })

                                # 클립된 피쳐들을 새로운 GeoDataFrame에 저장
                                if clipped_features:
                                    # 새로운 벡터 레이어로 저장
                                    crs = active_layer.crs()  # active_layer의 CRS를 사용
                                    clipped_layer = QgsVectorLayer('Polygon?crs=' + crs.toWkt(), 'clipped_layer', 'memory')
                                    provider = clipped_layer.dataProvider()

                                    # 필드 정의
                                    provider.addAttributes(other_layer.fields())
                                    clipped_layer.updateFields()

                                    # 클립된 피쳐들 추가
                                    for feat in clipped_features:
                                        clipped_feature = QgsFeature()
                                        clipped_feature.setGeometry(feat['geometry'])  # geometry 설정
                                        clipped_feature.setAttributes(feat['attributes'])  # attributes 설정
                                        provider.addFeature(clipped_feature)

                                    # 클립된 레이어를 GeoJSON 파일로 저장
                                    clipped_layer.dataProvider().createSpatialIndex()
                                    QgsVectorFileWriter.writeAsVectorFormat(clipped_layer, output_geojson, 'utf-8', crs, 'GeoJSON')
                                    print(f"피쳐 {idx:04d} 클립된 벡터 레이어를 GeoJSON 파일로 저장: {output_geojson}")

                            # 래스터 레이어 처리
                            elif other_layer.type() == QgsMapLayer.RasterLayer:
                                # 피쳐 번호를 4자리로 표시
                                output_tif = os.path.join(storage_folder, f"{other_layer.name()}_clipped_{idx:04d}.tif")
                                
                                # active_layer의 CRS를 사용하여 래스터 클립
                                crs = active_layer.crs()

                                # Create a temporary mask layer with the geometry of the active layer's feature
                                mask_layer = QgsVectorLayer('Polygon?crs=' + crs.toWkt(), 'mask_layer', 'memory')
                                provider = mask_layer.dataProvider()
                                provider.addAttributes([QgsField("id", QVariant.Int)])
                                mask_layer.updateFields()

                                # Create a feature for the mask layer (using the geometry of the active layer's feature)
                                mask_feature = QgsFeature()
                                mask_feature.setGeometry(geometry)  # Set the geometry of the mask feature to be the same as the active layer's feature
                                mask_feature.setAttributes([idx])  # Add any additional attributes if needed
                                provider.addFeature(mask_feature)

                                # Run the clipping with the mask layer (active_layer's feature geometry)
                                processing.run("gdal:cliprasterbymasklayer", {
                                    'INPUT': other_layer,
                                    'MASK': mask_layer,
                                    'OUTPUT': output_tif,
                                    'TARGET_CRS': crs.toWkt(),  # active_layer의 CRS를 적용
                                })
                                print(f"피쳐 {idx:04d} 클립된 래스터 레이어를 TIFF 파일로 저장: {output_tif}")

        else:
            return "활성화된 레이어는 벡터 레이어여야 합니다."

        return "스크립트 실행 완료"
    
    except Exception as e:
        return f"오류 발생: {str(e)}"

if __name__ == '__main__':
    print(run_script())
