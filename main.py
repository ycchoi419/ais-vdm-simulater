import yaml
import redis
import json
from redis.exceptions import RedisError
from redis.asyncio import Redis
import asyncio
from app.vdm_creater import vdmCreator
from geographiclib.geodesic import Geodesic
from config import REDIS, TARGET, APP

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

    target_ip   = TARGET["host"]
    target_port = TARGET["port"]
    
    vdm_creator = vdmCreator(target_ip, target_port)

    # Target ship settings from file
    with open("tgt-setting.yaml", encoding="UTF-8") as f:
        target_ship = yaml.load(f, Loader=yaml.FullLoader)
    
    # Redis 연결
    redis_connection = await get_redis_connection()
    
    try:
        redis_ownship_data = await redis_connection.get("nmea:display")
        if redis_ownship_data:
            try:
                data    = json.loads(redis_ownship_data)
                lat_os  = float(data.get("Latitude", 0.0))
                lon_os  = float(data.get("Longitude", 0.0))
                lon_cog = float(data.get("COG", 0.0))
                lon_sog = float(data.get("SOG", 0.0))
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
        else:
            print("Redis에서 데이터를 가져오지 못했습니다.")
            return

        # Define a function for repeated execution
        async def repeat_task(key, args):
            while True:
                await vdm_creator.createTgt(args)

                lat, lon = args["lat"], args["lon"]
                dist_NM = int(args["speed"]) * (int(args["send_period"]) / 3600)
                dist_m = dist_NM * 1852
                result = geod.Direct(lat, lon, int(args["course"]), dist_m) 
                args['lat'], args['lon'] = result['lat2'], result['lon2']
                
                await asyncio.sleep(args["send_period"])
                print("target_host:", target_ip, "target_port:", target_port)
                print("lat_init:", lat_os, "lon_init:", lon_os)

        # Create tasks for N ships
        create_tasks = [
            asyncio.create_task(repeat_task(key, args))
            for key, args in target_ship.items()
        ]
        # Use asyncio.gather to run tasks indefinitely
        await asyncio.gather(*create_tasks)
    finally:
        # Redis 연결 종료
        await redis_connection.close()

if __name__ == "__main__":
    asyncio.run(main())