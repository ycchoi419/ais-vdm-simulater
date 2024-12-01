import asyncio
import time
from collections import defaultdict
from pyais.encode import encode_dict
from geographiclib.geodesic import Geodesic

class vdmCreator:
    def __init__(self, target_ip: str, target_port: str):
        self.target_ip = target_ip
        self.target_port = target_port
        self.ship_dict: dict = defaultdict(dict)

    async def createTgt(self, ship_args: dict) -> None:
        """
        Creates a manual target ship with a user-specified property value and sends it via UDP
        """

        data = {
            "msg_type": 1,
            "repeat": 1,
            "mmsi": ship_args["mmsi"],
            "status": 0,
            "turn": 0,
            "speed": ship_args["speed"],
            "accuracy": 0,
            "lon": ship_args["lon"],
            "lat": ship_args["lat"],
            "course": ship_args["course"],
            "heading": ship_args["course"],
            "second": time.gmtime().tm_sec,
            "maneuver": 0,
            "spare_1": b"",
            "raim": 0,
            "radio": 0,
        }
        
        # Encode AIS message
        encoded_data = encode_dict(data, radio_channel="A", talker_id="AIVDM")[0]
        encoded_data = encoded_data + "\r\n"
        print(data["mmsi"], ":", data["lat"], data["lon"], encoded_data)

        # Send encoded data via UDP
        try:
            # Create a UDP socket
            transport, protocol = await asyncio.get_running_loop().create_datagram_endpoint(
                lambda: asyncio.DatagramProtocol(),
                remote_addr=(self.target_ip, int(self.target_port))
            )

            # Send the data
            transport.sendto(encoded_data.encode("utf-8"))
            # transport.sendto(encoded_data + "\r\n").encode("utf-8")

            # Close the transport after sending
            transport.close()
        except Exception as e:
            print(f"Failed to send data via UDP: {e}")