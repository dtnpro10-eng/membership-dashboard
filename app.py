"""
Recovery & Repayment Performance Dashboard (Python & Streamlit Edition)
Daily Tracking, SQLite Database History Persistence, and WhatsApp/SMS Alerts.
Includes Group Iresha (5 members) & Group Dila (4 members) with Google Sheet Auto Sync.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import urllib.parse

from roster import ROSTER_IRESHA, ROSTER_DILA, TEAM_TARGET_IRESHA, TEAM_TARGET_DILA, DEFAULT_GOOGLE_SHEET_URL
import database as db
import data_processor as dp
import image_generator as ig

# Page setup
st.set_page_config(
    page_title="Recovery & Repayment Performance Dashboard - 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; }
    
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        position: relative;
    }
    .metric-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 4px;
    }
    .metric-val {
        font-size: 24px;
        font-weight: 900;
        color: #0f172a;
    }
    .metric-sub {
        font-size: 12px;
        font-weight: 600;
        color: #475569;
        margin-top: 5px;
    }

    .dark-table-container {
        background-color: #171d2b;
        border-radius: 12px;
        padding: 18px;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
    }
    .dark-header {
        background-color: #8c9ba8;
        color: #171d2b;
        text-align: center;
        padding: 10px;
        border-radius: 6px;
        font-weight: 900;
        margin-bottom: 12px;
    }
    .dark-sub-header {
        display: flex;
        background-color: #0f131c;
        padding: 8px;
        font-weight: 800;
        color: #f59e0b;
        text-align: center;
        font-size: 12px;
        margin-bottom: 8px;
    }
    .dark-sub-col { flex: 1; }
    .dark-tbl {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }
    .dark-tbl th {
        background-color: #1a2233;
        color: #94a3b8;
        padding: 8px;
        border-bottom: 2px solid #2d3748;
        font-size: 11px;
    }
    .dark-tbl td {
        padding: 8px;
        border-bottom: 1px solid #1e293b;
    }
    .dark-tbl tfoot td {
        background-color: #121824;
        border-top: 2px solid #334155;
        font-weight: 800;
    }
    .dark-highlight-box {
        background-color: #121824;
        border: 1px solid #d97706;
        padding: 14px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        margin-top: 14px;
        font-weight: 800;
        font-size: 13px;
    }
    
    .badge-pink { background: #fdf2f8; color: #db2777; border: 1px solid #fbcfe8; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; }
    .badge-green { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; }
    .badge-blue { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# Initialize Database
db.init_db()

# Load targets from database or defaults
custom_targets = {}
for o in ROSTER_IRESHA + ROSTER_DILA:
    saved_tgt = db.get_setting(f"target_{o['id']}")
    custom_targets[o['id']] = float(saved_tgt) if saved_tgt else o['defaultTarget']

def format_money(val):
    return f"{val:,.0f}"

# Session State Initialization
if 'transactions_df' not in st.session_state:
    st.session_state['transactions_df'] = pd.DataFrame()
if 'data_source_label' not in st.session_state:
    st.session_state['data_source_label'] = 'Google Sheet Live'
if 'officer_phones' not in st.session_state:
    st.session_state['officer_phones'] = db.get_officer_phones(ROSTER_IRESHA + ROSTER_DILA)

# Auto-fetch Google Sheet on first run
if st.session_state['transactions_df'].empty:
    try:
        raw_df = dp.fetch_google_sheet(DEFAULT_GOOGLE_SHEET_URL)
        mapping = dp.auto_detect_columns(raw_df)
        st.session_state['transactions_df'] = dp.process_transactions_dataframe(raw_df, mapping)
        st.session_state['data_source_label'] = 'Google Sheet Live (Auto Synced)'
    except Exception:
        pass

# --- TOP HEADER ---
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 44px; height: 44px; background: linear-gradient(135deg, #2563eb, #4f46e5); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-size: 22px; font-weight: bold; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);">
                📈
            </div>
            <div>
                <h1 style="font-size: 21px; font-weight: 900; color: #0f172a; margin: 0; line-height: 1.2;">
                    Recovery Performance Dashboard <span class="badge-blue">Live 2026</span>
                </h1>
                <p style="font-size: 12px; color: #64748b; margin: 0; font-weight: 500;">
                    Repayments, Officer Tracking (Iresha & Dila) & Daily Target Analytics
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_head2:
    st.markdown(f"""
        <div style="text-align: right; padding-top: 5px;">
            <span style="font-size: 11px; color: #64748b; font-weight: 600;">අද දිනය: </span>
            <strong style="font-size: 13px; color: #0f172a;">{datetime.now().strftime('%Y-%m-%d')}</strong>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 10px 0 16px 0; border: none; border-top: 1px solid #e2e8f0;'/>", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### 🎛️ පාලන පුවරුව (Control Panel)")
    
    app_mode = st.radio(
        "මෙනුව තෝරන්න:",
        ["📊 Daily Dashboard (දෛනික වාර්තාව)",
         "💾 Daily History & Trends (ඉතිහාසය සහ සේව් කිරීම)",
         "🎯 Target Settings (ඉලක්ක සැකසුම්)",
         "📱 SMS / WhatsApp Sender"],
        index=0
    )

    st.markdown("---")
    st.markdown("#### 🌐 Google Sheet සෘජු සම්බන්ධතාව")
    sheet_url_input = st.text_input(
        "Google Sheet URL:",
        value=DEFAULT_GOOGLE_SHEET_URL,
        help="Google Sheet එක 'Anyone with the link can view' ලෙස තබා Link එක ලබාදෙන්න."
    )
    if st.button("🔄 Google Sheet Live Sync කරන්න", type="primary", use_container_width=True):
        try:
            with st.spinner("Google Sheet එකෙන් දත්ත බාගත වෙමින් පවතී..."):
                raw_df = dp.fetch_google_sheet(sheet_url_input)
                mapping = dp.auto_detect_columns(raw_df)
                st.session_state['transactions_df'] = dp.process_transactions_dataframe(raw_df, mapping)
                st.session_state['data_source_label'] = "Google Sheet Live"
                st.success(f"✅ ගනුදෙනු {len(raw_df):,} ක් සාර්ථකව Sync විය!")
        except Exception as e:
            st.error(f"Sync දෝෂය: {str(e)}")

    with st.expander("📁 වෙනත් Excel / CSV ගොනුවක් Upload කිරීමට"):
        uploaded_file = st.file_uploader("ගොනුව තෝරන්න:", type=['xlsx', 'xls', 'csv'])
        if uploaded_file is not None:
            try:
                raw_df = dp.read_uploaded_file(uploaded_file)
                mapping = dp.auto_detect_columns(raw_df)
                st.session_state['transactions_df'] = dp.process_transactions_dataframe(raw_df, mapping)
                st.session_state['data_source_label'] = uploaded_file.name
                st.success(f"✅ ගනුදෙනු {len(raw_df)} ක් සාර්ථකව කියවන ලදී!")
            except Exception as e:
                st.error(f"දෝෂයක් මතු විය: {str(e)}")

    st.markdown("---")
    st.markdown("#### 📅 මාසය සහ දින Filters")

    # Available months in transactions
    all_months = []
    if not st.session_state['transactions_df'].empty:
        all_months = sorted(st.session_state['transactions_df']['month'].unique().tolist(), reverse=True)
    
    current_month = datetime.now().strftime('%Y-%m')
    default_month_idx = all_months.index(current_month) if current_month in all_months else 0
    selected_month = st.selectbox("මාසය (Month):", all_months if all_months else [current_month], index=default_month_idx)

    # Available dates for selected month
    dates_in_month = []
    if not st.session_state['transactions_df'].empty:
        month_filtered = st.session_state['transactions_df'][st.session_state['transactions_df']['month'] == selected_month]
        dates_in_month = sorted(month_filtered['date'].unique().tolist(), reverse=True)

    date_options = ["සියලුම දින (Month Cumulative)"] + dates_in_month
    selected_date_choice = st.selectbox("දිනය (Transaction Date):", date_options, index=0)

    selected_date = "ALL" if selected_date_choice.startswith("සියලුම දින") else selected_date_choice
    st.session_state['selected_date'] = selected_date if selected_date != "ALL" else (dates_in_month[0] if dates_in_month else datetime.now().strftime('%Y-%m-%d'))

    # Remaining working days
    ref_calc_date = st.session_state['selected_date']
    auto_working_days = dp.calculate_remaining_working_days(ref_calc_date)
    working_days = st.number_input(
        "ඉතිරි වැඩ දින (Sat/Sun හැර):",
        min_value=1, max_value=31, value=auto_working_days, step=1
    )

# Compute current metrics
summary, officer_records = dp.compute_dashboard_metrics(
    st.session_state['transactions_df'],
    selected_month=selected_month,
    selected_date=selected_date,
    working_days=working_days,
    custom_targets=custom_targets
)
for o in officer_records:
    o['phone'] = st.session_state['officer_phones'].get(o['officer_id'], o.get('phone', '0770000000'))


# ==========================================
# TAB 1: DAILY DASHBOARD
# ==========================================
if "Daily Dashboard" in app_mode:

    # Direct Snapshot Save Action Bar
    bar_col1, bar_col2 = st.columns([3, 1])
    with bar_col1:
        st.markdown(f"""
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 16px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span style="font-size: 13px; font-weight: 700; color: #1e293b;">ප්‍රභවය: <strong>{st.session_state['data_source_label']}</strong></span> |
                    <span style="font-size: 13px; font-weight: 700; color: #2563eb;"> මාසය: <strong>{selected_month}</strong></span> |
                    <span style="font-size: 13px; font-weight: 700; color: #0284c7;"> දිනය: <strong>{selected_date_choice}</strong></span> |
                    <span style="font-size: 13px; font-weight: 700; color: #059669;"> ඉතිරි වැඩ දින: <strong>{working_days} Days</strong></span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with bar_col2:
        snapshot_date_tag = st.session_state['selected_date']
        if st.button("💾 මෙම වාර්තාව Database එකේ Save කරන්න", type="primary", use_container_width=True):
            db.save_daily_snapshot(
                record_date=snapshot_date_tag,
                summary_data=summary,
                officer_records=officer_records,
                notes=f"Source: {st.session_state['data_source_label']} | Month: {selected_month}"
            )
            st.toast(f"✅ {snapshot_date_tag} දින වාර්තාව සාර්ථකව Database එකේ සුරකින ලදී!", icon="💾")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 4 Key Summary Cards
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    with m_col1:
        total_ach = summary['total_achieved']
        total_tgt = summary['total_target']
        total_pct = (total_ach / total_tgt * 100) if total_tgt > 0 else 0
        rem_gap = summary['total_remaining']
        
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">මුළු අයවීම් (Total Achieved)</div>
                <div class="metric-val">Rs. {format_money(total_ach)}</div>
                <div class="metric-sub">ඉලක්කය: Rs. {format_money(total_tgt)} ({total_pct:.1f}%)</div>
                <div style="background: #e2e8f0; height: 6px; border-radius: 6px; margin: 8px 0; overflow: hidden;">
                    <div style="background: #2563eb; width: {min(total_pct, 100)}%; height: 100%;"></div>
                </div>
                <div style="font-size: 11px; font-weight: 700; color: {'#059669' if rem_gap == 0 else '#64748b'};">
                    {'🎉 ඉලක්කය සම්පූර්ණයි!' if rem_gap == 0 else f'ඉතිරි ඉලක්කය: රු. {format_money(rem_gap)}'}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with m_col2:
        i_ach = summary['iresha_achieved']
        i_tgt = summary['iresha_target']
        i_pct = (i_ach / i_tgt * 100) if i_tgt > 0 else 0
        i_rem = max(0.0, i_tgt - i_ach)
        st.markdown(f"""
            <div class="metric-card" style="border-color: #fbcfe8;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div class="metric-title" style="color: #db2777;">Group Iresha (ඉරේශා)</div>
                    <span class="badge-pink">5 Members</span>
                </div>
                <div class="metric-val">Rs. {format_money(i_ach)}</div>
                <div class="metric-sub">Target: Rs. {format_money(i_tgt)} ({i_pct:.1f}%)</div>
                <div style="background: #fce7f3; height: 6px; border-radius: 6px; margin: 8px 0; overflow: hidden;">
                    <div style="background: #db2777; width: {min(i_pct, 100)}%; height: 100%;"></div>
                </div>
                <div style="font-size: 11px; font-weight: 700; color: #db2777;">
                    {'🎉 සම්පූර්ණයි' if i_rem == 0 else f'තව අවශ්‍ය මුදල: රු. {format_money(i_rem)}'}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with m_col3:
        d_ach = summary['dila_achieved']
        d_tgt = summary['dila_target']
        d_pct = (d_ach / d_tgt * 100) if d_tgt > 0 else 0
        d_rem = max(0.0, d_tgt - d_ach)
        st.markdown(f"""
            <div class="metric-card" style="border-color: #a7f3d0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div class="metric-title" style="color: #059669;">Group Dila (ඩිලා)</div>
                    <span class="badge-green">4 Members</span>
                </div>
                <div class="metric-val">Rs. {format_money(d_ach)}</div>
                <div class="metric-sub">Target: Rs. {format_money(d_tgt)} ({d_pct:.1f}%)</div>
                <div style="background: #d1fae5; height: 6px; border-radius: 6px; margin: 8px 0; overflow: hidden;">
                    <div style="background: #059669; width: {min(d_pct, 100)}%; height: 100%;"></div>
                </div>
                <div style="font-size: 11px; font-weight: 700; color: #059669;">
                    {'🎉 සම්පූර්ණයි' if d_rem == 0 else f'තව අවශ්‍ය මුදල: රු. {format_money(d_rem)}'}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with m_col4:
        top_officer = max(officer_records, key=lambda x: x['achieved']) if officer_records else None
        top_name = top_officer['officer_name'] if top_officer and top_officer['achieved'] > 0 else 'නැත'
        top_amt = top_officer['achieved'] if top_officer else 0
        
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">මුළු කොන්ත්‍රාත්තු (Contracts)</div>
                <div class="metric-val" style="color: #4f46e5;">{summary['total_contracts']:,}</div>
                <div class="metric-sub" style="border-top: 1px solid #f1f5f9; padding-top: 6px; margin-top: 10px;">
                    🏆 <strong>Top Officer:</strong> {top_name}<br/>
                    <span style="font-size: 11px; color: #d97706; font-weight: 800;">Rs. {format_money(top_amt)}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    if summary.get('unassigned_achieved', 0) > 0:
        st.info(f"ℹ️ **සටහන:** Group Iresha හෝ Group Dila කණ්ඩායම් දෙකට අයත් නොවන වෙනත් නිලධාරීන්ගේ එකතු කිරීම් LKR {format_money(summary['unassigned_achieved'])} ක් (ගනුදෙනු {summary.get('unassigned_contracts', 0)}) පවතී. ඒවා මෙම කණ්ඩායම් ඉලක්ක වාර්තාවට ඇතුළත් කර නොමැත.")

    # Determine if Daily column should be shown (only on Month Cumulative view)
    show_daily_col = selected_date_choice.startswith("සියලුම දින") or selected_date == "ALL"

    # 🎯 DARK THEME DAILY TARGET REPORT HEADER & PNG BUTTON
    dark_col_head, dark_col_btn = st.columns([3, 1])
    with dark_col_head:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 8px;">
                <h3 style="font-size: 16px; font-weight: 800; color: #0f172a; margin: 0;">
                    🎯 Membership Loan Daily Target Report (Dark Theme Edition)
                </h3>
                <span class="badge-blue">Group Iresha (5) | Group Dila (4)</span>
            </div>
        """, unsafe_allow_html=True)
    with dark_col_btn:
        dark_png_bytes = ig.generate_dark_table_png(
            summary, 
            [r for r in officer_records if r['team_key'] == 'TEAM_IRESHA'],
            [r for r in officer_records if r['team_key'] == 'TEAM_DILA'],
            selected_month, 
            selected_date_choice, 
            working_days, 
            show_daily_col=show_daily_col
        )
        st.download_button(
            label="📸 Download PNG (Dark Report)",
            data=dark_png_bytes,
            file_name=f"Daily_Target_Report_{selected_month}_{selected_date_choice.replace(' ', '_')}.png",
            mime="image/png",
            key="btn_download_dark_png",
            use_container_width=True
        )

    iresha_rows = [r for r in officer_records if r['team_key'] == 'TEAM_IRESHA']
    dila_rows = [r for r in officer_records if r['team_key'] == 'TEAM_DILA']

    rows_html = ""
    max_rows = max(len(iresha_rows), len(dila_rows))
    for i in range(max_rows):
        i_item = iresha_rows[i] if i < len(iresha_rows) else None
        d_item = dila_rows[i] if i < len(dila_rows) else None

        # Format Iresha
        if i_item:
            if show_daily_col:
                i_var_color = "#4ade80" if i_item['variance'] >= 0 else "#f87171"
                i_var_str = f"+{format_money(i_item['variance'])}" if i_item['variance'] >= 0 else f"({format_money(abs(i_item['variance']))})"
                i_daily_cell = f'<td style="text-align:right;color:#38bdf8;font-weight:900;border-right:1px solid #334155;padding:8px;">{format_money(i_item["daily_required"])}</td>'
                i_td = f'''<td style="font-weight:700;text-align:left;padding:8px;">{i_item['officer_name']}</td><td style="text-align:right;color:#cbd5e1;padding:8px;">{format_money(i_item['target'])}</td><td style="text-align:right;font-weight:700;color:#ffffff;padding:8px;">{format_money(i_item['achieved'])}</td><td style="text-align:right;color:{i_var_color};font-weight:700;padding:8px;">{i_var_str}</td>{i_daily_cell}'''
            else:
                # Omit VARIANCE on single date view
                i_td = f'''<td style="font-weight:700;text-align:left;padding:8px;">{i_item['officer_name']}</td><td style="text-align:right;color:#cbd5e1;padding:8px;">{format_money(i_item['target'])}</td><td style="text-align:right;font-weight:700;color:#ffffff;padding:8px;border-right:1px solid #334155;">{format_money(i_item['achieved'])}</td>'''
        else:
            colspan = "5" if show_daily_col else "3"
            i_td = f'<td colspan="{colspan}" style="border-right:1px solid #334155;text-align:center;color:#64748b;padding:8px;">-</td>'

        # Format Dila
        if d_item:
            if show_daily_col:
                d_var_color = "#4ade80" if d_item['variance'] >= 0 else "#f87171"
                d_var_str = f"+{format_money(d_item['variance'])}" if d_item['variance'] >= 0 else f"({format_money(abs(d_item['variance']))})"
                d_daily_cell = f'<td style="text-align:right;color:#38bdf8;font-weight:900;padding:8px;">{format_money(d_item["daily_required"])}</td>'
                d_td = f'''<td style="font-weight:700;text-align:left;padding:8px;padding-left:12px;">{d_item['officer_name']}</td><td style="text-align:right;color:#cbd5e1;padding:8px;">{format_money(d_item['target'])}</td><td style="text-align:right;font-weight:700;color:#ffffff;padding:8px;">{format_money(d_item['achieved'])}</td><td style="text-align:right;color:{d_var_color};font-weight:700;padding:8px;">{d_var_str}</td>{d_daily_cell}'''
            else:
                # Omit VARIANCE on single date view
                d_td = f'''<td style="font-weight:700;text-align:left;padding:8px;padding-left:12px;">{d_item['officer_name']}</td><td style="text-align:right;color:#cbd5e1;padding:8px;">{format_money(d_item['target'])}</td><td style="text-align:right;font-weight:700;color:#ffffff;padding:8px;">{format_money(d_item['achieved'])}</td>'''
        else:
            colspan = "5" if show_daily_col else "3"
            d_td = f'<td colspan="{colspan}" style="text-align:center;color:#64748b;padding:8px;">-</td>'

        rows_html += f'<tr style="border-bottom:1px solid #1e293b;">{i_td}{d_td}</tr>\n'

    # Headers HTML
    if show_daily_col:
        thead_html = f'''<tr style="background-color:#1a2233;border-bottom:2px solid #2d3748;">
<th style="text-align:left;padding:8px;color:#94a3b8;">NAME</th>
<th style="text-align:right;padding:8px;color:#94a3b8;">TARGET</th>
<th style="text-align:right;padding:8px;color:#94a3b8;">ACHIEV.</th>
<th style="text-align:right;padding:8px;color:#94a3b8;">VARIANCE</th>
<th style="text-align:right;padding:8px;color:#38bdf8;border-right:1px solid #334155;">DAILY ({working_days}D)</th>
<th style="text-align:left;padding:8px;padding-left:12px;color:#94a3b8;">NAME</th>
<th style="text-align:right;padding:8px;color:#94a3b8;">TARGET</th>
<th style="text-align:right;padding:8px;color:#94a3b8;">ACHIEV.</th>
<th style="text-align:right;padding:8px;color:#94a3b8;">VARIANCE</th>
<th style="text-align:right;padding:8px;color:#38bdf8;">DAILY ({working_days}D)</th>
</tr>'''
        sub_view_text = f"DATE / VIEW: {selected_date_choice.upper()} | REMAINING WORKING DAYS: {working_days} DAYS (EXCL. SAT/SUN)"
        
        # Team totals for cumulative view (with variance & daily)
        i_tot_var = summary['iresha_achieved'] - summary['iresha_target']
        i_tot_var_color = "#4ade80" if i_tot_var >= 0 else "#f87171"
        i_tot_var_str = f"+{format_money(i_tot_var)}" if i_tot_var >= 0 else f"({format_money(abs(i_tot_var))})"
        i_rem = max(0.0, summary['iresha_target'] - summary['iresha_achieved'])
        i_daily_req = round(i_rem / working_days) if working_days > 0 else 0
        
        d_tot_var = summary['dila_achieved'] - summary['dila_target']
        d_tot_var_color = "#4ade80" if d_tot_var >= 0 else "#f87171"
        d_tot_var_str = f"+{format_money(d_tot_var)}" if d_tot_var >= 0 else f"({format_money(abs(d_tot_var))})"
        d_rem = max(0.0, summary['dila_target'] - summary['dila_achieved'])
        d_daily_req = round(d_rem / working_days) if working_days > 0 else 0

        tfoot_row1 = f'''<tr style="background-color:#121824;border-top:2px solid #334155;font-weight:800;">
<td style="text-align:left;padding:8px;">TOTAL</td>
<td style="text-align:right;color:#cbd5e1;padding:8px;">{format_money(summary['iresha_target'])}</td>
<td style="text-align:right;background-color:#fef3c7;color:#78350f;font-weight:900;padding:8px;">{format_money(summary['iresha_achieved'])}</td>
<td style="text-align:right;color:{i_tot_var_color};padding:8px;">{i_tot_var_str}</td>
<td style="text-align:right;color:#38bdf8;font-weight:900;border-right:1px solid #334155;padding:8px;">{format_money(i_daily_req)}</td>
<td style="text-align:left;padding:8px;padding-left:12px;">TOTAL</td>
<td style="text-align:right;color:#cbd5e1;padding:8px;">{format_money(summary['dila_target'])}</td>
<td style="text-align:right;background-color:#fef3c7;color:#78350f;font-weight:900;padding:8px;">{format_money(summary['dila_achieved'])}</td>
<td style="text-align:right;color:{d_tot_var_color};padding:8px;">{d_tot_var_str}</td>
<td style="text-align:right;color:#38bdf8;font-weight:900;padding:8px;">{format_money(d_daily_req)}</td>
</tr>'''
        
        tfoot_row2 = f'''<tr style="background-color:#0b0f19;border-top:2px solid #d97706;font-size:13px;font-weight:900;">
<td colspan="5" style="text-align:center;color:#fbbf24;padding:10px;border-right:1px solid #334155;">
🎯 GRAND TOTAL TARGET: LKR {format_money(summary['total_target'])}
</td>
<td colspan="5" style="text-align:center;color:#4ade80;background-color:#052e16;padding:10px;">
✅ TOTAL ACHIEVED: LKR {format_money(summary['total_achieved'])} ({(summary['total_achieved'] / summary['total_target'] * 100) if summary['total_target'] > 0 else 0:.1f}%)
</td>
</tr>'''

        bottom_box_html = f'''<div style="background-color:#121824;border:1px solid #d97706;padding:14px;border-radius:8px;display:flex;justify-content:space-between;margin-top:14px;font-weight:800;font-size:13px;">
<div style="color:#fbbf24;">GRAND TOTAL REMAINING: LKR {format_money(summary['total_remaining'])}</div>
<div style="color:#38bdf8;">DAILY REQUIRED TARGET ({working_days} DAYS): LKR {format_money(summary["daily_required"])}</div>
</div>'''
    else:
        # Single Date View: NO VARIANCE, NO DAILY, NO GRAND TOTAL REMAINING!
        thead_html = '''<tr style="background-color:#1a2233;border-bottom:2px solid #2d3748;">
<th style="text-align:left;padding:8px;color:#94a3b8;">NAME</th>
<th style="text-align:right;padding:8px;color:#94a3b8;">TARGET</th>
<th style="text-align:right;padding:8px;color:#94a3b8;border-right:1px solid #334155;">ACHIEV.</th>
<th style="text-align:left;padding:8px;padding-left:12px;color:#94a3b8;">NAME</th>
<th style="text-align:right;padding:8px;color:#94a3b8;">TARGET</th>
<th style="text-align:right;padding:8px;color:#94a3b8;">ACHIEV.</th>
</tr>'''
        sub_view_text = f"DATE: {selected_date_choice.upper()} | DAILY TRANSACTIONS PERFORMANCE VIEW"

        tfoot_row1 = f'''<tr style="background-color:#121824;border-top:2px solid #334155;font-weight:800;">
<td style="text-align:left;padding:8px;">TOTAL</td>
<td style="text-align:right;color:#cbd5e1;padding:8px;">{format_money(summary['iresha_target'])}</td>
<td style="text-align:right;background-color:#fef3c7;color:#78350f;font-weight:900;padding:8px;border-right:1px solid #334155;">{format_money(summary['iresha_achieved'])}</td>
<td style="text-align:left;padding:8px;padding-left:12px;">TOTAL</td>
<td style="text-align:right;color:#cbd5e1;padding:8px;">{format_money(summary['dila_target'])}</td>
<td style="text-align:right;background-color:#fef3c7;color:#78350f;font-weight:900;padding:8px;">{format_money(summary['dila_achieved'])}</td>
</tr>'''

        tfoot_row2 = f'''<tr style="background-color:#0b0f19;border-top:2px solid #10b981;font-size:13px;font-weight:900;">
<td colspan="3" style="text-align:center;color:#fbbf24;padding:10px;border-right:1px solid #334155;">
🎯 GRAND TOTAL TARGET: LKR {format_money(summary['total_target'])}
</td>
<td colspan="3" style="text-align:center;color:#4ade80;background-color:#052e16;padding:10px;">
✅ TOTAL COLLECTED ON {selected_date_choice}: LKR {format_money(summary['total_achieved'])}
</td>
</tr>'''

        # Specific date: completely omit GRAND TOTAL REMAINING
        bottom_box_html = f'''<div style="background-color:#121824;border:1px solid #10b981;padding:14px;border-radius:8px;display:flex;justify-content:space-between;margin-top:14px;font-weight:800;font-size:13px;">
<div style="color:#4ade80;">📅 TOTAL COLLECTED ON {selected_date_choice}: LKR {format_money(summary['total_achieved'])}</div>
<div style="color:#38bdf8;">GROUP IRESHAS: LKR {format_money(summary['iresha_achieved'])} | GROUP DILA: LKR {format_money(summary['dila_achieved'])}</div>
</div>'''

    dark_html = f'''<div style="background-color:#171d2b;border-radius:12px;padding:18px;color:#ffffff;font-family:'Inter',sans-serif;margin:10px 0;box-shadow:inset 0 2px 4px rgba(0,0,0,0.4);">
<div style="background-color:#8c9ba8;color:#171d2b;text-align:center;padding:10px;border-radius:6px;font-weight:900;margin-bottom:12px;">
<div style="font-size:16px;letter-spacing:0.05em;">MEMBERSHIP LOAN TARGET - {selected_month.upper()}</div>
<div style="font-size:11px;margin-top:2px;">{sub_view_text}</div>
</div>
<div style="display:flex;background-color:#0f131c;padding:8px;font-weight:800;color:#f59e0b;text-align:center;font-size:12px;margin-bottom:8px;">
<div style="flex:1;border-right:1px solid #334155;">GROUP IRESHAS (5 MEMBERS)</div>
<div style="flex:1;">GROUP DILA (4 MEMBERS)</div>
</div>
<table style="width:100%;border-collapse:collapse;font-size:12px;">
<thead>
{thead_html}
</thead>
<tbody>
{rows_html}
</tbody>
<tfoot>
{tfoot_row1}
{tfoot_row2}
</tfoot>
</table>
{bottom_box_html}
</div>'''

    st.html(dark_html)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 📋 OFFICER BREAKDOWN TABLE HEADER & PNG BUTTON
    off_col_head, off_col_btn = st.columns([3, 1])
    with off_col_head:
        st.markdown("### 📋 සියලු නිලධාරීන්ගේ සවිස්තරාත්මක වාර්තාව (Officer Breakdown)")
    with off_col_btn:
        breakdown_png_bytes = ig.generate_officer_breakdown_png(
            officer_records, selected_month, selected_date_choice
        )
        st.download_button(
            label="📸 Download PNG (Breakdown Table)",
            data=breakdown_png_bytes,
            file_name=f"Officer_Breakdown_{selected_month}_{selected_date_choice.replace(' ', '_')}.png",
            mime="image/png",
            key="btn_download_breakdown_png",
            use_container_width=True
        )
    
    table_data = []
    sorted_officers = sorted(officer_records, key=lambda x: x['achieved'], reverse=True)
    for rank, o in enumerate(sorted_officers, start=1):
        medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
        table_data.append({
            "ශ්‍රේණිය": medal,
            "නිලධාරියා (Officer)": o['officer_name'],
            "කණ්ඩායම (Team)": o['team_name'],
            "කොන්ත්‍රාත් ගණන": o['contracts_count'],
            "Target (රු.)": o['target'],
            "එකතු කළ මුදල (රු.)": o['achieved'],
            "Variance (රු.)": o['variance'],
            "ප්‍රගතිය %": f"{o['achieved_pct']:.1f}%",
            "දෛනික ඉලක්කය (රු.)": o['daily_required']
        })

    tbl_df = pd.DataFrame(table_data)
    st.dataframe(
        tbl_df,
        use_container_width=True,
        column_config={
            "Target (රු.)": st.column_config.NumberColumn(format="රු. %d"),
            "එකතු කළ මුදල (රු.)": st.column_config.NumberColumn(format="රු. %d"),
            "Variance (රු.)": st.column_config.NumberColumn(format="රු. %d"),
            "දෛනික ඉලක්කය (රු.)": st.column_config.NumberColumn(format="රු. %d"),
        },
        hide_index=True
    )


# ==========================================
# TAB 2: DAILY HISTORY & TRENDS
# ==========================================
elif "Daily History" in app_mode:
    st.markdown("## 💾 දිනපතා සේව් වූ වාර්තා සහ ප්‍රගති ඉතිහාසය (Daily History & Trends)")
    st.write("මෙතැනින් ඔබ දිනපතා සේව් කළ සියලු වාර්තා, දින අනුව සැසඳීම් සහ ප්‍රස්ථාර (Trends) බලාගත හැක.")

    saved_dates = db.get_saved_dates()

    if not saved_dates:
        st.info("ℹ️ මෙතෙක් කිසිදු දිනයක වාර්තාවක් Database එකේ Save කර නොමැත. **'Daily Dashboard'** වෙත ගොස් **'මෙම වාර්තාව Database එකේ Save කරන්න'** බොත්තම ඔබන්න.")
    else:
        hist_col1, hist_col2 = st.columns([1, 2])
        
        with hist_col1:
            st.markdown("#### 📅 පෙර දින වාර්තාවක් පරීක්ෂා කිරීම")
            pick_date = st.selectbox("සුරැකි දිනයක් තෝරන්න:", saved_dates)
            
            if st.button("🗑️ මෙම දිනයේ Record එක මකන්න", help="වරදවා ඇතුළත් කළ Record එකක් ඉවත් කිරීමට"):
                db.delete_snapshot(pick_date)
                st.warning(f"{pick_date} දින වාර්තාව Database එකෙන් ඉවත් කරන ලදී.")
                st.rerun()

        with hist_col2:
            s_snap, s_officers = db.get_snapshot(pick_date)
            if s_snap:
                st.markdown(f"""
                    <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 10px; padding: 14px;">
                        <h4 style="margin: 0; color: #1e293b;">📌 {pick_date} දින සාරාංශය:</h4>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; font-size: 13px;">
                            <div><strong>මුළු එකතුව:</strong> රු. {format_money(s_snap['total_achieved'])}</div>
                            <div><strong>මුළු Target:</strong> රු. {format_money(s_snap['total_target'])}</div>
                            <div><strong>ඉතිරි වැඩ දින:</strong> {s_snap['remaining_days']} Days</div>
                            <div><strong>Group Iresha:</strong> රු. {format_money(s_snap['iresha_achieved'])}</div>
                            <div><strong>Group Dila:</strong> රු. {format_money(s_snap['dila_achieved'])}</div>
                            <div><strong>දෛනික ඉලක්කය:</strong> රු. {format_money(s_snap['daily_required'])}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Historical Trend Line Chart
        st.markdown("### 📈 දිනපතා එකතු කිරීම් ප්‍රගති ප්‍රස්ථාරය (Daily Trend Chart)")
        all_snaps_df = db.get_all_snapshots()
        if not all_snaps_df.empty:
            chart_data = all_snaps_df[['record_date', 'total_achieved', 'iresha_achieved', 'dila_achieved']].copy()
            chart_data = chart_data.rename(columns={
                'record_date': 'දිනය',
                'total_achieved': 'මුළු එකතුව (Total)',
                'iresha_achieved': 'Group Iresha',
                'dila_achieved': 'Group Dila'
            })
            chart_data = chart_data.set_index('දිනය')
            st.line_chart(chart_data)

        # Full History Table
        st.markdown("### 📑 සුරැකි සියලු දිනවල සාරාංශ වගුව (All Snapshots Table)")
        st.dataframe(
            all_snaps_df[['record_date', 'total_target', 'total_achieved', 'total_variance', 'daily_required', 'remaining_days', 'saved_at']],
            column_config={
                'record_date': 'දිනය',
                'total_target': st.column_config.NumberColumn("Target (රු.)", format="රු. %d"),
                'total_achieved': st.column_config.NumberColumn("Achieved (රු.)", format="රු. %d"),
                'total_variance': st.column_config.NumberColumn("Variance (රු.)", format="රු. %d"),
                'daily_required': st.column_config.NumberColumn("Daily Req (රු.)", format="රු. %d"),
                'remaining_days': "ඉතිරි දින",
                'saved_at': "Save කළ වේලාව"
            },
            hide_index=True,
            use_container_width=True
        )


# ==========================================
# TAB 3: TARGET SETTINGS
# ==========================================
elif "Target Settings" in app_mode:
    st.markdown("## 🎯 ඉලක්ක (Targets) වෙනස් කිරීමේ කළමනාකරණය")
    st.write("කණ්ඩායම් හා තනි නිලධාරීන්ගේ ඉලක්ක මෙතැනින් වෙනස් කර සුරැකිය හැක. වෙනස්කම් ස්වයංක්‍රීයව Database එකෙහි සුරැකේ.")

    t_col1, t_col2 = st.columns(2)

    with t_col1:
        st.markdown("### 🌸 Group Iresha Targets (5 Members)")
        for m in ROSTER_IRESHA:
            val = st.number_input(
                f"{m['shortName']} ({m['nic']}):",
                min_value=0.0,
                max_value=10000000.0,
                value=float(custom_targets.get(m['id'], m['defaultTarget'])),
                step=10000.0,
                key=f"input_tgt_{m['id']}"
            )
            custom_targets[m['id']] = val

    with t_col2:
        st.markdown("### 🌿 Group Dila Targets (4 Members)")
        for m in ROSTER_DILA:
            val = st.number_input(
                f"{m['shortName']} ({m['nic']}):",
                min_value=0.0,
                max_value=10000000.0,
                value=float(custom_targets.get(m['id'], m['defaultTarget'])),
                step=10000.0,
                key=f"input_tgt_{m['id']}"
            )
            custom_targets[m['id']] = val

    if st.button("💾 නව Targets Database එකෙහි සුරකින්න", type="primary"):
        for oid, tgt in custom_targets.items():
            db.save_setting(f"target_{oid}", str(tgt))
        st.success("✅ සියලු Targets සාර්ථකව යාවත්කාලීන විය!")


# ==========================================
# TAB 4: SMS / WHATSAPP SENDER
# ==========================================
elif "SMS / WhatsApp" in app_mode:
    st.markdown("## 📱 SMS & WhatsApp වාර්තා යැවීම")
    st.write("Manager සඳහා විධායක වාර්තාව සහ එක් එක් නිලධාරියාට පුද්ගලික දෛනික ඉලක්කය යැවීම.")

    # 1. PHONE NUMBERS MANAGER (User Request 2)
    with st.expander("📞 නිලධාරීන්ගේ දුරකථන අංක සැකසීම (Officer Phone Numbers Manager)", expanded=True):
        st.write("මෙහිදී එක් එක් නිලධාරියාගේ දුරකථන අංක ඇතුළත් කර **Save** කර තැබිය හැක. (Database එකෙහි ස්ථිරව සුරැකේ)")
        
        ph_col1, ph_col2 = st.columns(2)
        with ph_col1:
            st.markdown("##### 🌸 Group Iresha (5 Members)")
            iresha_recs = [r for r in officer_records if r['team_key'] == 'TEAM_IRESHA']
            for o in iresha_recs:
                cur_val = st.session_state['officer_phones'].get(o['officer_id'], o.get('phone', '0770000000'))
                new_val = st.text_input(f"📱 {o['officer_name']}", value=cur_val, key=f"edit_ph_{o['officer_id']}")
                st.session_state['officer_phones'][o['officer_id']] = new_val.strip()
                o['phone'] = new_val.strip()

        with ph_col2:
            st.markdown("##### 🌿 Group Dila (4 Members)")
            dila_recs = [r for r in officer_records if r['team_key'] == 'TEAM_DILA']
            for o in dila_recs:
                cur_val = st.session_state['officer_phones'].get(o['officer_id'], o.get('phone', '0770000000'))
                new_val = st.text_input(f"📱 {o['officer_name']}", value=cur_val, key=f"edit_ph_{o['officer_id']}")
                st.session_state['officer_phones'][o['officer_id']] = new_val.strip()
                o['phone'] = new_val.strip()

        if st.button("💾 සියලු දුරකථන අංක Database එකෙහි Save කරන්න", type="primary"):
            db.save_officer_phones(st.session_state['officer_phones'])
            st.success("✅ සියලු දුරකථන අංක සාර්ථකව සුරකින ලදී!")

    st.markdown("---")

    # 2. 1-CLICK DISPATCHER & GROUP BROADCAST (User Request 3)
    st.markdown("### 🚀 එක ක්ලික් එකකින් සියලු දෙනාටම WhatsApp යැවීම (1-Click Multi-Sender)")
    
    # Prepare recipient list for 1-click sender
    import json
    recipients_data = []
    all_msgs_text = f"=== MEMBERSHIP REPAYMENT ALERTS ({selected_month} | {selected_date_choice}) ===\n\n"

    for o in officer_records:
        var_text = f"+Rs. {format_money(o['variance'])}" if o['variance'] >= 0 else f"-Rs. {format_money(abs(o['variance']))}"
        msg = (
            f"📢 *Recovery Update: {o['officer_name']}*\n"
            f"📅 දිනය: {selected_month} | {selected_date_choice}\n"
            f"🎯 Target: Rs. {format_money(o['target'])}\n"
            f"✅ Achieved: Rs. {format_money(o['achieved'])}\n"
            f"⚠️ Variance: {var_text}\n"
            f"⏳ ඉතිරි වැඩ දින: {working_days} Days\n"
            f"⚡ දෛනික ඉලක්කය (Daily): Rs. {format_money(o['daily_required'])}\n\n"
            f"කරුණාකර දෛනික ඉලක්කය සම්පූර්ණ කිරීමට සහය වන්න!"
        )
        all_msgs_text += msg + "\n\n------------------------\n\n"
        
        ph = st.session_state['officer_phones'].get(o['officer_id'], o.get('phone', ''))
        clean_ph = ph.replace(' ', '').replace('-', '')
        if clean_ph:
            intl_ph = '94' + clean_ph[1:] if clean_ph.startswith('0') else (clean_ph if clean_ph.startswith('94') else '94' + clean_ph)
            wa_url = f"https://web.whatsapp.com/send?phone={intl_ph}&text={urllib.parse.quote(msg)}"
            recipients_data.append({
                'id': o['officer_id'],
                'name': o['officer_name'],
                'phone': clean_ph,
                'intlPhone': intl_ph,
                'url': wa_url
            })

    # Render interactive 1-click HTML/JS multi-sender
    recipients_json = json.dumps(recipients_data)
    
    dispatcher_html = """
    <div style="background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 20px; color: white; font-family: sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
            <div>
                <h4 style="margin: 0; color: #38bdf8; font-size: 16px;">⚡ Automated WhatsApp Broadcast Dispatcher</h4>
                <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 12px;">පහත බටන් එක ක්ලික් කළ විට සියලුම නිලධාරීන්ගේ WhatsApp චැට් ස්වයංක්‍රීයව විවෘත වේ.</p>
            </div>
            <button id="btnStartBatch" onclick="startBatchSend()" style="background: linear-gradient(135deg, #10b981, #059669); color: white; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 900; font-size: 14px; cursor: pointer; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4); display: flex; align-items: center; gap: 8px;">
                <span>🚀</span>
                <span>සියලු දෙනාටම WhatsApp යවන්න (Start 1-Click Send)</span>
            </button>
        </div>

        <div id="dispatchProgressBox" style="background: #1e293b; border-radius: 8px; padding: 12px; font-size: 12px; color: #cbd5e1; border: 1px solid #334155; display: none;">
            <div id="dispatchStatusText" style="font-weight: bold; color: #38bdf8; margin-bottom: 6px;">යැවීමට සූදානම්...</div>
            <div style="background: #0f172a; border-radius: 6px; height: 8px; overflow: hidden; margin-bottom: 8px;">
                <div id="dispatchProgressBar" style="background: #10b981; height: 100%; width: 0%; transition: width 0.3s;"></div>
            </div>
            <div id="dispatchLog" style="max-height: 120px; overflow-y: auto; font-family: monospace; font-size: 11px; color: #94a3b8;"></div>
        </div>
    </div>

    <script>
        const recipients = __RECIPIENTS_JSON__;
        let isSending = false;

        function startBatchSend() {
            if (recipients.length === 0) {
                alert("කරුණාකර අවම වශයෙන් එක් නිලධාරියෙකුගේ දුරකථන අංකයක් ඇතුළත් කරන්න.");
                return;
            }

            if (isSending) return;
            isSending = true;

            const box = document.getElementById('dispatchProgressBox');
            const status = document.getElementById('dispatchStatusText');
            const bar = document.getElementById('dispatchProgressBar');
            const log = document.getElementById('dispatchLog');

            box.style.display = 'block';
            log.innerHTML = '';

            let currentIdx = 0;
            const total = recipients.length;

            function sendNext() {
                if (currentIdx >= total) {
                    status.innerHTML = "🎉 සියලුම නිලධාරීන්ට WhatsApp සාර්ථකව විවෘත කරන ලදී! (Complete)";
                    bar.style.width = "100%";
                    isSending = false;
                    return;
                }

                const item = recipients[currentIdx];
                const pct = Math.round(((currentIdx + 1) / total) * 100);
                bar.style.width = pct + "%";
                status.innerHTML = `[${currentIdx + 1}/${total}] ${item.name} (${item.phone}) වෙත WhatsApp විවෘත කරමින් පවතී...`;

                window.open(item.url, '_blank');

                const line = document.createElement('div');
                line.style.color = '#4ade80';
                line.style.marginTop = '2px';
                line.innerHTML = `✓ [${currentIdx + 1}/${total}] ${item.name} (${item.phone}) - Dispatched`;
                log.appendChild(line);
                log.scrollTop = log.scrollHeight;

                currentIdx++;
                if (currentIdx < total) {
                    setTimeout(sendNext, 1200);
                } else {
                    setTimeout(() => {
                        status.innerHTML = "🎉 සියලුම දෙනාට WhatsApp සාර්ථකව යවා අවසන්!";
                        isSending = false;
                    }, 1000);
                }
            }

            sendNext();
        }
    </script>
    """.replace("__RECIPIENTS_JSON__", recipients_json)
    st.components.v1.html(dispatcher_html, height=210)

    # Master Group Broadcast & Copy Tools
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        # Group Broadcast text
        group_master_msg = (
            f"📢 *RECOVERY PERFORMANCE MASTER UPDATE*\n"
            f"📅 කාලසීමාව: {selected_month} | {selected_date_choice}\n"
            f"⏳ ඉතිරි වැඩ දින: {working_days} Days\n"
            f"🎯 Total Target: Rs. {format_money(summary['total_target'])}\n"
            f"✅ Total Achieved: Rs. {format_money(summary['total_achieved'])}\n\n"
            f"🌸 *Group Iresha:* Rs. {format_money(summary['iresha_achieved'])} / {format_money(summary['iresha_target'])}\n"
            f"🌿 *Group Dila:* Rs. {format_money(summary['dila_achieved'])} / {format_money(summary['dila_target'])}\n\n"
            f"කරුණාකර සියලු දෙනා දෛනික ඉලක්කය සාක්ෂාත් කිරීමට සහය වන්න! 💪"
        )
        wa_group_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(group_master_msg)}"
        st.markdown(f"""
            <a href="{wa_group_url}" target="_blank" style="text-decoration: none;">
                <button style="width: 100%; background-color: #059669; color: white; border: none; border-radius: 8px; padding: 12px; font-weight: 800; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    👥 WhatsApp Group එකට Master Alert එක යවන්න
                </button>
            </a>
        """, unsafe_allow_html=True)

    with b_col2:
        with st.expander("📋 සියලු පණිවිඩ එකවර පිටපත් කරන්න (Copy All)"):
            st.text_area("සියලු නිලධාරීන්ගේ පණිවිඩ:", value=all_msgs_text, height=140)

    st.markdown("---")

    # 3. MANAGER EXECUTIVE REPORT
    st.markdown("### 👔 Manager Executive Report")
    manager_phone = st.text_input("Manager දුරකථන අංකය:", value=db.get_setting("manager_phone", "0771234567"))
    if manager_phone:
        db.save_setting("manager_phone", manager_phone)

    exec_text = f"🏢 *RECOVERY PERFORMANCE - DAILY EXECUTIVE REPORT*\n"
    exec_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    exec_text += f"📅 *මාසය / දිනය:* {selected_month} | {selected_date_choice}\n"
    exec_text += f"⏳ *ඉතිරි වැඩ දින:* {working_days} Days\n"
    exec_text += f"📑 *මුළු කොන්ත්‍රාත්තු:* {summary['total_contracts']:,}\n\n"
    exec_text += f"📊 *සමස්ත සාරාංශය (GRAND TOTAL):*\n"
    exec_text += f"🎯 Total Target: Rs. {format_money(summary['total_target'])}\n"
    exec_text += f"✅ Total Achieved: Rs. {format_money(summary['total_achieved'])}\n"
    exec_text += f"⚠️ Variance: {format_money(summary['total_variance'])}\n"
    exec_text += f"⚡ Daily Required: Rs. {format_money(summary['daily_required'])} / day\n"
    exec_text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    exec_text += f"🌸 *GROUP IRESHAS (5 Members)*\n"
    exec_text += f"🎯 Target: Rs. {format_money(summary['iresha_target'])} | Achieved: Rs. {format_money(summary['iresha_achieved'])}\n\n"
    exec_text += f"🌿 *GROUP DILA (4 Members)*\n"
    exec_text += f"🎯 Target: Rs. {format_money(summary['dila_target'])} | Achieved: Rs. {format_money(summary['dila_achieved'])}\n"

    st.text_area("පිටපත් කරගැනීමට වාර්තාව (Report Preview):", value=exec_text, height=180)

    m_clean_phone = manager_phone.replace(' ', '').replace('-', '')
    m_intl = '94' + m_clean_phone[1:] if m_clean_phone.startswith('0') else m_clean_phone
    wa_mgr_url = f"https://api.whatsapp.com/send?phone={m_intl}&text={urllib.parse.quote(exec_text)}"

    st.markdown(f"""
        <a href="{wa_mgr_url}" target="_blank" style="text-decoration: none;">
            <button style="background-color: #059669; color: white; border: none; border-radius: 8px; padding: 10px 18px; font-weight: 700; cursor: pointer;">
                💬 Manager වෙත WhatsApp මඟින් යවන්න ({manager_phone})
            </button>
        </a>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 4. INDIVIDUAL OFFICER CARDS
    st.markdown("### 👤 නිලධාරීන්ගේ තනි පුද්ගල WhatsApp පණිවිඩ (Individual Officer Cards)")

    for o in officer_records:
        var_text = f"+Rs. {format_money(o['variance'])}" if o['variance'] >= 0 else f"-Rs. {format_money(abs(o['variance']))}"
        msg = (
            f"📢 *Recovery Update: {o['officer_name']}*\n"
            f"📅 දිනය: {selected_month} | {selected_date_choice}\n"
            f"🎯 Target: Rs. {format_money(o['target'])}\n"
            f"✅ Achieved: Rs. {format_money(o['achieved'])}\n"
            f"⚠️ Variance: {var_text}\n"
            f"⏳ ඉතිරි වැඩ දින: {working_days} Days\n"
            f"⚡ දෛනික ඉලක්කය (Daily): Rs. {format_money(o['daily_required'])}\n\n"
            f"කරුණාකර දෛනික ඉලක්කය සම්පූර්ණ කිරීමට සහය වන්න!"
        )

        ph = st.session_state['officer_phones'].get(o['officer_id'], o.get('phone', '0770000000'))
        clean_ph = ph.replace(' ', '').replace('-', '')
        intl_ph = '94' + clean_ph[1:] if clean_ph.startswith('0') else clean_ph
        o_wa_url = f"https://api.whatsapp.com/send?phone={intl_ph}&text={urllib.parse.quote(msg)}"

        with st.expander(f"✉️ {o['officer_name']} ({o['team_name']}) - 📱 {ph}"):
            st.text_area("පණිවිඩය:", value=msg, height=130, key=f"msg_box_{o['officer_id']}")
            st.markdown(f"""
                <a href="{o_wa_url}" target="_blank">
                    <button style="background-color: #2563eb; color: white; border: none; border-radius: 6px; padding: 6px 14px; font-weight: bold; cursor: pointer;">
                        💬 WhatsApp යවන්න ({ph})
                    </button>
                </a>
            """, unsafe_allow_html=True)
