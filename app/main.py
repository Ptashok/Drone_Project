from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import secrets

app = FastAPI(title="Drone Swarm Authentication System")

class Swarm(BaseModel):
    name: str
    mission: str

swarms = [] 


class Drone(BaseModel):
    name: str
    drone_type: str
    serial_number: str
    

drones = []

class Heartbeat(BaseModel):
    drone_id: int
    battery: int
    status: str
    auth_key: str

heartbeats = []

@app.get("/")
def root():
    return {"message": "System is working"}



@app.post("/drones")
def create_drone(drone: Drone):
    drone_data= {
        "id" : len(drones) + 1,
        "name" : drone.name ,
        "drone_type" : drone.drone_type ,
        "serial_number": drone.serial_number ,
        "auth_key": secrets.token_hex(16)

    }
    drones.append(drone_data)
    
    return {
        "message": "Drone registered successfully",
        "drone": drone_data
    }


@app.get("/drones")
def get_drones():
    return drones

@app.get("/drones/{drone_id}")
def get_drone(drone_id: int): 
    for drone in drones:
        if drone["id"] == drone_id:
            return drone 
        
@app.get("/drones/{drone_id}/status")
def monitoring(drone_id: int):
    found_heartbeats = []
    for heartbeat in heartbeats:
        if heartbeat["drone_id"] == drone_id:
            found_heartbeats.append(heartbeat)
            
    if not found_heartbeats:
            return {"error": "No heartbeat found"}
    
    return found_heartbeats[-1]

@app.get("/drones/{drone_id}/health")
def detection(drone_id: int):
    found_heartbeat = []
    for heartbeat in heartbeats:
        if heartbeat["drone_id"] == drone_id:
            found_heartbeat.append(heartbeat)
    if not found_heartbeat:
        return {"error": "No heartbeat found"}
    last_timestamp = found_heartbeat[-1]["timestamp"]
    now = datetime.now()
    difference = now - last_timestamp
    if difference.seconds > 30:
            return {"offline"}
    else: 
            return {"online"}

@app.delete("/drones/{drone_id}")
def delete_drone(drone_id: int):
    for drone in drones:
        if drone["id"] == drone_id:
            drone.remove(drone)
            return {"messege": "Drone deleted successfully"}
    return {"message": "Drone not found"}


@app.post("/heartbeats")
def create_heartbeat(heartbeat: Heartbeat):
    heartbeat_data= {
        "battery" : heartbeat.battery,
        "status": heartbeat.status  ,
        "drone_id": heartbeat.drone_id,
        "timestamp": datetime.now(), 
        "auth_key": heartbeat.auth_key 
    }
    
    found_drone = None 

    for drone in drones: 
        if drone ["id"] == heartbeat.drone_id:
            found_drone = drone
    if found_drone is None: 
        return{"error": "Drone not found"}
    if found_drone["auth_key"] != heartbeat.auth_key:
        return {"error": "Unauthorized drone"}
    heartbeats.append(heartbeat_data)
    return{
        "message": "Heartbeat registered successfully ",
        "heartbeats": heartbeat_data
    }
    

@app.get("/heartbeats")
def get_heartbeats():
    return heartbeats

@app.get("/heartbeats/{drone_id}")
def get_heartbeat(drone_id: int):
    result = []

    for heartbeat in heartbeats:
        if heartbeat["drone_id"] == drone_id:
            result.append(heartbeat)

    return result


@app.post("/swarms")
def create_swarm(swarm: Swarm):
    swarm_data = {
        "mission": swarm.mission,
        "id": len(swarms) + 1,
        "name": swarm.name,  
        "members": []
    }
    swarms.append(swarm_data)
    return {
        "message": "Swarms registered successfully",
        "swarms": swarm_data
    }
@app.get("/swarms")
def get_swarms():
    return swarms

@app.get("/swarms/{swarm_id}")
def get_swarm(swarm_id: int): 
    for swarm in swarms:
        if swarm["id"] == swarm_id:
            return swarm  
        
@app.post("/swarms/{swarm_id}/members/{drone_id}")
def add_drone_to_swarm(swarm_id: int, drone_id: int):
    found_swarm = None
    found_drone = None

    for swarm in swarms:
        if swarm["id"] == swarm_id:
            found_swarm = swarm

    for drone in drones:
        if drone["id"] == drone_id:
            found_drone = drone

    if found_swarm is None:
        return {"error": "Swarm not found"}

    if found_drone is None:
        return {"error": "Drone not found"}

    found_swarm["members"].append(drone_id)

    return {
        "message": "Drone added to swarm successfully",
        "swarm": found_swarm
    }
