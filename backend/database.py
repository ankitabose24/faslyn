"""
Lightweight SQLite Database Layer for Faslyn
============================================
Zero-configuration, zero-cost, persistent embedded storage using Python's built-in sqlite3.
Stores farmer session profiles, telemetry snapshots, and regenerative advisory audit trails.
Database file is stored locally at `data/faslyn.db`.
"""

import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "faslyn.db")


def get_connection() -> sqlite3.Connection:
    """Ensure directory exists and return an active SQLite connection."""
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        fallback_path = os.path.join(os.environ.get("TMPDIR", "/tmp"), "faslyn.db")
        conn = sqlite3.connect(fallback_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn


def init_db() -> None:
    """Initialize database tables if they do not already exist."""
    conn = get_connection()
    with conn:
        cursor = conn.cursor()
        
        # 1. Farmers / Cooperative Members
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS farmers (
                id TEXT PRIMARY KEY,
                phone TEXT,
                name TEXT NOT NULL,
                region TEXT NOT NULL,
                role TEXT NOT NULL,
                hub_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Environmental Telemetry Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                hub_name TEXT,
                soil_moisture REAL,
                soil_temp REAL,
                air_temp REAL,
                solar_radiation REAL,
                precipitation REAL,
                root_zone_wetness REAL,
                source TEXT
            )
        """)

        # 3. Advisory & Regenerative Plan History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advisories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                farmer_id TEXT,
                language TEXT,
                advisory_text TEXT,
                recommended_crop TEXT,
                rotation_partner TEXT,
                soil_amendment TEXT,
                full_json TEXT
            )
        """)
    conn.close()


def upsert_farmer(farmer_id: str, phone: str, name: str, region: str, role: str, hub_name: str) -> None:
    """Insert or update farmer profile upon login."""
    init_db()
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO farmers (id, phone, name, region, role, hub_name, last_login)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                phone = excluded.phone,
                name = excluded.name,
                region = excluded.region,
                role = excluded.role,
                hub_name = excluded.hub_name,
                last_login = CURRENT_TIMESTAMP
        """, (farmer_id, phone, name, region, role, hub_name))
    conn.close()


def log_telemetry_snapshot(lat: float, lon: float, hub_name: str, telemetry: dict, satellite: dict) -> None:
    """Record a telemetry snapshot for longitudinal audit tracking."""
    init_db()
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO telemetry_logs (
                lat, lon, hub_name, soil_moisture, soil_temp, air_temp,
                solar_radiation, precipitation, root_zone_wetness, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lat, lon, hub_name,
            telemetry.get("soil_moisture"),
            telemetry.get("soil_temp"),
            telemetry.get("air_temp"),
            satellite.get("solar_radiation"),
            satellite.get("precipitation"),
            satellite.get("root_zone_soil_wetness"),
            telemetry.get("source", "open-meteo"),
        ))
    conn.close()


def log_advisory_record(farmer_id: str, language: str, text: str, crop_rec: Optional[dict] = None) -> None:
    """Store generated advisory and regenerative crop recommendations."""
    init_db()
    conn = get_connection()
    crop_rec = crop_rec or {}
    with conn:
        conn.execute("""
            INSERT INTO advisories (
                farmer_id, language, advisory_text, recommended_crop,
                rotation_partner, soil_amendment, full_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            farmer_id,
            language,
            text,
            crop_rec.get("recommended_crop", ""),
            crop_rec.get("rotation_partner", ""),
            crop_rec.get("soil_amendment", ""),
            json.dumps(crop_rec) if crop_rec else None,
        ))
    conn.close()


def get_recent_telemetry(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve recent telemetry log entries."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM telemetry_logs ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
