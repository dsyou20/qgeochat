from qgis.core import *
from qgis.utils import iface

def run_script():
    """활성레이어 그리드 정보를 가지고 특징 레스터 레이어와 특징 shp 레이어의 이미지 패치와 객체정보를 geojson으로 만드는 방법, 또다른 json파일에 이미지의 원좌표값을 적어줘."""
    try:

        
        return "스크립트 실행 완료"
        
    except Exception as e:
        return f"오류 발생: {str(e)}"

if __name__ == '__main__':
    print(run_script())
