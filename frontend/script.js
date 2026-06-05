async function createDrone() {
    const name = document.getElementById("droneName").value;
    const drone_type = document.getElementById("droneType").value;
    const serial_number = document.getElementById("droneSerial").value;

    const response = await fetch("http://127.0.0.1:8000/drones", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            drone_type: drone_type,
            serial_number: serial_number
        })
    });

    const data = await response.json();

    localStorage.setItem(
        `drone_key_${data.drone.id}`,
        data.drone.auth_key
    );

    alert("Drone created and auth key saved automatically");

    loadDrones();
}

async function loadDrones() {
    const response = await fetch("http://127.0.0.1:8000/drones");
    const drones = await response.json();

    const table = document.getElementById("droneTable");
    table.innerHTML = "";

  drones.forEach(drone => {

    if (drone.auth_key) {
        localStorage.setItem(
            `drone_key_${drone.id}`,
            drone.auth_key
        );
    }
        table.innerHTML += `
            <tr>
                <td>${drone.id}</td>
                <td>${drone.name}</td>
                <td>${drone.drone_type}</td>
                <td>${drone.serial_number}</td>
                <td id="health-${drone.id}">Not checked</td>
                <td id="status-${drone.id}">-</td>
                <td id="battery-${drone.id}">-</td>
                <td>
                    <button onclick="checkHealth(${drone.id})">Check Health</button>
                    <button onclick="deleteDrone(${drone.id})">Delete</button>
                </td>
            </tr>
        `;
    });
}

async function deleteDrone(id) {
    await fetch(`http://127.0.0.1:8000/drones/${id}`, {
        method: "DELETE"
    });

    loadDrones();
}

async function checkHealth(id) {
    const response = await fetch(`http://127.0.0.1:8000/drones/${id}/health`);
    const data = await response.json();

    document.getElementById(`health-${id}`).innerHTML = data.health || "unknown";
    document.getElementById(`status-${id}`).innerHTML = data.status || "-";
    document.getElementById(`battery-${id}`).innerHTML = data.battery !== undefined ? data.battery + "%" : "-";
}

async function sendHeartbeat() {
    const drone_id = Number(document.getElementById("heartbeatDroneId").value);
    const battery = Number(document.getElementById("heartbeatBattery").value);
    if (battery < 0 || battery > 100) {
        alert("Battery must be between 0 and 100");
        return;
    }
    const status = document.getElementById("heartbeatStatus").value;

    const auth_key = localStorage.getItem(`drone_key_${drone_id}`);

    if (!auth_key) {
        alert("Auth key not found. Create this drone from frontend first.");
        return;
    }

    const response = await fetch("http://127.0.0.1:8000/heartbeats", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            drone_id: drone_id,
            battery: battery,
            status: status,
            auth_key: auth_key
        })
    });

    const data = await response.json();

    alert(JSON.stringify(data, null, 2));

    checkHealth(drone_id);
}
async function createSwarm() {
    const name = document.getElementById("swarmName").value;
    const mission = document.getElementById("swarmMission").value;

    const response = await fetch("http://127.0.0.1:8000/swarms", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            mission: mission
        })
    });

    const data = await response.json();

    alert(JSON.stringify(data, null, 2));

    loadSwarms();
}

async function loadSwarms() {
    const response = await fetch("http://127.0.0.1:8000/swarms");
    const swarms = await response.json();

    const table = document.getElementById("swarmTable");
    table.innerHTML = "";

    swarms.forEach(swarm => {
        table.innerHTML += `
            <tr>
                <td>${swarm.id}</td>
                <td>${swarm.name}</td>
                <td>${swarm.mission}</td>
                <td>
                    <button onclick="viewSwarmMembers(${swarm.id}, '${swarm.name}')">
                        View Members
                    </button>
                    <button onclick="deleteSwarm(${swarm.id})">
                        Delete
                    </button>
                </td>
            </tr>
        `;
    });
}

async function viewSwarmMembers(swarm_id, swarm_name) {
    document.getElementById("memberSwarmId").value = swarm_id;
    document.getElementById("selectedSwarmTitle").innerHTML =
        `Members of Swarm ${swarm_id}: ${swarm_name}`;

    const response = await fetch(
        `http://127.0.0.1:8000/swarms/${swarm_id}/members`
    );

    const members = await response.json();

    const table = document.getElementById("membersTable");
    table.innerHTML = "";

    members.forEach(drone => {
        table.innerHTML += `
            <tr>
                <td>${drone.id}</td>
                <td>${drone.name}</td>
                <td>${drone.drone_type}</td>
                <td>${drone.serial_number}</td>
            </tr>
        `;
    });
}

async function addDroneToSwarm() {
    const swarm_id = Number(document.getElementById("memberSwarmId").value);
    const drone_id = Number(document.getElementById("memberDroneId").value);

    const response = await fetch(
        `http://127.0.0.1:8000/swarms/${swarm_id}/members/${drone_id}`,
        { method: "POST" }
    );

    const data = await response.json();
    alert(JSON.stringify(data, null, 2));

    viewSwarmMembers(swarm_id, `Swarm ${swarm_id}`);
}

async function removeDroneFromSwarm() {
    const swarm_id = Number(document.getElementById("memberSwarmId").value);
    const drone_id = Number(document.getElementById("memberDroneId").value);

    const response = await fetch(
        `http://127.0.0.1:8000/swarms/${swarm_id}/members/${drone_id}`,
        { method: "DELETE" }
    );

    const data = await response.json();
    alert(JSON.stringify(data, null, 2));

    viewSwarmMembers(swarm_id, `Swarm ${swarm_id}`);
}

async function deleteSwarm(id) {
    await fetch(`http://127.0.0.1:8000/swarms/${id}`, {
        method: "DELETE"
    });

    loadSwarms();

    document.getElementById("membersTable").innerHTML = "";
    document.getElementById("selectedSwarmTitle").innerHTML = "No swarm selected";
}
async function loadDashboard() {

    const dronesResponse = await fetch(
        "http://127.0.0.1:8000/drones"
    );

    const drones = await dronesResponse.json();

    const swarmsResponse = await fetch(
        "http://127.0.0.1:8000/swarms"
    );

    const swarms = await swarmsResponse.json();

    let online = 0;
    let offline = 0;

    for (const drone of drones) {

        try {

            const healthResponse = await fetch(
                `http://127.0.0.1:8000/drones/${drone.id}/health`
            );

            const healthData = await healthResponse.json();

            if (healthData.health === "online") {
                online++;
            } else {
                offline++;
            }

        } catch {

            offline++;

        }
    }

    document.getElementById("totalDrones").innerHTML =
        drones.length;

    document.getElementById("onlineDrones").innerHTML =
        online;

    document.getElementById("offlineDrones").innerHTML =
        offline;

    document.getElementById("totalSwarms").innerHTML =
        swarms.length;
}
loadDashboard();

