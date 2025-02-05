import asyncio
from utils.vdm_creater import vdmCreator
from geographiclib.geodesic import Geodesic
from config import REDIS, TARGET, APP
import random
from model import ShipModel

class VirtualAIS():
    def __init__(self, config: ShipModel):
        self.lat = config.lat
        self.lon = config.lon
        self.speed= config.speed
        self.send_period = config.send_period
        self.course = config.course
        self.mmsi = config.mmsi
        self.geod = Geodesic.WGS84
        self.target_ip   = TARGET["host"]
        self.target_port = TARGET["port"]
        
        self._semaphore = 0
        self.vdm_creator = vdmCreator(self.target_ip, self.target_port)

    # Define a function for repeated execution
    async def start_signal(self):
        self._semaphore += 1
        if self._semaphore == 1:
            print(f"start signal : {self.mmsi}")
            await asyncio.sleep(random.random() * self.send_period)
        while True:
            if self._semaphore != 1:
                self._semaphore -= 1
                break
            args = {
                "lat": self.lat,
                "lon": self.lon,
                "course": self.course,
                "speed": self.speed,
                "mmsi": self.mmsi,
            }
            await self.vdm_creator.createTgt(args)

            lat, lon = args["lat"], args["lon"]
            dist_NM = int(self.speed) * (int(self.send_period) / 3600)
            dist_m = dist_NM * 1852
            result = self.geod.Direct(lat, lon, int(self.course), dist_m) 
            self.lat, self.lon = result['lat2'], result['lon2']
            print("target_host:", self.target_ip, "target_port:", self.target_port)
            await asyncio.sleep(self.send_period)
    
    def stop_signal(self):
        self._semaphore = 0
        print(f"stop signal : {self.mmsi}")



        
#     # Create tasks for N ships
#     create_tasks = [
#         asyncio.create_task(repeat_task(key, args))
#         for key, args in target_ship.items()
#     ]

#     # Use asyncio.gather to run tasks indefinitely
#     await asyncio.gather(*create_tasks)

# if __name__ == "__main__":
#     asyncio.run(main())