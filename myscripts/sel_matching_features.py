from qgis.core import *
from qgis.utils import iface
from PyQt5.QtCore import QVariant  # Import QVariant for field types

def run_script():
    """선택된 레이어에서 feature을 출력하여 feature가 여러 조건을 만족하는 것만을 골라서, 새로운 레이어로 만들어줘"""
    try:
        # 활성화된 레이어 가져오기
        layer = iface.activeLayer()
        if not layer:
            return "활성화된 레이어가 없습니다."
        
        # 레이어의 모든 필드와 데이터 타입 출력
        print("레이어 필드 및 데이터 타입:")
        for field in layer.fields():
            print(f"Field Name: {field.name()}, Type: {field.typeName()}")
        
        # 필터링할 조건 설정 (여러 필드와 조건)
        """
        conditions = [
            {'field': 'field_name_1', 'value': ['value1', 'value2', 'value3'], 'operator': 'in'},  # field_name_1 IN ['value1', 'value2', 'value3']
            {'field': 'field_name_2', 'value': 'value2', 'operator': '!='},  # field_name_2 != 'value2'
            {'field': 'field_name_3', 'value': (10, 20), 'operator': 'between'},  # field_name_3 BETWEEN 10 AND 20
            {'field': 'field_name_4', 'value': 'doncare', 'operator': 'dontcare'}  # "don't care" 조건
        ]
        """
        
        conditions = [
            {'field': 'id', 'value': 'doncare', 'operator': 'dontcare'}  # "don't care" 조건
        ]
        
        # 선택할 피쳐 필터링
        filtered_features = []
        
        for feature in layer.getFeatures():
            is_match = True  # 피쳐가 모든 조건을 만족하는지 확인
            
            # 각 조건을 확인
            for condition in conditions:
                field_value = feature[condition['field']]
                
                if condition['operator'] == '==':
                    if field_value != condition['value']:
                        is_match = False
                        break
                elif condition['operator'] == '!=':
                    if field_value == condition['value']:
                        is_match = False
                        break
                elif condition['operator'] == 'between':
                    if not (condition['value'][0] <= field_value <= condition['value'][1]):
                        is_match = False
                        break
                elif condition['operator'] == 'in':
                    # 'in' 조건: field_value가 condition['value'] 리스트에 있는지 확인
                    if field_value not in condition['value']:
                        is_match = False
                        break
                elif condition['operator'] == 'dontcare':
                    # "don't care" 조건: 해당 필드 값을 무시하고 처리
                    # 이 경우 is_match는 그대로 유지 (필터링하지 않음)
                    pass
            
            # 조건을 만족하는 피쳐를 리스트에 추가
            if is_match:
                filtered_features.append(feature)
        
        if not filtered_features:
            return "필터링된 피쳐가 없습니다."
        
        # gen_new_layer 플래그 설정
        gen_new_layer = True  # 이 값을 True로 설정하면 새로운 레이어가 생성됨. False일 경우 피쳐 개수만 출력
        
        if gen_new_layer:
            # 필터링된 피쳐로 새로운 메모리 레이어 생성
            crs = layer.crs()  # 기존 레이어의 CRS를 사용
            new_layer = QgsVectorLayer(f"Polygon?crs={crs.toWkt()}", "Filtered Layer", "memory")
            provider = new_layer.dataProvider()
            
            # 기존 레이어에서 사용한 필드 추가
            provider.addAttributes(layer.fields())
            new_layer.updateFields()
            
            # 필터링된 피쳐들 새로운 레이어에 추가
            provider.addFeatures(filtered_features)
            
            # 새로운 레이어를 프로젝트에 추가
            QgsProject.instance().addMapLayer(new_layer)
            
            # 작업 완료 메시지
            return f"필터링된 피쳐를 새 레이어로 저장했습니다. 레이어 이름: {new_layer.name()}"
        else:
            # 필터링된 피쳐 개수만 출력
            return f"필터링된 피쳐의 개수: {len(filtered_features)}"
        
    except Exception as e:
        return f"오류 발생: {str(e)}"

if __name__ == '__main__':
    print(run_script())
