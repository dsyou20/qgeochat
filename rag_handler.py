from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import tempfile
from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry, QgsWkbTypes, QgsDistanceArea, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsProject
from qgis.core import QgsProject
import platform
import json
import geopandas as gpd
import pandas as pd
import numpy as np
from qgis.core import QgsVectorLayer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
from qgis.core import QgsSettings

from langchain.chains.conversational_retrieval.prompts import QA_PROMPT

class RAGHandler:
    def __init__(self):
        """초기화"""
        self.gdf = None
        self.vector_store = None
        self.current_text_path = None
        self.reference_text = None
        self.chat_history = []
        self.chain = None
        
        # QSettings에서 API 키 읽기
        settings = QgsSettings()
        self.api_key = settings.value("QOllama/api_key", "", type=str)
        

    def register_korean_font(self):
        """한글 폰트 등록"""
        try:
            # 운영체제별 기본 한글 폰트 경로
            if platform.system() == 'Windows':
                font_paths = [
                    'C:/Windows/Fonts/malgun.ttf',  # 맑은 고딕
                    'C:/Windows/Fonts/gulim.ttc',   # 굴림
                    'C:/Windows/Fonts/batang.ttc'   # 바탕
                ]
            elif platform.system() == 'Darwin':  # macOS
                font_paths = [
                    '/System/Library/Fonts/AppleGothic.ttf',
                    '/Library/Fonts/AppleGothic.ttf'
                ]
            else:  # Linux
                font_paths = [
                    '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
                    '/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf'
                ]

            # 폰트 파일 존재 확인 및 등록
            font_registered = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        if font_path.endswith('malgun.ttf'):
                            pdfmetrics.registerFont(TTFont('Malgun', font_path))
                            font_registered = True
                            break
                        elif font_path.endswith('gulim.ttc'):
                            pdfmetrics.registerFont(TTFont('Gulim', font_path))
                            font_registered = True
                            break
                        elif font_path.endswith('AppleGothic.ttf'):
                            pdfmetrics.registerFont(TTFont('AppleGothic', font_path))
                            font_registered = True
                            break
                        elif font_path.endswith('NanumGothic.ttf'):
                            pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
                            font_registered = True
                            break
                        elif font_path.endswith('UnDotum.ttf'):
                            pdfmetrics.registerFont(TTFont('UnDotum', font_path))
                            font_registered = True
                            break
                    except Exception as e:
                        print(f"Font registration error for {font_path}: {str(e)}")
                        continue

            if not font_registered:
                print("Warning: No Korean font could be registered")
        except Exception as e:
            print(f"Font registration error: {str(e)}")

    def get_korean_font_name(self):
        """등록된 한글 폰트 이름 반환"""
        for font_name in ['Malgun', 'Gulim', 'AppleGothic', 'NanumGothic', 'UnDotum']:
            if font_name in pdfmetrics.getRegisteredFontNames():
                return font_name
        return 'Helvetica'  # 폴백 폰트


    def _extract_coordinates(self, geometry):
        """도형에서 모든 좌표 추출"""
        coords = []
        if geometry['type'] == 'Point':
            coords.append(tuple(geometry['coordinates'][:2]))
        elif geometry['type'] in ['LineString', 'MultiPoint']:
            coords.extend([tuple(c[:2]) for c in geometry['coordinates']])
        elif geometry['type'] in ['Polygon', 'MultiLineString']:
            for ring in geometry['coordinates']:
                coords.extend([tuple(c[:2]) for c in ring])
        elif geometry['type'] == 'MultiPolygon':
            for polygon in geometry['coordinates']:
                for ring in polygon:
                    coords.extend([tuple(c[:2]) for c in ring])
        return coords

    def qgis_layer_to_geopandas(self, layer):
        """QGIS 레이어를 GeoPandas DataFrame으로 변환"""
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        temp_gpkg = os.path.join(temp_dir, 'temp.gpkg')
        
        # 레이어를 GeoPackage로 저장
        error = QgsVectorFileWriter.writeAsVectorFormat(
            layer,
            temp_gpkg,
            'UTF-8',
            driverName='GPKG'
        )
        
        if error[0] != QgsVectorFileWriter.NoError:
            raise Exception(f"GeoPackage 저장 오류: {error[0]}")
        
        # GeoPandas로 읽기
        gdf = gpd.read_file(temp_gpkg)
        
        # 임시 파일 삭제
        try:
            os.remove(temp_gpkg)
        except:
            pass
            
        return gdf

    def analyze_geodataframe(self, gdf):
        """GeoPandas DataFrame 분석"""
        analysis = ["# 공간 데이터 분석 보고서\n"]
        
        # 1. 기본 정보
        analysis.append("## 기본 정보")
        analysis.append(f"- 전체 레코드 수: {len(gdf)}")
        analysis.append(f"- 좌표계: {gdf.crs}")
        analysis.append(f"- 도형 타입: {gdf.geom_type.unique().tolist()}\n")
        
        # 2. 속성 정보
        analysis.append("## 속성 정보")
        for column in gdf.columns:
            if column != 'geometry':
                dtype = gdf[column].dtype
                null_count = gdf[column].isnull().sum()
                unique_count = gdf[column].nunique()
                
                analysis.append(f"### {column}")
                analysis.append(f"- 데이터 타입: {dtype}")
                analysis.append(f"- Null 값 개수: {null_count}")
                analysis.append(f"- 고유값 개수: {unique_count}")
                
                if np.issubdtype(dtype, np.number):
                    stats = gdf[column].describe()
                    analysis.append(f"- 최소값: {stats['min']:.2f}")
                    analysis.append(f"- 최대값: {stats['max']:.2f}")
                    analysis.append(f"- 평균값: {stats['mean']:.2f}")
                    analysis.append(f"- 중앙값: {stats['50%']:.2f}")
                elif dtype == 'object':
                    value_counts = gdf[column].value_counts().head(5)
                    if not value_counts.empty:
                        analysis.append("- 상위 5개 값:")
                        for val, count in value_counts.items():
                            analysis.append(f"  - {val}: {count}개")
                analysis.append("")
        
        # 3. 공간 정보
        analysis.append("## 공간 정보")
        bounds = gdf.total_bounds
        analysis.append(f"- X 범위: {bounds[0]:.6f} ~ {bounds[2]:.6f}")
        analysis.append(f"- Y 범위: {bounds[1]:.6f} ~ {bounds[3]:.6f}")
        
        # 도형 통계
        for geom_type in gdf.geom_type.unique():
            type_gdf = gdf[gdf.geom_type == geom_type]
            analysis.append(f"\n### {geom_type} 통계")
            analysis.append(f"- 개수: {len(type_gdf)}개")
            
            if geom_type in ['LineString', 'MultiLineString']:
                lengths = type_gdf.length
                analysis.append(f"- 총 길이: {lengths.sum():.2f}")
                analysis.append(f"- 평균 길이: {lengths.mean():.2f}")
            elif geom_type in ['Polygon', 'MultiPolygon']:
                areas = type_gdf.area
                analysis.append(f"- 총 면적: {areas.sum():.2f}")
                analysis.append(f"- 평균 면적: {areas.mean():.2f}")
                
        # 4. 속성 정보 추가
        analysis.append("## 속성 정보")
        for column in gdf.columns:
            if column != 'geometry':
                analysis.append(f"### {column}")
                analysis.append(f"- 데이터 타입: {gdf[column].dtype}")
                
        # 5. 개별 피처 정보
        analysis.extend([
            "## 개별 피처 정보",
            "### 피처별 상세 데이터"
        ])
        
        for idx, row in self.gdf.iterrows():
            geom = row['geometry']
            
            # 피처 헤더 추가
            analysis.extend([
                f"\n#### 피처 {idx + 1}"
            ])
            
            # 모든 속성 정보 추가
            analysis.append("- 속성 정보:")
            for column in self.gdf.columns:
                if column != 'geometry':
                    value = row[column]
                    # None 값 처리
                    if pd.isna(value):
                        formatted_value = "NULL"
                    # 숫자형 데이터 처리
                    elif np.issubdtype(type(value), np.number):
                        formatted_value = f"{value:.6f}" if isinstance(value, float) else str(value)
                    # 나머지 데이터 타입
                    else:
                        formatted_value = str(value)
                    analysis.append(f"  - {column}: {formatted_value}")
            
            # 도형 정보 추가
            analysis.extend([
                "- 도형 정보:",
                f"  - 도형 타입: {geom.geom_type}",
                f"  - 면적: {geom.area:.2f}",
                f"  - 둘레: {geom.length:.2f}",
                "  - 중심점 좌표:",
                f"    - X: {geom.centroid.x:.6f}",
                f"    - Y: {geom.centroid.y:.6f}",
                "  - 경계 상자:",
                f"    - 최소 X: {geom.bounds[0]:.6f}",
                f"    - 최소 Y: {geom.bounds[1]:.6f}",
                f"    - 최대 X: {geom.bounds[2]:.6f}",
                f"    - 최대 Y: {geom.bounds[3]:.6f}"
            ])
            
            # 도형 타입별 추가 정보
            if geom.geom_type == 'MultiPolygon':
                polygon_count = len(list(geom.geoms))
                vertex_count = sum(len(list(polygon.exterior.coords)) for polygon in geom.geoms)
                hole_count = sum(len(polygon.interiors) for polygon in geom.geoms)
                analysis.extend([
                    "  - MultiPolygon 상세:",
                    f"    - 구성 폴리곤 수: {polygon_count}",
                    f"    - 전체 꼭지점 수: {vertex_count}",
                    f"    - 구멍 개수: {hole_count}"
                ])
                
                # 각 구성 폴리곤의 상세 정보
                analysis.append("    - 구성 폴리곤 정보:")
                for i, polygon in enumerate(geom.geoms):
                    analysis.extend([
                        f"      - 폴리곤 {i+1}:",
                        f"        - 면적: {polygon.area:.2f}",
                        f"        - 둘레: {polygon.length:.2f}",
                        f"        - 꼭지점 수: {len(list(polygon.exterior.coords))}",
                        f"        - 구멍 수: {len(polygon.interiors)}"
                    ])
            
            elif geom.geom_type == 'Polygon':
                analysis.extend([
                    "  - Polygon 상세:",
                    f"    - 꼭지점 수: {len(list(geom.exterior.coords))}",
                    f"    - 구멍 수: {len(geom.interiors)}"
                ])
                
                if geom.interiors:
                    analysis.append("    - 구멍 정보:")
                    for i, interior in enumerate(geom.interiors):
                        analysis.extend([
                            f"      - 구멍 {i+1}:",
                            f"        - 꼭지점 수: {len(list(interior.coords))}"
                        ])
            
            elif geom.geom_type in ['LineString', 'MultiLineString']:
                if geom.geom_type == 'LineString':
                    analysis.extend([
                        "  - LineString 상세:",
                        f"    - 꼭지점 수: {len(list(geom.coords))}"
                    ])
                else:
                    total_vertices = sum(len(list(line.coords)) for line in geom.geoms)
                    analysis.extend([
                        "  - MultiLineString 상세:",
                        f"    - 라인 수: {len(list(geom.geoms))}",
                        f"    - 전체 꼭지점 수: {total_vertices}"
                    ])
            
            elif geom.geom_type in ['Point', 'MultiPoint']:
                if geom.geom_type == 'Point':
                    analysis.extend([
                        "  - Point 상세:",
                        f"    - X: {geom.x:.6f}",
                        f"    - Y: {geom.y:.6f}"
                    ])
                else:
                    analysis.extend([
                        "  - MultiPoint 상세:",
                        f"    - 포인트 수: {len(list(geom.geoms))}",
                        "    - 포인트 좌표:"
                    ])
                    for i, point in enumerate(geom.geoms):
                        analysis.extend([
                            f"      - 포인트 {i+1}:",
                            f"        - X: {point.x:.6f}",
                            f"        - Y: {point.y:.6f}"
                        ])
            
            # WKT 형식 도형 정보 추가
            analysis.extend([
                "  - WKT 형식:",
                f"    {geom.wkt}"
            ])
                
        
        # 4. 개별 피처 정보
        analysis.append("\n## 개별 피처 정보")
        
        # 모든 컬럼 이름 (geometry 제외)
        columns = [col for col in gdf.columns if col != 'geometry']
        
        for idx, row in gdf.iterrows():
            analysis.append(f"\n### 피처 {idx + 1}")
            
            # 속성 정보
            analysis.append("#### 속성")
            for col in columns:
                value = row[col]
                # None, NaN 처리
                if pd.isna(value):
                    value = "없음"
                # 숫자형 데이터 포맷팅
                elif isinstance(value, (int, float)):
                    value = f"{value:,}" if isinstance(value, int) else f"{value:,.2f}"
                analysis.append(f"- {col}: {value}")
            
            # 도형 정보
            analysis.append("#### 도형 정보")
            geom = row['geometry']
            if geom is not None:
                analysis.append(f"- 도형 타입: {geom.geom_type}")
                
                # 도형 타입별 특성 정보
                if geom.geom_type in ['LineString', 'MultiLineString']:
                    analysis.append(f"- 길이: {geom.length:.2f}")
                elif geom.geom_type in ['Polygon', 'MultiPolygon']:
                    analysis.append(f"- 면적: {geom.area:.2f}")
                    analysis.append(f"- 둘레: {geom.length:.2f}")
                
                # 경계 상자 정보
                bounds = geom.bounds
                analysis.append(f"- 경계 상자:")
                analysis.append(f"  - 최소 X: {bounds[0]:.6f}")
                analysis.append(f"  - 최소 Y: {bounds[1]:.6f}")
                analysis.append(f"  - 최대 X: {bounds[2]:.6f}")
                analysis.append(f"  - 최대 Y: {bounds[3]:.6f}")
                
                # 중심점 정보
                centroid = geom.centroid
                analysis.append(f"- 중심점: ({centroid.x:.6f}, {centroid.y:.6f})")
            else:
                analysis.append("- 도형 없음")
            
            # 구분선 추가
            analysis.append("\n---")
        
        return "\n".join(analysis)

    def process_layer(self, layer):
        """레이어를 처리하고 벡터 저장소 생성"""
        try:
            # GeoPandas DataFrame으로 변환 및 분석
            self.gdf = self.qgis_layer_to_geopandas(layer)
            text = self.analyze_geodataframe(self.gdf)
            
            # 텍스트 분할 및 벡터 저장소 생성
            text_splitter = CharacterTextSplitter(
                separator="\n",
                chunk_size=1000,
                chunk_overlap=200
            )
            texts = text_splitter.split_text(text)
            
            if not texts:
                raise Exception("텍스트 추출에 실패했습니다.")

            embeddings = OpenAIEmbeddings(
                api_key=self.api_key,
                model="text-embedding-ada-002"
            )
            
            self.vector_store = FAISS.from_texts(
                texts,
                embeddings
            )
            
            llm = ChatOpenAI(
                temperature=0,
                api_key=self.api_key,
                model_name="gpt-4o"
            )
            
            self.chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=self.vector_store.as_retriever(),
                memory=ConversationBufferMemory(
                    memory_key="chat_history",
                    output_key="answer",
                    return_messages=True
                ),
                return_source_documents=True,
                verbose=True
            )
            
            self.reference_text = text
            self.is_processed = True  # 처리 완료 표시

        except Exception as e:
            self.is_processed = False  # 처리 실패 시 상태 초기화
            raise Exception(f"레이어 처리 중 오류: {str(e)}")


    def query(self, question: str) -> str:
        """질문에 대한 응답 생성"""
        try:
            if not self.chain:
                raise Exception("대화 체인이 초기화되지 않았습니다.")

            # 질문 처리
            chat_history = [(item["question"], item["answer"]) for item in self.chat_history]
            result = self.chain({
                "question": question,
                "chat_history": chat_history  # 대화 기록 전달
            })

            # 응답 및 소스 문서 추출
            answer = result.get('answer', '')
            source_docs = result.get('source_documents', [])

            # 응답 텍스트 구성
            response_text = answer

            # 소스 문서 정보 추가
            if source_docs:
                response_text += "\n\n참고 문서:"
                for i, doc in enumerate(source_docs, 1):
                    content = doc.page_content[:200]
                    response_text += f"\n{i}. {content}..."

            # 대화 기록 저장
            self.chat_history.append({
                "question": question,
                "answer": answer,
                "sources": [doc.page_content for doc in source_docs]
            })

            return response_text

        except Exception as e:
            error_msg = f"질문 처리 중 오류: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def get_chat_history(self) -> list:
        """대화 기록 반환"""
        return self.chat_history

    def clear_chat_history(self):
        """대화 기록 초기화"""
        try:
            self.chat_history = []
            if self.chain and hasattr(self.chain, 'memory'):
                self.chain.memory.clear()
            logging.info("대화 기록이 초기화되었습니다.")
        except Exception as e:
            logging.error(f"대화 기록 초기화 중 오류: {str(e)}") 