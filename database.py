"""
SQLite Database module for persisting daily recovery records, targets, and historical snapshots.
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), "repayments.db")


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Daily Summary Snapshots Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                record_date TEXT PRIMARY KEY,
                month TEXT,
                total_target REAL,
                total_achieved REAL,
                total_variance REAL,
                remaining_days INTEGER,
                daily_required REAL,
                total_contracts INTEGER,
                iresha_target REAL,
                iresha_achieved REAL,
                dila_target REAL,
                dila_achieved REAL,
                notes TEXT,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Daily Individual Officer Records Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_officer_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_date TEXT,
                officer_id TEXT,
                officer_name TEXT,
                nic TEXT,
                team_key TEXT,
                team_name TEXT,
                target REAL,
                achieved REAL,
                variance REAL,
                daily_required REAL,
                contracts_count INTEGER,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(record_date, officer_id) ON CONFLICT REPLACE
            )
        """)

        # 3. Settings Table (for target customization & phone numbers)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()


def save_daily_snapshot(record_date, summary_data, officer_records, notes=""):
    """
    Save or update a daily snapshot of repayment performance.
    """
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        
        month = summary_data.get('month', record_date[:7] if len(record_date) >= 7 else '')
        
        cursor.execute("""
            INSERT INTO daily_snapshots (
                record_date, month, total_target, total_achieved, total_variance,
                remaining_days, daily_required, total_contracts,
                iresha_target, iresha_achieved, dila_target, dila_achieved,
                notes, saved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(record_date) DO UPDATE SET
                month=excluded.month,
                total_target=excluded.total_target,
                total_achieved=excluded.total_achieved,
                total_variance=excluded.total_variance,
                remaining_days=excluded.remaining_days,
                daily_required=excluded.daily_required,
                total_contracts=excluded.total_contracts,
                iresha_target=excluded.iresha_target,
                iresha_achieved=excluded.iresha_achieved,
                dila_target=excluded.dila_target,
                dila_achieved=excluded.dila_achieved,
                notes=excluded.notes,
                saved_at=CURRENT_TIMESTAMP
        """, (
            record_date,
            month,
            summary_data.get('total_target', 0.0),
            summary_data.get('total_achieved', 0.0),
            summary_data.get('total_variance', 0.0),
            summary_data.get('remaining_days', 17),
            summary_data.get('daily_required', 0.0),
            summary_data.get('total_contracts', 0),
            summary_data.get('iresha_target', 0.0),
            summary_data.get('iresha_achieved', 0.0),
            summary_data.get('dila_target', 0.0),
            summary_data.get('dila_achieved', 0.0),
            notes,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

        for rec in officer_records:
            cursor.execute("""
                INSERT INTO daily_officer_records (
                    record_date, officer_id, officer_name, nic,
                    team_key, team_name, target, achieved, variance,
                    daily_required, contracts_count, saved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(record_date, officer_id) DO UPDATE SET
                    officer_name=excluded.officer_name,
                    nic=excluded.nic,
                    team_key=excluded.team_key,
                    team_name=excluded.team_name,
                    target=excluded.target,
                    achieved=excluded.achieved,
                    variance=excluded.variance,
                    daily_required=excluded.daily_required,
                    contracts_count=excluded.contracts_count,
                    saved_at=CURRENT_TIMESTAMP
            """, (
                record_date,
                rec.get('officer_id', ''),
                rec.get('officer_name', ''),
                rec.get('nic', ''),
                rec.get('team_key', ''),
                rec.get('team_name', ''),
                rec.get('target', 0.0),
                rec.get('achieved', 0.0),
                rec.get('variance', 0.0),
                rec.get('daily_required', 0.0),
                rec.get('contracts_count', 0),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))

        conn.commit()


def get_saved_dates():
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT record_date FROM daily_snapshots ORDER BY record_date DESC")
        rows = cursor.fetchall()
        return [r[0] for r in rows]


def get_snapshot(record_date):
    init_db()
    with get_connection() as conn:
        summary_df = pd.read_sql_query(
            "SELECT * FROM daily_snapshots WHERE record_date = ?", conn, params=(record_date,)
        )
        officers_df = pd.read_sql_query(
            "SELECT * FROM daily_officer_records WHERE record_date = ? ORDER BY achieved DESC",
            conn, params=(record_date,)
        )
        summary = summary_df.iloc[0].to_dict() if not summary_df.empty else None
        return summary, officers_df


def get_all_snapshots():
    init_db()
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM daily_snapshots ORDER BY record_date ASC", conn)
        return df


def get_officer_history(officer_id=None):
    init_db()
    with get_connection() as conn:
        if officer_id:
            query = "SELECT * FROM daily_officer_records WHERE officer_id = ? ORDER BY record_date ASC"
            return pd.read_sql_query(query, conn, params=(officer_id,))
        else:
            query = "SELECT * FROM daily_officer_records ORDER BY record_date ASC, officer_name ASC"
            return pd.read_sql_query(query, conn)


def delete_snapshot(record_date):
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_snapshots WHERE record_date = ?", (record_date,))
        cursor.execute("DELETE FROM daily_officer_records WHERE record_date = ?", (record_date,))
        conn.commit()


def save_setting(key, value):
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()


def get_setting(key, default=None):
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default


def get_officer_phones(roster_officers=None):
    """
    Get stored officer phone numbers from settings with fallback to roster defaults.
    """
    import json
    raw = get_setting("officer_phones", None)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass

    phones = {}
    if roster_officers:
        for o in roster_officers:
            phones[o['id']] = o.get('defaultPhone', '0770000000')
    return phones


def save_officer_phones(phones_dict):
    """
    Persist officer phone numbers into settings table.
    """
    import json
    save_setting("officer_phones", json.dumps(phones_dict))
