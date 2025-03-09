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
    def __init__(self, api_key=None):
        """초기화"""
        self.gdf = None
        self.vector_store = None
        self.current_text_path = None
        self.reference_text = None
        self.chat_history = []
        self.chain = None
        
        # API 키 설정
        self.api_key = api_key
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            logging.info("OpenAI API 키가 설정되었습니다.")
        else:
            # QSettings에서 API 키 읽기
            settings = QgsSettings()
            self.api_key = settings.value("QOllama/api_key", "", type=str)
            if self.api_key:
                os.environ["OPENAI_API_KEY"] = self.api_key
                logging.info("저장된 OpenAI API 키를 불러왔습니다.")
            else:
                logging.warning("OpenAI API 키가 설정되지 않았습니다.")

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

    def create_vector_store(self, reference_text = None):
        """벡터 저장소 및 대화 체인 생성"""
        try:
            
            self.reference_text = reference_text
            
            if not self.reference_text:
                raise Exception("참조할 텍스트가 없습니다.")

            # 1. 텍스트 분할
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100,
                length_function=len,
                separators=["\n## ", "\n### ", "\n#### ", "\n", " ", ""]
            )
            chunks = text_splitter.split_text(self.reference_text)

            # 2. 벡터 저장소 생성
            embeddings = OpenAIEmbeddings()
            self.vector_store = FAISS.from_texts(chunks, embeddings)

            # 3. 대화 히스토리 메모리 설정
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                output_key="answer",
                return_messages=True
            )

            # 4. ConversationalRetrievalChain 설정
            llm = ChatOpenAI(
                model_name="gpt-4o",
                temperature=0
            )

            self.chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=self.vector_store.as_retriever(),
                memory=memory,
                verbose=True,
                return_source_documents=True
            )

            logging.info(f"벡터 저장소와 대화 체인이 생성되었습니다. 총 {len(chunks)}개의 청크가 처리되었습니다.")

        except Exception as e:
            logging.error(f"벡터 저장소 생성 중 오류: {str(e)}")
            raise Exception(f"벡터 저장소 생성 중 오류: {str(e)}")

    def query(self, question: str) -> str:
        """질문에 대한 응답 생성"""
        try:
            if not self.chain:
                raise Exception("대화 체인이 초기화되지 않았습니다.")

            # 질문 처리
            chat_history = [(item["question"], item["answer"]) for item in self.chat_history]
            result = self.chain({
                "question": question,
                "chat_history": chat_history
            })

            # 응답 및 소스 문서 추출
            answer = result.get('answer', '')
            source_docs = result.get('source_documents', [])

            # 응답 텍스트 구성
            response_text = answer

            # # 소스 문서 정보 추가
            # if source_docs:
            #     response_text += "\n\n참고 문서:"
            #     for i, doc in enumerate(source_docs, 1):
            #         content = doc.page_content[:200]
            #         response_text += f"\n{i}. {content}..."

            # 대화 기록 저장
            self.chat_history.append({
                "question": question,
                "answer": answer,
                #"sources": [doc.page_content for doc in source_docs]
            })

            return response_text

        except Exception as e:
            error_msg = f"질문 처리 중 오류: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def clear_chat_history(self):
        """대화 기록 초기화"""
        try:
            self.chat_history = []
            if self.chain and hasattr(self.chain, 'memory'):
                self.chain.memory.clear()
            logging.info("대화 기록이 초기화되었습니다.")
        except Exception as e:
            logging.error(f"대화 기록 초기화 중 오류: {str(e)}")

