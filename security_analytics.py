#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEMA LOCAL DE LOGS Y ANALÍTICA DE SEGURIDAD (LAB 6)
Autor: Fernando Silva Felix
Descripción: Engine local para el procesamiento de logs de autenticación Unix,
             saneamiento de datos y persistencia segura en base de datos relacional.
"""

import re
import psycopg2
import sys
import json

# Ruta nativa del log de autenticación en Linux
AUTH_LOG_PATH = "/var/log/auth.log"

# Configuración de conectividad local hacia el contenedor Docker
DB_CONFIG = {
    "dbname": "network_security_audit",
    "user": "analyst_secops",
    "password": "VaultSecurePassword2026!",
    "host": "127.0.0.1",
    "port": "54321"
}

def inicializar_base_datos():
    """Garantiza la estructura relacional básica para el almacenamiento de eventos."""
    query_tabla = """
    CREATE TABLE IF NOT EXISTS eventos_seguridad (
        id SERIAL PRIMARY KEY,
        fecha_evento VARCHAR(50) NOT NULL,
        ip_origen VARCHAR(50) NOT NULL,
        ip_ofuscada VARCHAR(50) NOT NULL,
        mensaje_sistema TEXT NOT NULL
    );
    """
    try:
        with psycopg2.connect(**DB_CONFIG) as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(query_tabla)
                conexion.commit()
                print("[*] INFRAESTRUCTURA: Base de datos y tablas inicializadas correctamente en Docker.")
    except psycopg2.OperationalError as e:
        print(f"[!] ERROR DE CONEXIÓN: Verifique el estado del contenedor en el puerto {DB_CONFIG['port']}. Detalles: {e}")
        sys.exit(1)

def registrar_evento_seguro(fecha, ip, defanged, mensaje):
    """
    Inserta las alertas mitigando SQL Injection mediante consultas parametrizadas.
    Garantiza que las entradas externas no alteren la lógica del motor de base de datos.
    """
    query_insercion = """
        INSERT INTO eventos_seguridad (fecha_evento, ip_origen, ip_ofuscada, mensaje_sistema) 
        VALUES (%s, %s, %s, %s);
    """
    try:
        with psycopg2.connect(**DB_CONFIG) as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(query_insercion, (fecha, ip, defanged, mensaje))
                conexion.commit()
    except psycopg2.DatabaseError as e:
        print(f"[!] ERROR SQL: No se pudo persistir el registro: {e}")

def procesar_logs_unix():
    print("[*] PROCESO: Analizando registros de red locales...")
    patron_ip = r'from \b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    
    try:
        inicializar_base_datos()
        alertas_guardadas = 0
        
        with open(AUTH_LOG_PATH, 'r') as archivo_logs:
            for linea in archivo_logs:
                if "Failed password for" in linea or "Invalid user" in linea:
                    linea_limpia = linea.strip()
                    buscar_ip = re.search(patron_ip, linea_limpia)
                    
                    ip_detectada = buscar_ip.group().replace("from ", "") if buscar_ip else "0.0.0.0"
                    fecha_evento = linea_limpia[:15]
                    ip_defanged = ip_detectada.replace(".", "[.]")
                    
                    # Persistencia local indexada
                    registrar_evento_seguro(fecha_evento, ip_detectada, ip_defanged, linea_limpia)
                    alertas_guardadas += 1
                    
        print(f"[✅] ÉXITO: Pipeline finalizado. {alertas_guardadas} eventos reales persistidos en PostgreSQL.")
        
    except PermissionError:
        print("[!] ERROR DE PRIVILEGIOS: Ejecute el script con elevación: 'sudo python3 security_analytics.py'")
    except FileNotFoundError:
        print(f"[!] ERROR: El fichero real {AUTH_LOG_PATH} no existe en este servidor.")

if __name__ == "__main__":
    procesar_logs_unix()