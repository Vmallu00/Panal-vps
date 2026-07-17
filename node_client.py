#!/usr/bin/env python3
import requests

class NodeClient:
    def __init__(self, api_url, api_key):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

    def _req(self, method, endpoint, data=None):
        url = f"{self.api_url}{endpoint}"
        try:
            r = requests.request(method, url, headers=self.headers, json=data, timeout=60)
            if r.status_code >= 400:
                return {"error": r.json().get("error", "Unknown error"), "status": r.status_code}
            return r.json()
        except Exception as e:
            return {"error": str(e), "status": 500}

    # ----- Health / Stats -----
    def health(self):
        return self._req("GET", "/health")

    def stats(self):
        return self._req("GET", "/api/stats")

    # ----- Container Management -----
    def create_container(self, name, cpu, ram_mb, disk_gb, ssh_port, image="lvm-vps:latest"):
        return self._req("POST", "/api/containers", data={
            "name": name,
            "cpu": cpu,
            "ram_mb": ram_mb,
            "disk_gb": disk_gb,
            "ssh_port": ssh_port,
            "image": image
        })

    def start(self, container_id):
        return self._req("POST", f"/api/containers/{container_id}/start")

    def stop(self, container_id):
        return self._req("POST", f"/api/containers/{container_id}/stop")

    def restart(self, container_id):
        return self._req("POST", f"/api/containers/{container_id}/restart")

    def delete(self, container_id):
        return self._req("DELETE", f"/api/containers/{container_id}/delete")

    def resize(self, container_id, cpu=None, ram_mb=None):
        data = {}
        if cpu is not None:
            data["cpu"] = cpu
        if ram_mb is not None:
            data["ram_mb"] = ram_mb
        return self._req("PUT", f"/api/containers/{container_id}/resize", data)

    # ----- Execute commands (tmate, file manager) -----
    def exec_cmd(self, container_id, cmd):
        return self._req("POST", f"/api/containers/{container_id}/exec", data={"cmd": cmd})

    def get_tmate(self, container_id):
        return self._req("GET", f"/api/containers/{container_id}/tmate")
