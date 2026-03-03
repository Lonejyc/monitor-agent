from flask import Flask, jsonify
from flask_cors import CORS
import psutil
import platform
import time
import os

app = Flask(__name__)
# Autorise les appels Cross-Origin (utile si vous testez le DNS custom en direct)
CORS(app)

def get_size(bytes, suffix="GB"):
    """Formatte les octets en Giga-octets"""
    factor = 1024**3
    return f"{round(bytes / factor, 2)} {suffix}"

@app.route('/api/stats')
def get_stats():
    # Informations CPU détaillées
    cpu_freq = psutil.cpu_freq()

    # Tentative de récupération de la température (Linux uniquement)
    temps = {}
    try:
        if hasattr(psutil, "sensors_temperatures"):
            sensors = psutil.sensors_temperatures()
            if 'coretemp' in sensors:
                temps = {"current": sensors['coretemp'][0].current}
    except Exception:
        temps = {"error": "Non disponible"}

    # Statistiques Réseau
    net_io = psutil.net_io_counters()

    return jsonify({
        "hostname": platform.node(),
        "os": {
            "platform": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine()
        },
        "uptime": {
            "seconds": int(time.time() - psutil.boot_time()),
            "boot_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(psutil.boot_time()))
        },
        "cpu": {
            "usage_percent": psutil.cpu_percent(interval=1),
            "usage_per_cpu": psutil.cpu_percent(interval=None, percpu=True),
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "frequency_mhz": cpu_freq.current if cpu_freq else "N/A",
            "temperature": temps
        },
        "memory": {
            "total": get_size(psutil.virtual_memory().total),
            "available": get_size(psutil.virtual_memory().available),
            "used": get_size(psutil.virtual_memory().used),
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total": get_size(psutil.disk_usage('/').total),
            "used": get_size(psutil.disk_usage('/').used),
            "free": get_size(psutil.disk_usage('/').free),
            "percent": psutil.disk_usage('/').percent
        },
        "network": {
            "sent": f"{round(net_io.bytes_sent / (1024**2), 2)} MB",
            "recv": f"{round(net_io.bytes_recv / (1024**2), 2)} MB"
        },
        "load_average": os.getloadavg() if hasattr(os, "getloadavg") else "N/A"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)