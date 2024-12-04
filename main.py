import yaml
import redis
import json
from redis.exceptions import RedisError
from redis.asyncio import Redis
import asyncio
from app.vdm_creater import vdmCreator
from app.ownship_nmea_mock import OwnshipNMEAMock
from geographiclib.geodesic import Geodesic
from config import REDIS, TARGET
import math

# Leave this not using async
def create_redis_getter(ip: str, port: int, channel: str):
    option = QueueOption(ip, port, 0, channel=channel)
    return Getter(option)

async def get_redis_connection(retries=10, delay=2):
    attempt = 0
    while attempt < retries:
        try:
            # Redis에 비동기적으로 연결 시도
            connection = Redis(host=REDIS["host"], port=REDIS["port"], decode_responses=True)
            # Ping으로 연결 확인
            await connection.ping()
            print("Redis 연결 성공")
            return connection
        except RedisError as e:
            attempt += 1
            print(f"Redis 연결 실패: {e}, 재시도 {attempt}/{retries}")
            await asyncio.sleep(delay)
    raise Exception("Redis에 연결할 수 없습니다.")

async def main() -> None:
    geod = Geodesic.WGS84

    target_ip = TARGET["host"]
    target_port = TARGET["port"]
    
    vdm_creator = vdmCreator(target_ip, target_port)
    ownship_nmea = OwnshipNMEAMock("10.0.100.20", "6501")

    # Target ship settings from file
    with open("tgt-setting.yaml", encoding="UTF-8") as f:
        target_ship = yaml.load(f, Loader=yaml.FullLoader)
    
    # Redis 연결
    redis_connection = await get_redis_connection()
    
    try:
        redis_ownship_data = await redis_connection.get("nmea:display")
        if redis_ownship_data:
            try:
                data = json.loads(redis_ownship_data)

                # None 값 체크 및 기본값 설정
                lat_os = float(data.get("Latitude", 0.0) or 0.0)
                lon_os = float(data.get("Longitude", 0.0) or 0.0)
                lon_cog = float(data.get("COG", 0.0) or 0.0)
                lon_sog = float(data.get("SOG", 0.0) or 0.0)

            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"JSON parsing error: {e}")
                return
        else:
            print("Redis에서 데이터를 가져오지 못했습니다.")
            return

        # Static ship state for NMEA generation
        ship_state = {
            "r": 0.1,
            "lat": 37.7749,  # 고정된 초기 위도
            "lon": -122.4194,  # 고정된 초기 경도
            "psi": 1.5,  # 초기 침로
            "SOG": 10.5,  # 초기 속도 (Speed Over Ground)
            "COG": 45.0,  # 초기 침로 (Course Over Ground)
            "STW": 10.5,  # Speed Through Water
            "del_cmd": 15.0,
            "radot_cmd": 0.5,
            "rot_cmd": 1.0,
            "hdg_cmd": 90.0,
            "steering_mode": "A",
            "turn_mode": "N",
            "del": 15.0,
        }

        # Define a function for repeated execution
        async def repeat_task(key, args):
            while True:
                # VDM 생성 및 송신
                await vdm_creator.createTgt(args)

                # 위치 업데이트
                lat, lon = ship_state["lat"], ship_state["lon"]
                dist_NM = int(ship_state["SOG"]) * (10 / 3600)  # 10초마다 이동 거리 계산
                dist_m = dist_NM * 1852
                result = geod.Direct(lat, lon, math.degrees(ship_state["COG"]), dist_m)
                ship_state["lat"], ship_state["lon"] = result["lat2"], result["lon2"]

                # NMEA 더미 문장 생성 및 송신
                nmea_sentences = ownship_nmea.generate_nmea_sentences(
                    lat=ship_state["lat"], lon=ship_state["lon"], sog=ship_state["SOG"],
                    cog=math.radians(ship_state["COG"]), psi=ship_state["psi"],
                    rot=ship_state["r"], stw=ship_state["STW"]
                )
                await ownship_nmea.send_nmea(nmea_sentences)

                await asyncio.sleep(args["send_period"])
                print(f"Target {key} -> lat: {ship_state['lat']}, lon: {ship_state['lon']}")

        # Create tasks for N ships
        create_tasks = [
            asyncio.create_task(repeat_task(key, args))
            for key, args in target_ship.items()
        ]
        # Use asyncio.gather to run tasks indefinitely
        await asyncio.gather(*create_tasks)
    finally:
        # Redis 연결 종료
        await redis_connection.aclose()  # Deprecated `close()` 대신 `aclose()` 사용

if __name__ == "__main__":
    asyncio.run(main())
