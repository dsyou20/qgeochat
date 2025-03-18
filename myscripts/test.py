import importlib

def check(required_packages):
    # 필요한 패키지 설치 여부 확인
    missing_packages = []
    
    for package_req in required_packages:
        # 버전 정보가 있는 경우 패키지명만 추출
        package_name = package_req.split('>=')[0].split('==')[0].strip()
        
        try:
            print( "package_name: ", package_name )
            module = importlib.import_module(package_name)
            print( "package_name2: ", package_name )
            
            # pdfgpt 특별 처리
            if package_name == 'pdfgpt':
                import pdfgpt
                if pdfgpt.__version__ != '0.2.2':
                    missing_packages.append('pdfgpt==0.2.2')
            # 버전 체크가 필요한 경우
            elif '>=' in package_req or '==' in package_req:
                if hasattr(module, '__version__'):
                    current_version = module.__version__
                    required_version = package_req.split('>=')[-1].split('==')[-1].strip()
                    
                    print(package_name, current_version)
                    print(package_name, required_version)

                    # _version_satisfies 함수가 구현되어 있지 않으므로 간단한 버전 비교로 대체
                    if '>=' in package_req:
                        if current_version < required_version:
                            missing_packages.append(package_req)
                    else:  # == 인 경우
                        if current_version != required_version:
                            missing_packages.append(package_req)

        except ImportError:
            print("no pakg", package_req )
            missing_packages.append(package_req)

    print(missing_packages)

def run_script():
    check(['openai>=1.0.0', 'langchain==0.3.19', 'langchain_openai==0.3.7', 'faiss==1.10.0', 
           'reportlab==4.3.1', 'geopandas==0.11.1', 'PyPDF2', 'langchain_community'])

# Run the script to check missing packages
run_script()
