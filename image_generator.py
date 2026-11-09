"""
Image Generator Module using Pillow (PIL)
Generates high-resolution PNG images for:
1. Membership Loan Daily Target Report (Dark Theme Edition)
2. Officer Performance Breakdown Table
"""

import io
import os
from PIL import Image, ImageDraw, ImageFont


def get_fonts():
    """
    Load clean fonts with cross-platform Linux / Windows fallback.
    """
    candidates_bold = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
        "arialbd.ttf"
    ]
    candidates_reg = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "DejaVuSans.ttf",
        "arial.ttf"
    ]

    font_bold_path = next((p for p in candidates_bold if os.path.exists(p)), None)
    font_reg_path = next((p for p in candidates_reg if os.path.exists(p)), None)

    try:
        if font_bold_path and font_reg_path:
            f_title = ImageFont.truetype(font_bold_path, 26)
            f_subtitle = ImageFont.truetype(font_bold_path, 16)
            f_badge = ImageFont.truetype(font_bold_path, 18)
            f_header = ImageFont.truetype(font_bold_path, 15)
            f_cell = ImageFont.truetype(font_bold_path, 16)
            f_cell_reg = ImageFont.truetype(font_reg_path, 16)
            f_footer = ImageFont.truetype(font_bold_path, 18)
            f_small = ImageFont.truetype(font_reg_path, 14)
        else:
            default_f = ImageFont.load_default()
            f_title = f_subtitle = f_badge = f_header = f_cell = f_cell_reg = f_footer = f_small = default_f
    except Exception:
        default_f = ImageFont.load_default()
        f_title = f_subtitle = f_badge = f_header = f_cell = f_cell_reg = f_footer = f_small = default_f

    return {
        'title': f_title,
        'subtitle': f_subtitle,
        'badge': f_badge,
        'header': f_header,
        'cell': f_cell,
        'cell_reg': f_cell_reg,
        'footer': f_footer,
        'small': f_small
    }


def format_money(val):
    return f"{val:,.0f}"


def generate_dark_table_png(summary, iresha_rows, dila_rows, selected_month, selected_date_choice, working_days, show_daily_col=True):
    """
    Renders the exact Dark Theme Daily Target Report as a high-resolution PNG image.
    """
    fonts = get_fonts()
    width = 1400
    row_height = 42
    max_rows = max(len(iresha_rows), len(dila_rows))
    
    # Calculate height
    # Padding(30) + TitleBanner(90) + GroupBanner(45) + HeaderRow(45) + DataRows(max_rows * row_height) + Footers(100) + HighlightBox(80) + Padding(30)
    height = 400 + (max_rows * row_height)

    img = Image.new("RGB", (width, height), color="#171d2b")
    draw = ImageDraw.Draw(img)

    margin_x = 40
    curr_y = 35

    # 1. Header Banner (Gray pill)
    banner_w = width - (margin_x * 2)
    banner_h = 75
    draw.rounded_rectangle([margin_x, curr_y, margin_x + banner_w, curr_y + banner_h], radius=10, fill="#8c9ba8")
    
    title_text = f"MEMBERSHIP LOAN TARGET - {selected_month.upper()}"
    if show_daily_col:
        sub_text = f"DATE / VIEW: {selected_date_choice.upper()}  |  REMAINING WORKING DAYS: {working_days} DAYS (EXCL. SAT/SUN)"
    else:
        sub_text = f"DATE: {selected_date_choice.upper()}  |  DAILY TRANSACTIONS PERFORMANCE VIEW"

    draw.text((width // 2, curr_y + 14), title_text, font=fonts['title'], fill="#171d2b", anchor="mt")
    draw.text((width // 2, curr_y + 48), sub_text, font=fonts['subtitle'], fill="#24303e", anchor="mt")
    curr_y += banner_h + 16

    # 2. Team Sub-headers (Group Iresha vs Group Dila)
    group_h = 36
    half_w = banner_w // 2
    # Left: Group Iresha
    draw.rectangle([margin_x, curr_y, margin_x + half_w, curr_y + group_h], fill="#0f131c")
    draw.text((margin_x + half_w // 2, curr_y + 8), "GROUP IRESHAS (5 MEMBERS)", font=fonts['badge'], fill="#f59e0b", anchor="mt")
    # Right: Group Dila
    draw.rectangle([margin_x + half_w, curr_y, margin_x + banner_w, curr_y + group_h], fill="#0f131c")
    draw.text((margin_x + half_w + half_w // 2, curr_y + 8), "GROUP DILA (4 MEMBERS)", font=fonts['badge'], fill="#f59e0b", anchor="mt")
    curr_y += group_h

    # 3. Table Column Headers
    header_h = 36
    draw.rectangle([margin_x, curr_y, margin_x + banner_w, curr_y + header_h], fill="#1a2233")

    if show_daily_col:
        # 5 cols per side
        col_w_name = int(half_w * 0.28)
        col_w_tgt = int(half_w * 0.18)
        col_w_ach = int(half_w * 0.18)
        col_w_var = int(half_w * 0.18)
        col_w_dly = half_w - (col_w_name + col_w_tgt + col_w_ach + col_w_var)
        cols_spec = [("NAME", col_w_name, "left"), ("TARGET", col_w_tgt, "right"), ("ACHIEV.", col_w_ach, "right"), ("VARIANCE", col_w_var, "right"), (f"DAILY ({working_days}D)", col_w_dly, "right")]
    else:
        # 3 cols per side (NAME, TARGET, ACHIEV. - VARIANCE & DAILY omitted on specific date)
        col_w_name = int(half_w * 0.40)
        col_w_tgt = int(half_w * 0.30)
        col_w_ach = half_w - (col_w_name + col_w_tgt)
        cols_spec = [("NAME", col_w_name, "left"), ("TARGET", col_w_tgt, "right"), ("ACHIEV.", col_w_ach, "right")]

    # Draw Headers for left and right
    def draw_col_headers(start_x):
        x = start_x
        for title, cw, align in cols_spec:
            color = "#38bdf8" if "DAILY" in title else "#94a3b8"
            tx = x + 12 if align == "left" else x + cw - 12
            draw.text((tx, curr_y + 10), title, font=fonts['header'], fill=color, anchor="lt" if align == "left" else "rt")
            x += cw

    draw_col_headers(margin_x)
    draw_col_headers(margin_x + half_w)
    
    # Separator line
    draw.line([margin_x + half_w, curr_y, margin_x + half_w, curr_y + header_h + (max_rows * row_height) + 85], fill="#334155", width=2)
    curr_y += header_h

    # 4. Data Rows
    for i in range(max_rows):
        i_item = iresha_rows[i] if i < len(iresha_rows) else None
        d_item = dila_rows[i] if i < len(dila_rows) else None
        row_bg = "#171d2b" if i % 2 == 0 else "#141926"

        draw.rectangle([margin_x, curr_y, margin_x + banner_w, curr_y + row_height], fill=row_bg)
        draw.line([margin_x, curr_y + row_height, margin_x + banner_w, curr_y + row_height], fill="#1e293b", width=1)

        # Draw Left (Iresha)
        if i_item:
            x = margin_x
            draw.text((x + 12, curr_y + 12), i_item['officer_name'], font=fonts['cell'], fill="#ffffff", anchor="lt")
            x += cols_spec[0][1]
            draw.text((x + cols_spec[1][1] - 12, curr_y + 12), format_money(i_item['target']), font=fonts['cell_reg'], fill="#cbd5e1", anchor="rt")
            x += cols_spec[1][1]
            draw.text((x + cols_spec[2][1] - 12, curr_y + 12), format_money(i_item['achieved']), font=fonts['cell'], fill="#ffffff", anchor="rt")
            x += cols_spec[2][1]
            if show_daily_col:
                var_color = "#4ade80" if i_item['variance'] >= 0 else "#f87171"
                var_str = f"+{format_money(i_item['variance'])}" if i_item['variance'] >= 0 else f"({format_money(abs(i_item['variance']))})"
                draw.text((x + cols_spec[3][1] - 12, curr_y + 12), var_str, font=fonts['cell'], fill=var_color, anchor="rt")
                x += cols_spec[3][1]
                draw.text((x + cols_spec[4][1] - 12, curr_y + 12), format_money(i_item['daily_required']), font=fonts['cell'], fill="#38bdf8", anchor="rt")
        else:
            draw.text((margin_x + half_w // 2, curr_y + 12), "-", font=fonts['cell'], fill="#64748b", anchor="mt")

        # Draw Right (Dila)
        if d_item:
            x = margin_x + half_w
            draw.text((x + 12, curr_y + 12), d_item['officer_name'], font=fonts['cell'], fill="#ffffff", anchor="lt")
            x += cols_spec[0][1]
            draw.text((x + cols_spec[1][1] - 12, curr_y + 12), format_money(d_item['target']), font=fonts['cell_reg'], fill="#cbd5e1", anchor="rt")
            x += cols_spec[1][1]
            draw.text((x + cols_spec[2][1] - 12, curr_y + 12), format_money(d_item['achieved']), font=fonts['cell'], fill="#ffffff", anchor="rt")
            x += cols_spec[2][1]
            if show_daily_col:
                var_color = "#4ade80" if d_item['variance'] >= 0 else "#f87171"
                var_str = f"+{format_money(d_item['variance'])}" if d_item['variance'] >= 0 else f"({format_money(abs(d_item['variance']))})"
                draw.text((x + cols_spec[3][1] - 12, curr_y + 12), var_str, font=fonts['cell'], fill=var_color, anchor="rt")
                x += cols_spec[3][1]
                draw.text((x + cols_spec[4][1] - 12, curr_y + 12), format_money(d_item['daily_required']), font=fonts['cell'], fill="#38bdf8", anchor="rt")
        else:
            draw.text((margin_x + half_w + half_w // 2, curr_y + 12), "-", font=fonts['cell'], fill="#64748b", anchor="mt")

        curr_y += row_height

    # 5. Team Totals Footer Row
    tfoot_h = 42
    draw.rectangle([margin_x, curr_y, margin_x + banner_w, curr_y + tfoot_h], fill="#121824")
    draw.line([margin_x, curr_y, margin_x + banner_w, curr_y], fill="#334155", width=2)

    # Left Team Total
    x = margin_x
    draw.text((x + 12, curr_y + 12), "TOTAL", font=fonts['footer'], fill="#ffffff", anchor="lt")
    x += cols_spec[0][1]
    draw.text((x + cols_spec[1][1] - 12, curr_y + 12), format_money(summary['iresha_target']), font=fonts['footer'], fill="#cbd5e1", anchor="rt")
    x += cols_spec[1][1]
    draw.text((x + cols_spec[2][1] - 12, curr_y + 12), format_money(summary['iresha_achieved']), font=fonts['footer'], fill="#fcd34d", anchor="rt")
    x += cols_spec[2][1]
    if show_daily_col:
        i_tot_var = summary['iresha_achieved'] - summary['iresha_target']
        i_var_str = f"+{format_money(i_tot_var)}" if i_tot_var >= 0 else f"({format_money(abs(i_tot_var))})"
        draw.text((x + cols_spec[3][1] - 12, curr_y + 12), i_var_str, font=fonts['footer'], fill="#4ade80" if i_tot_var >= 0 else "#f87171", anchor="rt")
        x += cols_spec[3][1]
        i_rem = max(0.0, summary['iresha_target'] - summary['iresha_achieved'])
        i_daily = round(i_rem / working_days) if working_days > 0 else 0
        draw.text((x + cols_spec[4][1] - 12, curr_y + 12), format_money(i_daily), font=fonts['footer'], fill="#38bdf8", anchor="rt")

    # Right Team Total
    x = margin_x + half_w
    draw.text((x + 12, curr_y + 12), "TOTAL", font=fonts['footer'], fill="#ffffff", anchor="lt")
    x += cols_spec[0][1]
    draw.text((x + cols_spec[1][1] - 12, curr_y + 12), format_money(summary['dila_target']), font=fonts['footer'], fill="#cbd5e1", anchor="rt")
    x += cols_spec[1][1]
    draw.text((x + cols_spec[2][1] - 12, curr_y + 12), format_money(summary['dila_achieved']), font=fonts['footer'], fill="#fcd34d", anchor="rt")
    x += cols_spec[2][1]
    if show_daily_col:
        d_tot_var = summary['dila_achieved'] - summary['dila_target']
        d_var_str = f"+{format_money(d_tot_var)}" if d_tot_var >= 0 else f"({format_money(abs(d_tot_var))})"
        draw.text((x + cols_spec[3][1] - 12, curr_y + 12), d_var_str, font=fonts['footer'], fill="#4ade80" if d_tot_var >= 0 else "#f87171", anchor="rt")
        x += cols_spec[3][1]
        d_rem = max(0.0, summary['dila_target'] - summary['dila_achieved'])
        d_daily = round(d_rem / working_days) if working_days > 0 else 0
        draw.text((x + cols_spec[4][1] - 12, curr_y + 12), format_money(d_daily), font=fonts['footer'], fill="#38bdf8", anchor="rt")

    curr_y += tfoot_h

    # 6. Prominent Grand Total Row
    grand_h = 44
    draw.rectangle([margin_x, curr_y, margin_x + banner_w, curr_y + grand_h], fill="#0b0f19")
    draw.line([margin_x, curr_y, margin_x + banner_w, curr_y], fill="#d97706", width=2)
    
    tot_pct = (summary['total_achieved'] / summary['total_target'] * 100) if summary['total_target'] > 0 else 0
    gt_target_str = f"🎯 GRAND TOTAL TARGET: LKR {format_money(summary['total_target'])}"
    if show_daily_col:
        gt_achieved_str = f"✅ TOTAL ACHIEVED: LKR {format_money(summary['total_achieved'])} ({tot_pct:.1f}%)"
    else:
        gt_achieved_str = f"✅ TOTAL COLLECTED ON {selected_date_choice}: LKR {format_money(summary['total_achieved'])}"
    
    draw.text((margin_x + half_w // 2, curr_y + 12), gt_target_str, font=fonts['footer'], fill="#fbbf24", anchor="mt")
    draw.text((margin_x + half_w + half_w // 2, curr_y + 12), gt_achieved_str, font=fonts['footer'], fill="#4ade80", anchor="mt")
    curr_y += grand_h + 16

    # 7. Bottom Highlight Card (No GRAND TOTAL REMAINING on specific date view)
    box_h = 56
    outline_color = "#10b981" if not show_daily_col else "#d97706"
    draw.rounded_rectangle([margin_x, curr_y, margin_x + banner_w, curr_y + box_h], radius=8, fill="#121824", outline=outline_color, width=1)
    
    if show_daily_col:
        rem_text = f"GRAND TOTAL REMAINING: LKR {format_money(summary['total_remaining'])}"
        daily_text = f"DAILY REQUIRED TARGET ({working_days} DAYS): LKR {format_money(summary['daily_required'])}"
        draw.text((margin_x + 20, curr_y + 18), rem_text, font=fonts['footer'], fill="#fbbf24", anchor="lt")
        draw.text((margin_x + banner_w - 20, curr_y + 18), daily_text, font=fonts['footer'], fill="#38bdf8", anchor="rt")
    else:
        # On specific date: completely omit GRAND TOTAL REMAINING
        collected_text = f"📅 TOTAL COLLECTED ON {selected_date_choice}: LKR {format_money(summary['total_achieved'])}"
        teams_text = f"GROUP IRESHAS: LKR {format_money(summary['iresha_achieved'])}   |   GROUP DILA: LKR {format_money(summary['dila_achieved'])}"
        draw.text((margin_x + 20, curr_y + 18), collected_text, font=fonts['footer'], fill="#4ade80", anchor="lt")
        draw.text((margin_x + banner_w - 20, curr_y + 18), teams_text, font=fonts['footer'], fill="#38bdf8", anchor="rt")

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()


def generate_officer_breakdown_png(officer_records, selected_month, selected_date_choice):
    """
    Renders the Officer Performance Breakdown Table as a clean, high-resolution PNG image.
    """
    fonts = get_fonts()
    width = 1300
    row_h = 42
    sorted_officers = sorted(officer_records, key=lambda x: x['achieved'], reverse=True)
    num_rows = len(sorted_officers)

    height = 280 + (num_rows * row_h)

    img = Image.new("RGB", (width, height), color="#0f172a")
    draw = ImageDraw.Draw(img)

    margin_x = 40
    curr_y = 35
    table_w = width - (margin_x * 2)

    # 1. Header Banner
    draw.rounded_rectangle([margin_x, curr_y, margin_x + table_w, curr_y + 70], radius=8, fill="#1e293b", outline="#334155", width=1)
    draw.text((width // 2, curr_y + 14), f"OFFICER PERFORMANCE BREAKDOWN - {selected_month.upper()}", font=fonts['title'], fill="#f8fafc", anchor="mt")
    draw.text((width // 2, curr_y + 44), f"VIEW: {selected_date_choice.upper()}  |  TOTAL OFFICERS: {num_rows}", font=fonts['small'], fill="#94a3b8", anchor="mt")
    curr_y += 85

    # 2. Table Column Headers
    cols = [
        ("RANK", int(table_w * 0.08), "center"),
        ("OFFICER NAME", int(table_w * 0.24), "left"),
        ("TEAM", int(table_w * 0.16), "left"),
        ("CONTRACTS", int(table_w * 0.12), "right"),
        ("TARGET (LKR)", int(table_w * 0.14), "right"),
        ("ACHIEVED (LKR)", int(table_w * 0.14), "right"),
        ("PROGRESS %", table_w - int(table_w * 0.88), "right"),
    ]

    header_h = 36
    draw.rectangle([margin_x, curr_y, margin_x + table_w, curr_y + header_h], fill="#1e293b")

    x = margin_x
    for title, cw, align in cols:
        tx = x + cw // 2 if align == "center" else (x + 12 if align == "left" else x + cw - 12)
        draw.text((tx, curr_y + 10), title, font=fonts['header'], fill="#94a3b8", anchor="mt" if align == "center" else ("lt" if align == "left" else "rt"))
        x += cw
    curr_y += header_h

    # 3. Data Rows
    tot_target = 0
    tot_achieved = 0
    tot_contracts = 0

    for rank, o in enumerate(sorted_officers, start=1):
        row_bg = "#0f172a" if rank % 2 == 1 else "#141e33"
        draw.rectangle([margin_x, curr_y, margin_x + table_w, curr_y + row_h], fill=row_bg)
        draw.line([margin_x, curr_y + row_h, margin_x + table_w, curr_y + row_h], fill="#1e293b", width=1)

        medal = "1" if rank == 1 else ("2" if rank == 2 else ("3" if rank == 3 else str(rank)))
        medal_color = "#f59e0b" if rank == 1 else ("#cbd5e1" if rank == 2 else ("#b45309" if rank == 3 else "#94a3b8"))

        pct = o['achieved_pct']
        pct_color = "#4ade80" if pct >= 100 else ("#facc15" if pct >= 50 else "#f87171")

        tot_target += o['target']
        tot_achieved += o['achieved']
        tot_contracts += o['contracts_count']

        x = margin_x
        # Rank
        draw.text((x + cols[0][1] // 2, curr_y + 12), f"#{medal}", font=fonts['cell'], fill=medal_color, anchor="mt")
        x += cols[0][1]
        # Name
        draw.text((x + 12, curr_y + 12), o['officer_name'], font=fonts['cell'], fill="#ffffff", anchor="lt")
        x += cols[1][1]
        # Team
        team_color = "#f472b6" if "Iresha" in o['team_name'] else "#34d399"
        draw.text((x + 12, curr_y + 12), o['team_name'], font=fonts['cell'], fill=team_color, anchor="lt")
        x += cols[2][1]
        # Contracts
        draw.text((x + cols[3][1] - 12, curr_y + 12), str(o['contracts_count']), font=fonts['cell_reg'], fill="#e2e8f0", anchor="rt")
        x += cols[3][1]
        # Target
        draw.text((x + cols[4][1] - 12, curr_y + 12), format_money(o['target']), font=fonts['cell_reg'], fill="#cbd5e1", anchor="rt")
        x += cols[4][1]
        # Achieved
        draw.text((x + cols[5][1] - 12, curr_y + 12), format_money(o['achieved']), font=fonts['cell'], fill="#ffffff", anchor="rt")
        x += cols[5][1]
        # Progress %
        draw.text((x + cols[6][1] - 12, curr_y + 12), f"{pct:.1f}%", font=fonts['cell'], fill=pct_color, anchor="rt")

        curr_y += row_h

    # 4. Total Footer Row
    foot_h = 44
    draw.rectangle([margin_x, curr_y, margin_x + table_w, curr_y + foot_h], fill="#1e293b")
    draw.line([margin_x, curr_y, margin_x + table_w, curr_y], fill="#38bdf8", width=2)

    total_pct = (tot_achieved / tot_target * 100) if tot_target > 0 else 0

    x = margin_x
    draw.text((x + cols[0][1] // 2, curr_y + 12), "-", font=fonts['footer'], fill="#94a3b8", anchor="mt")
    x += cols[0][1]
    draw.text((x + 12, curr_y + 12), "GRAND TOTAL", font=fonts['footer'], fill="#ffffff", anchor="lt")
    x += cols[1][1]
    draw.text((x + 12, curr_y + 12), "ALL TEAMS", font=fonts['footer'], fill="#38bdf8", anchor="lt")
    x += cols[2][1]
    draw.text((x + cols[3][1] - 12, curr_y + 12), str(tot_contracts), font=fonts['footer'], fill="#ffffff", anchor="rt")
    x += cols[3][1]
    draw.text((x + cols[4][1] - 12, curr_y + 12), format_money(tot_target), font=fonts['footer'], fill="#cbd5e1", anchor="rt")
    x += cols[4][1]
    draw.text((x + cols[5][1] - 12, curr_y + 12), format_money(tot_achieved), font=fonts['footer'], fill="#4ade80", anchor="rt")
    x += cols[5][1]
    draw.text((x + cols[6][1] - 12, curr_y + 12), f"{total_pct:.1f}%", font=fonts['footer'], fill="#4ade80", anchor="rt")

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()
