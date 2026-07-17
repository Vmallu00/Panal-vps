#!/usr/bin/env python3
"""
LVM Panel - Node Agent
Run this on each worker VPS.
Set environment variables: NODE_API_KEY and AGENT_PORT (default 9000)
"""
import os
import hmac
import docker
import psutil
from flask import Flask, request, jsonify
from functools import wraps

# ---------- CONFIG ----------
API_KEY = os.environ.get("NODE_API_KEY", "change-me-now")
PORT = int(os.environ.get("AGENT_PORT", 9000))
# ----------------------------

app = Flask(__name__)
docker_client = docker.from_env()

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        provided = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(provided, API_KEY):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# ------------------- HEALTH & STATS -------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/api/stats", methods=["GET"])
@require_auth
def stats():
    try:
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.5)
        disk = psutil.disk_usage("/")
        return jsonify({
            "ram_total": mem.total // (1024**2),      # MB
            "ram_used": mem.used // (1024**2),
            "ram_free": mem.free // (1024**2),
            "ram_percent": mem.percent,
            "cpu_percent": cpu,
            "disk_total": disk.total // (1024**3),    # GB
            "disk_used": disk.used // (1024**3),
            "disk_free": disk.free // (1024**3),
            "disk_percent": disk.percent,
            "container_count": len(docker_client.containers.list(all=True))
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------- CONTAINER CRUD -------------------
@app.route("/api/containers", methods=["POST"])
@require_auth
def create_container():
    data = request.get_json()
    required = ["name", "cpu", "ram_mb", "disk_gb", "ssh_port"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Ensure private network exists
        try:
            docker_client.networks.get("lvm_net")
        except docker.errors.NotFound:
            docker_client.networks.create(
                "lvm_net",
                driver="bridge",
                ipam=docker.types.IPAMConfig(
                    pool_configs=[docker.types.IPAMPool(subnet="10.77.0.0/16")]
                )
            )

        # Pull image if missing
        image = data.get("image", "lvm-vps:latest")
        try:
            docker_client.images.get(image)
        except docker.errors.ImageNotFound:
            docker_client.images.pull(image)

        # Create container
        container = docker_client.containers.create(
            image=image,
            name=data["name"],
            hostname=data["name"],
            nano_cpus=int(data["cpu"] * 1e9),
            mem_limit=f"{data['ram_mb']}m",
            storage_opt={"size": f"{data['disk_gb']}G"},
            ports={"22/tcp": data["ssh_port"]},
            network="lvm_net",
            detach=True,
            stdin_open=True,
            tty=True,
            privileged=False
        )
        container.start()

        # Get private IP
        net_data = container.attrs["NetworkSettings"]["Networks"]["lvm_net"]
        private_ip = net_data["IPAddress"]

        return jsonify({
            "container_id": container.id,
            "private_ip": private_ip,
            "ssh_port": data["ssh_port"]
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/containers/<cid>/start", methods=["POST"])
@require_auth
def start_container(cid):
    try:
        docker_client.containers.get(cid).start()
        return jsonify({"status": "started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/containers/<cid>/stop", methods=["POST"])
@require_auth
def stop_container(cid):
    try:
        docker_client.containers.get(cid).stop()
        return jsonify({"status": "stopped"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/containers/<cid>/restart", methods=["POST"])
@require_auth
def restart_container(cid):
    try:
        docker_client.containers.get(cid).restart()
        return jsonify({"status": "restarted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/containers/<cid>/delete", methods=["DELETE"])
@require_auth
def delete_container(cid):
    try:
        c = docker_client.containers.get(cid)
        c.stop()
        c.remove()
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/containers/<cid>/resize", methods=["PUT"])
@require_auth
def resize_container(cid):
    data = request.get_json()
    try:
        c = docker_client.containers.get(cid)
        if "cpu" in data:
            c.update(nano_cpus=int(data["cpu"] * 1e9))
        if "ram_mb" in data:
            c.update(mem_limit=f"{data['ram_mb']}m")
        return jsonify({"status": "updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/containers/<cid>/exec", methods=["POST"])
@require_auth
def exec_command(cid):
    data = request.get_json()
    cmd = data.get("cmd", ["/bin/bash"])
    try:
        c = docker_client.containers.get(cid)
        exec_res = c.exec_run(cmd, stdout=True, stderr=True, tty=False)
        return jsonify({
            "exit_code": exec_res.exit_code,
            "output": exec_res.output.decode("utf-8", errors="ignore")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/containers/<cid>/tmate", methods=["GET"])
@require_auth
def get_tmate(cid):
    try:
        c = docker_client.containers.get(cid)
        exec_res = c.exec_run(["tmate", "-F"], stdout=True, stderr=True, tty=False)
        output = exec_res.output.decode("utf-8").strip()
        return jsonify({"tmate_string": output})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
