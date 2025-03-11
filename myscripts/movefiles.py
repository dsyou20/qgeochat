from qgis.core import *
from qgis.utils import iface

import os
import shutil

def move(src_folder, dest_folder):
    # source 폴더와 destination 폴더가 존재하는지 확인
    if not os.path.exists(src_folder):
        print(f"Source folder {src_folder} does not exist.")
        return

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # 목적지 폴더가 없다면 생성

    # source 폴더에서 모든 파일을 확인
    for filename in os.listdir(src_folder):
        # 파일 경로 만들기
        file_path = os.path.join(src_folder, filename)

        # 파일이 .csv 확장자라면 목적지 폴더로 이동
        if os.path.isfile(file_path) and filename.endswith('.csv'):
            shutil.move(file_path, os.path.join(dest_folder, filename))
            print(f"Moved: {filename}")

def run_script():
    # 사용 예시
    src_folder = 'C:\\Users\\dsyou\\Documents'  # 소스 폴더 경로
    dest_folder = 'C:\\Users\\dsyou\\Documents\\out'  # 목적지 폴더 경로

    move(src_folder, dest_folder)


if __name__ == '__main__':

    print(run_script())
