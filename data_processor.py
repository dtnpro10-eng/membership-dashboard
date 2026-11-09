"""
Data processing module for parsing Excel/CSV files, Google Sheets,
matching officers, calculating working days, and computing daily repayment analytics.
"""

import re
import calendar
from datetime import datetime
import pandas as pd
import requests
from io import BytesIO, StringIO
from roster import ROSTER_IRESHA, ROSTER_DILA, TEAM_TARGET_IRESHA, TEAM_TARGET_DILA, DEFAULT_GOOGLE_SHEET_URL


def calculate_remaining_working_days(date_obj_or_str):
    """
    Calculates remaining working days in the month excluding Saturdays and Sundays.
    """
    try:
        if isinstance(date_obj_or_str, str):
            dt = datetime.strptime(date_obj_or_str[:10], "%Y-%m-%d")
        elif isinstance(date_obj_or_str, (datetime, pd.Timestamp)):
            dt = date_obj_or_str
        else:
            return 17

        year = dt.year
        month = dt.month
        current_day = dt.day

        _, last_day = calendar.monthrange(year, month)
        working_days = 0

        for day in range(current_day, last_day + 1):
            check_date = datetime(year, month, day)
            # Monday=0, Sunday=6. Exclude Saturday (5) and Sunday (6)
            if check_date.weekday() < 5:
                working_days += 1

        return max(1, working_days)
    except Exception:
        return 17


def match_officer(raw_text):
    """
    Matches raw string against predefined rosters using tokens.
    """
    if pd.isna(raw_text) or not str(raw_text).strip():
        return {
            'teamKey': 'UNASSIGNED',
            'teamName': 'Unassigned',
            'officerId': 'unknown',
            'displayName': 'Unknown',
            'shortName': 'Unknown',
            'nic': '-'
        }

    str_val = str(raw_text).strip().lower()

    for m in ROSTER_IRESHA:
        for t in m['tokens']:
            if t.lower() in str_val:
                return {
                    'teamKey': 'TEAM_IRESHA',
                    'teamName': 'Group Iresha',
                    'officerId': m['id'],
                    'displayName': m['displayName'],
                    'shortName': m['shortName'],
                    'nic': m['nic']
                }

    for m in ROSTER_DILA:
        for t in m['tokens']:
            if t.lower() in str_val:
                return {
                    'teamKey': 'TEAM_DILA',
                    'teamName': 'Group Dila',
                    'officerId': m['id'],
                    'displayName': m['displayName'],
                    'shortName': m['shortName'],
                    'nic': m['nic']
                }

    clean_name = str(raw_text).strip()
    return {
        'teamKey': 'UNASSIGNED',
        'teamName': 'Other / Unassigned',
        'officerId': f'other_{clean_name}',
        'displayName': clean_name,
        'shortName': clean_name[:20],
        'nic': '-'
    }


def auto_detect_columns(df):
    """
    Detects relevant columns for Date, Officer, Amount, and Contract No.
    """
    cols = list(df.columns)
    
    date_col = next((c for c in cols if re.search(r'transaction\s*date|txn\s*date|date', str(c), re.I)), None)
    officer_col = next((c for c in cols if re.search(r'receipted\s*by|collected\s*by|officer|collector', str(c), re.I)), None)
    amount_col = next((c for c in cols if re.search(r'repayments?|amount|collected|paid', str(c), re.I)), None)
    contract_col = next((c for c in cols if re.search(r'account\s*id|contract.*no|contract|agreement|loan.*no|loan.*id|acc.*no', str(c), re.I)), None)

    return {
        'date_col': date_col or cols[0],
        'officer_col': officer_col or (cols[1] if len(cols) > 1 else cols[0]),
        'amount_col': amount_col or (cols[2] if len(cols) > 2 else cols[0]),
        'contract_col': contract_col or (cols[3] if len(cols) > 3 else 'Contract_No')
    }


def clean_amount(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = re.sub(r'[^0-9.-]', '', str(val))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def clean_date_str(val):
    if pd.isna(val) or val is None or str(val).strip() == '':
        return datetime.now().strftime('%Y-%m-%d')
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime('%Y-%m-%d')
    s = str(val).strip().split()[0].replace('/', '-')
    
    # Check if YYYY-MM-DD
    match_ymd = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})', s)
    if match_ymd:
        y, m, d = match_ymd.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        
    # Check if DD-MM-YYYY
    match_dmy = re.match(r'^(\d{1,2})-(\d{1,2})-(\d{2,4})', s)
    if match_dmy:
        d, m, y = match_dmy.groups()
        y_int = int(y)
        if y_int < 100:
            y_int += 2000
        return f"{y_int:04d}-{int(m):02d}-{int(d):02d}"
        
    try:
        dt = pd.to_datetime(s, errors='coerce')
        if pd.notna(dt):
            return dt.strftime('%Y-%m-%d')
    except Exception:
        pass
    return datetime.now().strftime('%Y-%m-%d')


def read_uploaded_file(uploaded_file):
    """
    Reads an uploaded file buffer (.xlsx, .xls, .csv).
    Auto-detects header row if not row 0.
    """
    name = uploaded_file.name.lower()
    if name.endswith('.csv'):
        content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
        df = pd.read_csv(StringIO(content))
    else:
        # Excel file: scan first 25 rows to find header
        raw_df = pd.read_excel(uploaded_file, header=None)
        best_row = 0
        best_score = -1
        for r in range(min(25, len(raw_df))):
            row_str = " ".join([str(x).lower() for x in raw_df.iloc[r].dropna()])
            score = 0
            if re.search(r'transaction\s*date|txn\s*date', row_str): score += 5
            if re.search(r'receipted\s*by|collected\s*by', row_str): score += 5
            if re.search(r'repayment|amount', row_str): score += 4
            if score > best_score:
                best_score = score
                best_row = r
        
        uploaded_file.seek(0)
        df = pd.read_excel(uploaded_file, header=best_row)
    
    # Drop completely empty rows and columns
    df = df.dropna(how='all').dropna(axis=1, how='all')
    return df


def fetch_google_sheet(sheet_url=None):
    """
    Converts a Google Sheet URL to direct CSV download and parses it into a DataFrame.
    """
    if not sheet_url:
        sheet_url = DEFAULT_GOOGLE_SHEET_URL
    sheet_id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
    if not sheet_id_match:
        raise ValueError("වලංගු Google Sheet Link එකක් නොවේ.")
    sheet_id = sheet_id_match.group(1)
    
    gid_match = re.search(r'[#&?]gid=([0-9]+)', sheet_url)
    gid = gid_match.group(1) if gid_match else "0"

    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    resp = requests.get(export_url, timeout=15)
    if resp.status_code != 200:
        raise ConnectionError("Google Sheet වෙත සම්බන්ධ විය නොහැක. 'Anyone with the link can view' ලෙස සකසා ඇත්දැයි පරීක්ෂා කරන්න.")

    df = pd.read_csv(StringIO(resp.text))
    return df


def process_transactions_dataframe(df, mapping=None, custom_targets=None):
    """
    Processes transaction records and returns standardized rows.
    """
    if mapping is None:
        mapping = auto_detect_columns(df)
        
    date_col = mapping['date_col']
    officer_col = mapping['officer_col']
    amount_col = mapping['amount_col']
    contract_col = mapping.get('contract_col')

    records = []
    for idx, row in df.iterrows():
        raw_officer = row.get(officer_col, '')
        match = match_officer(raw_officer)
        raw_date = row.get(date_col)
        clean_date = clean_date_str(raw_date)
        amt = clean_amount(row.get(amount_col))
        
        contract = ''
        if contract_col and contract_col in row:
            contract = str(row[contract_col]).strip()
        if not contract or contract in ['nan', 'None', '-', '0']:
            contract = f"CTR-{idx+1}"

        records.append({
            'date': clean_date,
            'month': clean_date[:7],
            'officer_id': match['officerId'],
            'officer_name': match['shortName'],
            'full_officer_name': match['displayName'],
            'nic': match['nic'],
            'team_key': match['teamKey'],
            'team_name': match['teamName'],
            'amount': amt,
            'contract': contract
        })

    return pd.DataFrame(records)


def compute_dashboard_metrics(processed_df, selected_month=None, selected_date=None, working_days=None, custom_targets=None):
    """
    Aggregates data for Group Iresha, Group Dila, and each individual officer.
    Supports filtering by month and date.
    """
    all_officers = ROSTER_IRESHA + ROSTER_DILA
    target_map = {o['id']: o['defaultTarget'] for o in all_officers}
    if custom_targets:
        target_map.update(custom_targets)

    df_filtered = processed_df.copy() if not processed_df.empty else pd.DataFrame()

    # Filter by month if specified
    if not df_filtered.empty and selected_month and selected_month != "ALL":
        df_filtered = df_filtered[df_filtered['month'] == selected_month]

    # Filter by specific date if specified
    if not df_filtered.empty and selected_date and selected_date != "ALL":
        df_filtered = df_filtered[df_filtered['date'] == selected_date]

    if working_days is None:
        ref_date = selected_date if (selected_date and selected_date != "ALL") else datetime.now().strftime('%Y-%m-%d')
        working_days = calculate_remaining_working_days(ref_date)

    # Aggregates by officer
    grouped = {}
    for o in all_officers:
        team_key = 'TEAM_IRESHA' if any(x['id'] == o['id'] for x in ROSTER_IRESHA) else 'TEAM_DILA'
        team_name = 'Group Iresha' if team_key == 'TEAM_IRESHA' else 'Group Dila'
        target = target_map.get(o['id'], o['defaultTarget'])
        grouped[o['id']] = {
            'officer_id': o['id'],
            'officer_name': o['shortName'],
            'displayName': o['displayName'],
            'nic': o['nic'],
            'team_key': team_key,
            'team_name': team_name,
            'target': target,
            'achieved': 0.0,
            'contracts': set(),
            'defaultPhone': o['defaultPhone']
        }

    unassigned_achieved = 0.0
    unassigned_contracts = set()

    # Add transaction data
    if not df_filtered.empty:
        for _, row in df_filtered.iterrows():
            oid = row['officer_id']
            if oid in grouped:
                grouped[oid]['achieved'] += row['amount']
                if row['contract'] and str(row['contract']).strip() not in ['-', '0', '', 'nan', 'None']:
                    grouped[oid]['contracts'].add(row['contract'])
            else:
                unassigned_achieved += row['amount']
                if row['contract'] and str(row['contract']).strip() not in ['-', '0', '', 'nan', 'None']:
                    unassigned_contracts.add(row['contract'])

    # Build officer record list (Roster members only)
    officer_records = []
    for oid, d in grouped.items():
        ach = d['achieved']
        tgt = d['target']
        var = ach - tgt
        rem = max(0.0, tgt - ach)
        daily_req = round(rem / working_days) if working_days > 0 else 0.0
        contract_cnt = len(d['contracts'])
        avg_contract = (ach / contract_cnt) if contract_cnt > 0 else 0.0

        officer_records.append({
            'officer_id': oid,
            'officer_name': d['officer_name'],
            'displayName': d['displayName'],
            'nic': d['nic'],
            'team_key': d['team_key'],
            'team_name': d['team_name'],
            'target': tgt,
            'achieved': ach,
            'variance': var,
            'remaining': rem,
            'daily_required': daily_req,
            'contracts_count': contract_cnt,
            'avg_per_contract': avg_contract,
            'achieved_pct': (ach / tgt * 100) if tgt > 0 else 0.0,
            'phone': d['defaultPhone']
        })

    # Group Summaries
    iresha_achieved = sum(r['achieved'] for r in officer_records if r['team_key'] == 'TEAM_IRESHA')
    iresha_target = sum(r['target'] for r in officer_records if r['team_key'] == 'TEAM_IRESHA')
    
    dila_achieved = sum(r['achieved'] for r in officer_records if r['team_key'] == 'TEAM_DILA')
    dila_target = sum(r['target'] for r in officer_records if r['team_key'] == 'TEAM_DILA')

    total_achieved = iresha_achieved + dila_achieved
    total_target = iresha_target + dila_target
    total_variance = total_achieved - total_target
    total_remaining = max(0.0, total_target - total_achieved)
    total_daily_required = round(total_remaining / working_days) if working_days > 0 else 0.0
    total_contracts = sum(r['contracts_count'] for r in officer_records)

    display_date = selected_date if (selected_date and selected_date != "ALL") else (selected_month if selected_month else datetime.now().strftime('%Y-%m-%d'))

    summary = {
        'total_target': total_target,
        'total_achieved': total_achieved,
        'total_variance': total_variance,
        'total_remaining': total_remaining,
        'daily_required': total_daily_required,
        'remaining_days': working_days,
        'total_contracts': total_contracts,
        'iresha_target': iresha_target,
        'iresha_achieved': iresha_achieved,
        'dila_target': dila_target,
        'dila_achieved': dila_achieved,
        'unassigned_achieved': unassigned_achieved,
        'unassigned_contracts': len(unassigned_contracts),
        'record_date': display_date,
        'month': selected_month if selected_month else display_date[:7]
    }

    return summary, officer_records
