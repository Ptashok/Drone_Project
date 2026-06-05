from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone
from app.database import SessionLocal
from sqlalchemy import text
import secrets
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Drone Swarm Authentication System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Swarm(BaseModel):
    name: str
    mission: str
 
class Drone(BaseModel):
    name: str
    drone_type: str
    serial_number: str

class Heartbeat(BaseModel):
    drone_id: int
    battery: int
    status: str
    auth_key: str

class UpdateDrone(BaseModel):
    name: str
    drone_type: str
    serial_number: str

@app.get("/")
def root():
    return {"message": "System is working"}

@app.post("/drones")
def create_drone(drone: Drone):
    db = SessionLocal()

    auth_key = secrets.token_hex(16)

    query = text("""
    INSERT INTO drones (name, drone_type, serial_number, auth_key)
    VALUES (:name, :drone_type, :serial_number, :auth_key)
    RETURNING id, name, drone_type, serial_number, auth_key;
    """)

    result = db.execute(query, {
        "name": drone.name,
        "drone_type": drone.drone_type,
        "serial_number": drone.serial_number,
        "auth_key": auth_key
    })

    new_drone = result.fetchone()
    db.commit()
    db.close()

    return {
        "message": "Drone registered successfully",
        "drone": dict(new_drone._mapping)
    }

@app.get("/drones")
def get_drones():
    db = SessionLocal()

    result = db.execute(text("SELECT * FROM drones ORDER BY id"))
    drones = result.fetchall()

    db.close()

    return [dict(drone._mapping) for drone in drones]

@app.get("/drones/{drone_id}")
def get_drone(drone_id: int):
    db = SessionLocal()

    result = db.execute(
        text("SELECT * FROM drones WHERE id = :id"),
        {"id": drone_id}
    )

    drone = result.fetchone()
    db.close()

    if drone is None:
        return {"error": "Drone not found"}

    return dict(drone._mapping)
        
@app.get("/drones/{drone_id}/status")
def monitoring(drone_id: int):
    db = SessionLocal()

    result = db.execute(
        text("""
        SELECT * FROM heartbeats
        WHERE drone_id = :drone_id
        ORDER BY timestamp DESC
        LIMIT 1
        """),
        {"drone_id": drone_id}
    )

    heartbeat = result.fetchone()
    db.close()

    if heartbeat is None:
        return {"error": "No heartbeat found"}

    return dict(heartbeat._mapping)

@app.get("/drones/{drone_id}/health")
def detection(drone_id: int):
    db = SessionLocal()

    result = db.execute(
        text("""
        SELECT * FROM heartbeats
        WHERE drone_id = :drone_id
        ORDER BY timestamp DESC
        LIMIT 1
        """),
        {"drone_id": drone_id}
    )

    heartbeat = result.fetchone()
    db.close()

    if heartbeat is None:
        return {"error": "No heartbeat found"}

    heartbeat_data = dict(heartbeat._mapping)

    last_timestamp = heartbeat_data["timestamp"]
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    difference = now - last_timestamp

    print("LAST:", last_timestamp)
    print("NOW:", now)
    print("DIFF:", difference.total_seconds())

    if difference.total_seconds() > 300:
        health = "offline"
    else:
        health = "online"

    return {
        "health": health,
        "battery": heartbeat_data["battery"],
        "status": heartbeat_data["status"],
        "last_heartbeat": heartbeat_data["timestamp"]
    }
    
@app.delete("/drones/{drone_id}")
def delete_drone(drone_id: int):
    db = SessionLocal()

    result = db.execute(
        text("DELETE FROM drones WHERE id = :id RETURNING *"),
        {"id": drone_id}
    )

    deleted_drone = result.fetchone()

    db.commit()
    db.close()

    if deleted_drone is None:
        return {"error": "Drone not found"}

    return {"message": "Drone deleted successfully"}

@app.post("/heartbeats")
def create_heartbeat(heartbeat: Heartbeat):
    db = SessionLocal()
    if heartbeat.battery < 0 or heartbeat.battery > 100:
        db.close()
        return {
            "error": "Battery must be between 0 and 100"
        }
    result = db.execute(
        text("SELECT * FROM drones WHERE id = :id"),
        {"id": heartbeat.drone_id}
    )

    drone = result.fetchone()

    if drone is None:
        db.close()
        return {"error": "Drone not found"}

    drone_data = dict(drone._mapping)

    if drone_data["auth_key"] != heartbeat.auth_key:
        db.close()
        return {"error": "Unauthorized drone"}

    result = db.execute(
        text("""
        INSERT INTO heartbeats (drone_id, battery, status, auth_key)
        VALUES (:drone_id, :battery, :status, :auth_key)
        RETURNING id, drone_id, battery, status, timestamp;
        """),
        {
            "drone_id": heartbeat.drone_id,
            "battery": heartbeat.battery,
            "status": heartbeat.status,
            "auth_key": heartbeat.auth_key
        }
    )

    new_heartbeat = result.fetchone()

    db.commit()
    db.close()

    return {
        "message": "Heartbeat registered successfully",
        "heartbeat": dict(new_heartbeat._mapping)
    }
    

@app.get("/heartbeats")
def get_heartbeats():
    db = SessionLocal()

    result = db.execute(text("SELECT * FROM heartbeats ORDER BY id"))
    heartbeats = result.fetchall()

    db.close()

    return [dict(h._mapping) for h in heartbeats]

@app.get("/heartbeats/{drone_id}")
def get_heartbeat(drone_id: int):
    db = SessionLocal()

    result = db.execute(
        text("SELECT * FROM heartbeats WHERE drone_id = :drone_id ORDER BY timestamp DESC"),
        {"drone_id": drone_id}
    )

    heartbeats = result.fetchall()

    db.close()

    return [dict(h._mapping) for h in heartbeats]


@app.post("/swarms")
def create_swarm(swarm: Swarm):
    db = SessionLocal()

    result = db.execute(
        text("""
        INSERT INTO swarms (name, mission)
        VALUES (:name, :mission)
        RETURNING id, name, mission;
        """),
        {
            "name": swarm.name,
            "mission": swarm.mission
        }
    )

    new_swarm = result.fetchone()

    db.commit()
    db.close()

    return {
        "message": "Swarm registered successfully",
        "swarm": dict(new_swarm._mapping)
    }

@app.get("/swarms")
def get_swarms():
    db = SessionLocal()

    result = db.execute(text("SELECT * FROM swarms ORDER BY id"))
    swarms = result.fetchall()

    db.close()

    return [dict(swarm._mapping) for swarm in swarms]

@app.get("/swarms/{swarm_id}")
def get_swarm(swarm_id: int):
    db = SessionLocal()

    result = db.execute(
        text("SELECT * FROM swarms WHERE id = :id"),
        {"id": swarm_id}
    )

    swarm = result.fetchone()
    db.close()

    if swarm is None:
        return {"error": "Swarm not found"}

    return dict(swarm._mapping)
        
@app.get("/swarms/{swarm_id}/members")
def get_swarm_members(swarm_id: int):
    db = SessionLocal()

    result = db.execute(
        text("""
        SELECT d.*
        FROM drones d
        JOIN swarm_members sm
            ON d.id = sm.drone_id
        WHERE sm.swarm_id = :swarm_id
        """),
        {"swarm_id": swarm_id}
    )

    members = result.fetchall()

    db.close()

    return [dict(member._mapping) for member in members]

@app.post("/swarms/{swarm_id}/members/{drone_id}")
def add_drone_to_swarm(swarm_id: int, drone_id: int):
    db = SessionLocal()

    swarm = db.execute(
        text("SELECT * FROM swarms WHERE id = :id"),
        {"id": swarm_id}
    ).fetchone()

    if swarm is None:
        db.close()
        return {"error": "Swarm not found"}

    drone = db.execute(
        text("SELECT * FROM drones WHERE id = :id"),
        {"id": drone_id}
    ).fetchone()

    if drone is None:
        db.close()
        return {"error": "Drone not found"}

    existing_member = db.execute(
        text("""
        SELECT * FROM swarm_members
        WHERE swarm_id = :swarm_id AND drone_id = :drone_id
        """),
        {
            "swarm_id": swarm_id,
            "drone_id": drone_id
        }
    ).fetchone()

    if existing_member is not None:
        db.close()
        return {"error": "Drone already exists in this swarm"}

    db.execute(
        text("""
        INSERT INTO swarm_members (swarm_id, drone_id)
        VALUES (:swarm_id, :drone_id)
        """),
        {
            "swarm_id": swarm_id,
            "drone_id": drone_id
        }
    )

    db.commit()
    db.close()

    return {
        "message": "Drone added to swarm successfully"
    }

@app.delete("/swarms/{swarm_id}/members/{drone_id}")
def remove_drone_from_swarm(swarm_id: int, drone_id: int):
    db = SessionLocal()

    result = db.execute(
        text("""
        DELETE FROM swarm_members
        WHERE swarm_id = :swarm_id AND drone_id = :drone_id
        RETURNING *
        """),
        {
            "swarm_id": swarm_id,
            "drone_id": drone_id
        }
    )

    deleted_member = result.fetchone()

    db.commit()
    db.close()

    if deleted_member is None:
        return {"error": "Drone is not in this swarm"}

    return {
        "message": "Drone removed from swarm successfully"
    }

@app.put("/drones/{drone_id}")
def update_drone(drone_id: int, updated_drone: UpdateDrone):
    db = SessionLocal()

    result = db.execute(
        text("""
        UPDATE drones
        SET name = :name,
            drone_type = :drone_type,
            serial_number = :serial_number
        WHERE id = :id
        RETURNING id, name, drone_type, serial_number, auth_key;
        """),
        {
            "id": drone_id,
            "name": updated_drone.name,
            "drone_type": updated_drone.drone_type,
            "serial_number": updated_drone.serial_number
        }
    )

    updated = result.fetchone()

    db.commit()
    db.close()

    if updated is None:
        return {"error": "Drone not found"}

    return {
        "message": "Drone updated successfully",
        "drone": dict(updated._mapping)
    }

@app.delete("/swarms/{swarm_id}")
def delete_swarm(swarm_id: int):
    db = SessionLocal()

    result = db.execute(
        text("DELETE FROM swarms WHERE id = :id RETURNING *"),
        {"id": swarm_id}
    )

    deleted_swarm = result.fetchone()

    db.commit()
    db.close()

    if deleted_swarm is None:
        return {"error": "Swarm not found"}

    return {
        "message": "Swarm deleted successfully"
    }