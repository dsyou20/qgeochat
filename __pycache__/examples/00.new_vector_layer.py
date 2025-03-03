from qgis.core import QgsVectorLayer, QgsProject
import json

geojson_data = '''
{
"type": "FeatureCollection",
"features": [
{
"type": "Feature",
"properties": {
"id": 2,
"name": "garage2"
},
"geometry": {
"type": "Point",
"coordinates": [188406.915581, 282014.709229]
}
},
{
"type": "Feature",
"properties": {
"id": 3,
"name": "garage3"
},
"geometry": {
"type": "Point",
"coordinates": [188402.050834, 281989.822567]
}
},
{
"type": "Feature",
"properties": {
"id": 4,
"name": "garage4"
},
"geometry": {
"type": "Point",
"coordinates": [188384.084527, 281988.851646]
}
}
]
}
'''
# EPSG:5186 좌표계
crs = 'EPSG:5186'

layer = QgsVectorLayer(geojson_data, "MyGeoJSONLayer", "ogr")

layer.setCrs(QgsCoordinateReferenceSystem(crs))

# 레이어가 유효한지 확인
if not layer.isValid():
    print("레이어를 불러오는데 실패했습니다.")
else:
    # 현재 프로젝트에 레이어 추가
    QgsProject.instance().addMapLayer(layer)
    print("레이어가 성공적으로 추가되었습니다.")