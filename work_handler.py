import os
import sys
import importlib.util
from datetime import datetime
from qgis.core import Qgis
from qgis.utils import iface
from io import StringIO

class WorkHandler:
    def __init__(self):
        """작업 핸들러 초기화"""
        
        plugin_dir = os.path.dirname(__file__)
        self.scripts_dir = os.path.join(plugin_dir, 'myscripts')
        
        self.ensure_scripts_directory()
        
        # 현재 선택된 스크립트
        self.current_script = None
        
        # Python 경로에 스크립트 디렉토리 추가
        if self.scripts_dir not in sys.path:
            sys.path.append(self.scripts_dir)

    def ensure_scripts_directory(self):
        """스크립트 디렉토리 확인 및 생성"""
        try:
            if not os.path.exists(self.scripts_dir):
                os.makedirs(self.scripts_dir)
                # 예제 스크립트 생성
                self.create_example_script()
        except Exception as e:
            raise Exception(f"스크립트 디렉토리 생성 중 오류: {str(e)}")

    def create_example_script(self):
        """예제 스크립트 생성"""
        example_content = '''from qgis.core import *
from qgis.utils import iface

def run_script():
    """예제 스크립트"""
    try:
        # 현재 활성화된 레이어 가져오기
        layer = iface.activeLayer()
        if not layer:
            return "활성화된 레이어가 없습니다."
            
        # 레이어 정보 출력
        info = []
        info.append(f"레이어 이름: {layer.name()}")
        info.append(f"피처 개수: {layer.featureCount()}")
        info.append(f"좌표계: {layer.crs().authid()}")
        
        return "\\n".join(info)
        
    except Exception as e:
        return f"오류 발생: {str(e)}"

if __name__ == '__main__':
    print(run_script())
'''
        try:
            with open(os.path.join(self.scripts_dir, 'example.py'), 'w', encoding='utf-8') as f:
                f.write(example_content)
        except Exception as e:
            raise Exception(f"예제 스크립트 생성 중 오류: {str(e)}")

    def get_scripts_list(self):
        """스크립트 파일 목록 반환"""
        try:
            return sorted([f for f in os.listdir(self.scripts_dir) 
                         if f.endswith('.py')])
        except Exception as e:
            raise Exception(f"스크립트 목록 로드 중 오류: {str(e)}")

    def create_new_script(self, filename):
        """새 스크립트 파일 생성"""
        if not filename:
            raise ValueError("파일 이름을 입력해주세요.")
            
        if not filename.endswith('.py'):
            filename += '.py'
            
        filepath = os.path.join(self.scripts_dir, filename)
        
        if os.path.exists(filepath):
            raise ValueError("이미 존재하는 파일 이름입니다.")
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.get_script_template())
            return filename
        except Exception as e:
            raise Exception(f"스크립트 생성 중 오류: {str(e)}")

    def get_script_template(self):
        """기본 스크립트 템플릿 반환"""
        return '''from qgis.core import *
from qgis.utils import iface

def run_script():
    """스크립트 설명을 여기에 작성하세요"""
    try:
        # 여기에 코드를 작성하세요
        layer = iface.activeLayer()
        if not layer:
            return "활성화된 레이어가 없습니다."
            
        # 작업 수행
        
        return "스크립트 실행 완료"
        
    except Exception as e:
        return f"오류 발생: {str(e)}"

if __name__ == '__main__':
    print(run_script())
'''

    def load_script_content(self, filename):
        """스크립트 파일 내용 로드"""
        if not filename:
            return ""
            
        try:
            filepath = os.path.join(self.scripts_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"스크립트 로드 중 오류: {str(e)}")

    def save_script_content(self, filename, content):
        """스크립트 파일 내용 저장"""
        if not filename or not content:
            raise ValueError("파일 이름과 내용이 필요합니다.")
            
        try:
            filepath = os.path.join(self.scripts_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"스크립트 저장 중 오류: {str(e)}")

    def run_script(self, filename):
        """스크립트 실행"""
        if not filename:
            raise ValueError("실행할 스크립트를 선택해주세요.")
            
        try:
            # 출력을 캡처하기 위한 StringIO 객체 생성
            output_buffer = StringIO()
            original_stdout = sys.stdout
            sys.stdout = output_buffer
            
            try:
                # 스크립트 전체 경로
                filepath = os.path.join(self.scripts_dir, filename)
                
                # 모듈 import
                spec = importlib.util.spec_from_file_location(
                    "dynamic_script", filepath)
                module = importlib.util.module_from_spec(spec)
                
                try:
                    spec.loader.exec_module(module)
                    
                    # run_script 함수 실행
                    if hasattr(module, 'run_script'):
                        result = module.run_script()
                        
                        # print 출력 내용 가져오기
                        printed_output = output_buffer.getvalue()
                        
                        # 결과 문자열 처리
                        if isinstance(result, str):
                            result = result.replace('\\n', '\n')
                            result = '\n'.join(line.strip() for line in result.split('\n'))
                        
                        return {
                            'result': result if result else "스크립트가 실행되었습니다.",
                            'printed': printed_output
                        }
                    else:
                        return {
                            'result': "run_script() 함수를 찾을 수 없습니다.",
                            'printed': ""
                        }
                        
                except Exception as e:
                    # 에러 발생 위치 추출
                    import traceback
                    tb = traceback.extract_tb(sys.exc_info()[2])
                    # 스크립트 내에서 발생한 마지막 에러 위치 찾기
                    for frame in reversed(tb):
                        if frame.filename == filepath:
                            error_line = frame.lineno
                            return {
                                'result': f"오류 발생 (라인 {error_line}): {str(e)}",
                                'printed': ""
                            }
                    # 스크립트 내 위치를 찾지 못한 경우
                    return {
                        'result': f"오류 발생: {str(e)}",
                        'printed': ""
                    }
                    
            finally:
                # 원래의 stdout 복구
                sys.stdout = original_stdout
                output_buffer.close()
                
        except Exception as e:
            return {
                'result': f"스크립트 실행 중 오류: {str(e)}",
                'printed': ""
            }

    def delete_script(self, filename):
        """스크립트 파일 삭제"""
        if not filename:
            raise ValueError("삭제할 스크립트를 선택해주세요.")
            
        try:
            filepath = os.path.join(self.scripts_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            raise Exception(f"스크립트 삭제 중 오류: {str(e)}")

    def get_script_info(self, filename):
        """스크립트 파일 정보 반환"""
        if not filename:
            return None
            
        try:
            filepath = os.path.join(self.scripts_dir, filename)
            stats = os.stat(filepath)
            return {
                'name': filename,
                'size': stats.st_size,
                'created': datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            raise Exception(f"스크립트 정보 조회 중 오류: {str(e)}") 