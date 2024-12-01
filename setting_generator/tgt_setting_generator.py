import random
import yaml

# 중심 좌표 설정
center_lat = 31.5
center_lon = 135.1

# 10 마일 반경에 해당하는 위도, 경도 범위 10NM ~= 0.145
radius = 0.12

# 생성할 선박 수 설정
num_ships = 4

# MMSI 범위 설정 (9자리 숫자)
start_mmsi = 123456781

# 생성할 YAML 데이터를 저장할 딕셔너리
data = {}

# num_ships개의 test_ship 생성
for i in range(num_ships):
    random_lat = center_lat + random.uniform(-radius, radius)
    random_lon = center_lon + random.uniform(-radius, radius)
    
    ship_name = f"test_ship{i+1}"
    data[ship_name] = {
        'mmsi': start_mmsi + i,
        'course': 90,
        'distance': 2,
        'lat': round(random_lat, 4),
        'lon': round(random_lon, 4),
        'send_period': 2,
        'speed': 10,
        'time': {
            'create_time': 0,
            'end_time': 10
        }
    }

# YAML 파일로 저장
file_path = './tgt-setting-generated.yaml'
with open(file_path, 'w') as file:
    yaml.dump(data, file, default_flow_style=False)

print(f"YAML 파일이 생성되었습니다: {file_path}")
