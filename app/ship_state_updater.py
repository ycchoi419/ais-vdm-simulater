# pylint:disable=C0301,R0914
# mypy: ignore-errors
import math
import time
import socket
import asyncio

from pyais.encode import encode_dict


class ShipStateUpdator:
    EARTH_RADIUS = 6371000  # 지구의 반지름 (미터 단위)

    def __init__(
        self, sock: socket.socket, ship_dict: dict, target_ip: str, parser_port: int
    ):
        self.sock = sock
        self.ship_dict = ship_dict
        self.target_ip = target_ip
        self.parser_port = parser_port

    async def update_ship_state(
        self, mmsi: int, send_period: float, end_time: float, event: list
    ) -> None:
        """_summary_

        Args:
            mmsi (int): _description_
            send_period (float): _description_
            end_time (float): _description_
            event (list): _description_
        """
        event_index = 0
        current_time = 0
        event_len = len(event)
        loop = asyncio.get_event_loop()
        start_time = loop.time()

        while True:
            current_time = (loop.time() - start_time) / 60
            if current_time >= end_time:
                break

            if event_len > event_index:
                arrange_event = list(event[event_index].values())[0]
                if arrange_event["time"] <= current_time:
                    event_index += 1
                    if "course" in arrange_event:
                        self.ship_dict[f"{mmsi}"]["course"] = arrange_event["course"]
                    if "speed" in arrange_event:
                        self.ship_dict[f"{mmsi}"]["speed"] = arrange_event["speed"]

            lat_rad = math.radians(self.ship_dict[f"{mmsi}"]["lat"])
            lon_rad = math.radians(self.ship_dict[f"{mmsi}"]["lon"])
            course_rad = math.radians(self.ship_dict[f"{mmsi}"]["course"])

            distance_moved = self.ship_dict[f"{mmsi}"]["speed"] * 1852 / 3600

            delta_lat = distance_moved * math.cos(course_rad) / self.EARTH_RADIUS
            self.ship_dict[f"{mmsi}"]["lat"] = math.degrees(lat_rad + delta_lat)

            delta_lon = (distance_moved * math.sin(course_rad)) / (
                self.EARTH_RADIUS * math.cos(lat_rad)
            )
            self.ship_dict[f"{mmsi}"]["lon"] = math.degrees(lon_rad + delta_lon)
            self.ship_dict[f"{mmsi}"]["second"] = time.gmtime().tm_sec

            encoded_data = encode_dict(
                self.ship_dict[f"{mmsi}"], radio_channel="A", talker_id="AIVDM"
            )[0]
            self.sock.sendto(
                (encoded_data + "\r\n").encode(), (self.target_ip, self.parser_port)
            )

            await asyncio.sleep(send_period)
        print(f"{mmsi} finished!")