from pydantic import BaseModel


class TimeModel(BaseModel):
    create_time: int | float
    end_time: int | float

class ShipModel(BaseModel):
    course: int | float
    distance: int | float
    lat: float
    lon: float
    mmsi: int
    send_period: int | float
    speed: int | float
    time: TimeModel

class ReqBody(BaseModel):
    ships: dict[str, ShipModel]
