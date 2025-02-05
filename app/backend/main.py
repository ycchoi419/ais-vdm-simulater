from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import asyncio
from virtualAIS import VirtualAIS
from model import ReqBody

app = FastAPI()


class Simulator() :
    def __init__(self):
        self.target_ships = None
        self.ais_list = None

    async def start_simulation(self, target_ships):
        self.target_ships = target_ships
        if self.ais_list is not None:
            for v_ais in self.ais_list:
                v_ais.stop_signal()
                del v_ais
        if target_ships is None:
            return
        self.ais_list = [
            VirtualAIS(args)
            for _, args in self.target_ships.items()
        ]
        await asyncio.gather(*(v_ais.start_signal() for v_ais in self.ais_list))
    
    def stop_simulation(self):
        if self.ais_list is None: 
            return
        for v_ais in self.ais_list:
            v_ais.stop_signal()
            del v_ais
            self.ais_list = None

simulator = Simulator()
    
@app.get("/start")
async def start_bg(background_tasks: BackgroundTasks):
    background_tasks.add_task(simulator.start_simulation)
    return JSONResponse(content={"message": "success"})


@app.post("/start")
async def start_bg_with_Data(item: ReqBody, background_tasks: BackgroundTasks):
    if item.ships is None or len(item.ships) == 0:
        return JSONResponse(content={"message": "ship data is empty"})
    background_tasks.add_task(simulator.start_simulation, item.ships)
    return JSONResponse(content={"message": "success "})

@app.get("/stop")
async def stop_bg():
    print("success")
    simulator.stop_simulation()
    if simulator.ais_list is None:
        return JSONResponse(content={"message": "stop request accepted"})
    else:
        print(simulator.ais_list)
        return JSONResponse(content={"message": "stop request failed"})
app.mount ("/map", StaticFiles(directory="../map", html=False), name="map")
if os.path.exists("../frontend/dist"):
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
