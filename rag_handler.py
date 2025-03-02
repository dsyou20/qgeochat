from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
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
from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry, QgsWkbTypes, QgsDistanceArea
from qgis.core import QgsProject
import platform

class RAGHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        self.vector_store = None
        self.chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        # 한글 폰트 등록
        self.register_korean_font()

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

    def create_pdf_from_layer(self, layer):
        """SHP 레이어의 내용을 PDF로 변환"""
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        pdf_path = os.path.join(temp_dir, f"{layer.name()}_content.pdf")
        
        try:
            doc = SimpleDocTemplate(pdf_path, pagesize=letter)
            elements = []
            
            # 기본 스타일 가져오기
            styles = getSampleStyleSheet()
            korean_font = self.get_korean_font_name()
            
            # 한글 스타일 추가
            styles.add(ParagraphStyle(
                name='KoreanNormal',
                parent=styles['Normal'],
                fontName=korean_font,
                fontSize=10,
                leading=12
            ))
            
            styles.add(ParagraphStyle(
                name='KoreanHeading1',
                parent=styles['Heading1'],
                fontName=korean_font,
                fontSize=14,
                leading=16
            ))

            # 1. 레이어 기본 정보
            elements.append(Paragraph(f"레이어 분석 보고서: {layer.name()}", styles['KoreanHeading1']))
            
            # 2. 공간 정보 섹션
            elements.append(Paragraph("공간 정보", styles['KoreanHeading1']))
            
            # 좌표계 정보
            crs = layer.crs()
            spatial_info = [
                f"좌표계: {crs.description()}",
                f"EPSG 코드: {crs.authid()}",
                f"좌표계 유형: {'지리좌표계' if crs.isGeographic() else '투영좌표계'}"
            ]
            for info in spatial_info:
                elements.append(Paragraph(info, styles['KoreanNormal']))
            
            # 레이어 범위
            extent = layer.extent()
            extent_info = [
                f"X 최소: {extent.xMinimum():.6f}",
                f"X 최대: {extent.xMaximum():.6f}",
                f"Y 최소: {extent.yMinimum():.6f}",
                f"Y 최대: {extent.yMaximum():.6f}"
            ]
            elements.append(Paragraph("레이어 범위:", styles['KoreanHeading1']))
            for info in extent_info:
                elements.append(Paragraph(info, styles['KoreanNormal']))
            
            # 도형 타입 정보
            geom_type = QgsWkbTypes.displayString(layer.wkbType())
            elements.append(Paragraph(f"도형 타입: {geom_type}", styles['KoreanNormal']))
            
            # 3. 속성 정보 섹션
            elements.append(Paragraph("속성 정보", styles['KoreanHeading1']))
            fields = layer.fields()
            field_info = [
                [
                    "필드명",
                    "타입",
                    "길이",
                    "정밀도"
                ]
            ]
            for field in fields:
                field_info.append([
                    field.name(),
                    field.typeName(),
                    str(field.length()),
                    str(field.precision())
                ])
            
            # 속성 테이블 생성
            table = Table(field_info)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            
            # 4. 피처 통계 정보
            elements.append(Paragraph("피처 통계", styles['KoreanHeading1']))
            feature_count = layer.featureCount()
            elements.append(Paragraph(f"총 피처 수: {feature_count}", styles['KoreanNormal']))
            
            # 도형 통계 계산
            if layer.geometryType() != QgsWkbTypes.NullGeometry:
                total_length = 0
                total_area = 0
                for feature in layer.getFeatures():
                    geom = feature.geometry()
                    if geom:
                        if QgsWkbTypes.hasM(layer.wkbType()):
                            geom.dropM()
                        if QgsWkbTypes.hasZ(layer.wkbType()):
                            geom.dropZ()
                            
                        if geom.type() == QgsWkbTypes.LineGeometry:
                            total_length += geom.length()
                        elif geom.type() == QgsWkbTypes.PolygonGeometry:
                            total_area += geom.area()
                
                if total_length > 0:
                    elements.append(Paragraph(f"총 길이: {total_length:.2f}", styles['KoreanNormal']))
                if total_area > 0:
                    elements.append(Paragraph(f"총 면적: {total_area:.2f}", styles['KoreanNormal']))
            
            # 도형 정보를 위한 거리/면적 계산기 설정
            distance_area = QgsDistanceArea()
            distance_area.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
            distance_area.setEllipsoid(QgsProject.instance().ellipsoid())

            # 5. 피처 데이터와 도형 정보
            elements.append(Paragraph("피처 데이터 및 도형 정보", styles['KoreanHeading1']))
            
            # 필드명에 도형 정보 컬럼 추가
            headers = [field.name() for field in fields]
            headers.extend(['Geometry Type', 'WKT', 'Measurements'])
            data = [headers]
            
            # 피처 데이터 추가 (최대 100개까지만)
            feature_limit = 100
            for i, feature in enumerate(layer.getFeatures()):
                if i >= feature_limit:
                    elements.append(Paragraph(
                        f"* 참고: 전체 {feature_count}개 중 {feature_limit}개만 표시됨", 
                        styles['Italic']
                    ))
                    break
                    
                row = []
                # 속성 데이터 추가
                for field in fields:
                    value = feature[field.name()]
                    if isinstance(value, (str, bytes)):
                        try:
                            if isinstance(value, bytes):
                                value = value.decode('utf-8', errors='replace')
                            else:
                                value = str(value)
                        except:
                            value = str(value).encode('ascii', 'replace').decode('ascii')
                    else:
                        value = str(value)
                    row.append(value)
                
                # 도형 정보 추가
                geom = feature.geometry()
                if geom and not geom.isNull():
                    # 도형 타입
                    geom_type = QgsWkbTypes.displayString(geom.wkbType())
                    row.append(geom_type)
                    
                    # WKT (긴 문자열은 축약)
                    wkt = geom.asWkt()
                    if len(wkt) > 100:
                        wkt = wkt[:100] + "..."
                    row.append(wkt)
                    
                    # 도형 측정값
                    measurements = []
                    if geom.type() == QgsWkbTypes.PointGeometry:
                        point = geom.asPoint()
                        measurements.append(f"X: {point.x():.2f}")
                        measurements.append(f"Y: {point.y():.2f}")
                        if QgsWkbTypes.hasZ(geom.wkbType()):
                            measurements.append(f"Z: {point.z():.2f}")
                    
                    elif geom.type() == QgsWkbTypes.LineGeometry:
                        length = distance_area.measureLength(geom)
                        if length < 1000:
                            measurements.append(f"길이: {length:.2f} m")
                        else:
                            measurements.append(f"길이: {length/1000:.2f} km")
                    
                    elif geom.type() == QgsWkbTypes.PolygonGeometry:
                        area = distance_area.measureArea(geom)
                        perimeter = distance_area.measurePerimeter(geom)
                        if area < 1000000:
                            measurements.append(f"면적: {area:.2f} m²")
                        else:
                            measurements.append(f"면적: {area/1000000:.2f} km²")
                        if perimeter < 1000:
                            measurements.append(f"둘레: {perimeter:.2f} m")
                        else:
                            measurements.append(f"둘레: {perimeter/1000:.2f} km")
                    
                    row.append("\n".join(measurements))
                else:
                    row.extend(["No geometry", "", ""])
                
                data.append(row)
            
            # 도형 정보를 포함한 테이블 생성
            if len(data) > 1:
                # 테이블 스타일 설정
                table_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # 왼쪽 정렬로 변경
                    ('FONTNAME', (0, 0), (-1, -1), korean_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),  # 글자 크기 조정
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('WORDWRAP', (0, 0), (-1, -1), True)  # 자동 줄바꿈 활성화
                ]
                
                # 열 너비 설정
                col_widths = [80] * len(fields)  # 기본 필드들
                col_widths.extend([100, 150, 120])  # 도형 타입, WKT, 측정값 열
                
                feature_table = Table(data, colWidths=col_widths, repeatRows=1)
                feature_table.setStyle(TableStyle(table_style))
                elements.append(feature_table)
            
            # PDF 생성
            doc.build(elements)
            return pdf_path
            
        except Exception as e:
            raise Exception(f"PDF 생성 오류: {str(e)}")

    def process_layer(self, layer):
        """레이어를 처리하고 벡터 저장소 생성"""
        try:
            # PDF 생성
            pdf_path = self.create_pdf_from_layer(layer)
            
            # PDF 텍스트 추출
            text = ""
            try:
                with open(pdf_path, 'rb') as file:
                    content = file.read()
                    encodings = ['utf-8', 'cp1252', 'iso-8859-1', 'euc-kr']
                    for encoding in encodings:
                        try:
                            text = content.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if not text:
                        raise ValueError("텍스트 디코딩에 실패했습니다.")
            except Exception as e:
                raise Exception(f"PDF 읽기 오류: {str(e)}")

            # 텍스트 분할
            text_splitter = CharacterTextSplitter(
                separator="\n",
                chunk_size=1000,
                chunk_overlap=200
            )
            texts = text_splitter.split_text(text)
            
            if not texts:
                raise Exception("텍스트 추출에 실패했습니다.")

            # 벡터 저장소 생성 (FAISS 사용)
            embeddings = OpenAIEmbeddings(
                api_key=self.api_key,
                model="text-embedding-ada-002"
            )
            
            self.vector_store = FAISS.from_texts(
                texts,
                embeddings
            )
            
            # ConversationalRetrievalChain 설정
            llm = ChatOpenAI(
                temperature=0,
                api_key=self.api_key,
                model_name="gpt-4o"
            )
            
            self.chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=self.vector_store.as_retriever(),
                memory=self.memory
            )

            # PDF 파일 경로 반환 (임시 파일 삭제하지 않음)
            return pdf_path
            
        except Exception as e:
            raise Exception(f"레이어 처리 중 오류: {str(e)}")

    def get_response(self, question):
        """질문에 대한 응답 생성"""
        if not self.chain:
            return "레이어를 먼저 처리해주세요."
            
        try:
            response = self.chain({"question": question})
            return response['answer']
        except Exception as e:
            return f"응답 생성 중 오류가 발생했습니다: {str(e)}" 