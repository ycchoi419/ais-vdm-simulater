import asyncio
import yaml
from app.vdm_creater import vdmCreator
from geographiclib.geodesic import Geodesic

async def main() -> None:
    geod = Geodesic.WGS84

    target_ip = "10.0.100.20"
    target_port = "6501"
    
    vdm_creator = vdmCreator(target_ip, target_port)

    with open("tgt-setting.yaml", encoding="UTF-8") as f:
        target_ship = yaml.load(f, Loader=yaml.FullLoader)
    
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

    # Create tasks for N ships
    create_tasks = [
        asyncio.create_task(repeat_task(key, args))
        for key, args in target_ship.items()
    ]

    # Use asyncio.gather to run tasks indefinitely
    await asyncio.gather(*create_tasks)

if __name__ == "__main__":
    asyncio.run(main())