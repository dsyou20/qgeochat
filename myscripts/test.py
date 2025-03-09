from qgis.core import *
from qgis.utils import iface

def run_script():
    """스크립트 설명을 여기에 작성하세요"""
    try:
        # 여기에 코드를 작성하세요
        layer = iface.activeLayer()
        if not layer:
            return "활성화된 레이어가 없습니다."
            
        # 작업 수행
        
        return "스크립트 실행 완료!"
        
    except Exception as e:
        return f"오류 발생: {str(e)}"

if __name__ == '__main__':
    print(run_script())
