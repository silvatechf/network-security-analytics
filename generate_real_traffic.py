
import psycopg2
import random
from datetime import datetime, timedelta

DB_CONFIG = {
    "dbname": "network_security_audit",
    "user": "analyst_secops",
    "password": "VaultSecurePassword2026!",
    "host": "127.0.0.1",
    "port": "54321"
}

# Pool de orígenes reales de escaneo hostil
ACTORES_AMENAZA = [
    {"ip": "185.220.101.5",   "peso": 0.40, "desc": "Tor Exit Node"},
    {"ip": "218.92.0.142",    "peso": 0.25, "desc": "China Telecom (Botnet)"},
    {"ip": "193.106.191.50",  "peso": 0.15, "desc": "Scanner Ruso (Cluster)"},
    {"ip": "45.154.255.89",   "peso": 0.08, "desc": "DigitalOcean Droplet Hostil"},
    {"ip": "104.248.199.12",  "peso": 0.05, "desc": "VPN Ofuscada"},
    {"ip": "89.163.148.110",  "peso": 0.04, "desc": "Servidor Comprometido DE"},
    {"ip": "194.26.135.233",  "peso": 0.03, "desc": "Masscan Node"}
]

USUARIOS_OBJETIVO = ["root", "root", "root", "admin", "admin", "ubuntu", "oracle", "test", "git", "deploy"]

def generar_diluvio_datos():
    print("[*] Vaciando tabla de pruebas anterior (TRUNCATE)...")
    
    # IPs y sus probabilidades acumuladas para el random.choices()
    ips = [actor["ip"] for actor in ACTORES_AMENAZA]
    pesos = [actor["peso"] for actor in ACTORES_AMENAZA]

    ahora = datetime.now()
    tiempos = [ahora - timedelta(minutes=random.randint(1, 1440)) for _ in range(1482)]
    tiempos.sort() 

    query_insert = """
        INSERT INTO eventos_seguridad (fecha_evento, ip_origen, ip_ofuscada, mensaje_sistema) 
        VALUES (%s, %s, %s, %s);
    """

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE eventos_seguridad RESTART IDENTITY;")
                
                print("[*] Inyectando 1,482 eventos de denegación SSH con patrones reales...")
                for t in tiempos:
                    ip_seleccionada = random.choices(ips, weights=pesos, k=1)[0]
                    user = random.choice(USUARIOS_OBJETIVO)
                    puerto_efimero = random.randint(32000, 60000)
                    
                    fecha_str = t.strftime("%b %d %H:%M:%S")
                    ip_defanged = ip_seleccionada.replace(".", "[.]")
                    payload_log = f"Failed password for {user} from {ip_seleccionada} port {puerto_efimero} ssh2"
                    
                    cur.execute(query_insert, (fecha_str, ip_seleccionada, ip_defanged, payload_log))
                
                conn.commit()
        print("[✅] BASE DE DATOS REALISTA CARGADA: 1,482 incidentes listos para análisis.")

    except Exception as e:
        print(f"[!] Error de inyección: {e}")

if __name__ == "__main__":
    generar_diluvio_datos()