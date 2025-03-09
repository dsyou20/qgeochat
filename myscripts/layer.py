from qgis.core import *
from qgis.utils import iface

def run_script():
    """활성 레이어의 정보를 출력합니다."""
    try:
        # 활성 레이어 가져오기
        layer = iface.activeLayer()
        if not layer:
            print("활성화된 레이어가 없습니다.")
            return

        
        # 레이어 정보 출력
        print(f"레이어 이름: {layer.name()}")
        print(f"레이어 타입: {'벡터' if layer.type() == QgsMapLayer.VectorLayer else '래스터'}")
        
        if layer.type() == QgsMapLayer.VectorLayer:
            print(f"도형 유형: {layer.geometryType()}")
            print(f"피처 수: {layer.featureCount()}")
            print(f"필드 수: {len(layer.fields())}")
            for field in layer.fields():
                print(f"필드 이름: {field.name()}, 유형: {field.typeName()}")

        
        elif layer.type() == QgsMapLayer.RasterLayer:
            print(f"밴드 수: {layer.bandCount()}")
            print(f"너비: {layer.width()} 픽셀")
            print(f"높이: {layer.height()} 픽셀")

        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == '__main__':
    run_script()