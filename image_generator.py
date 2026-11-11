"""
Image Generator Module using Pillow (PIL)
Generates high-resolution, crystal-clear PNG images for:
1. Membership Loan Daily Target Report (Dark Theme Edition)
2. Officer Performance Breakdown Table
"""

import io
import os
import tempfile
import urllib.request
from PIL import Image, ImageDraw, ImageFont


def _ensure_bundled_fonts():
    """
    Resolve Bold & Regular TTF font paths reliably across Windows, Mac, and Linux (Streamlit Cloud).
    Checks local bundled fonts/, Linux system fonts, Windows fonts, and /tmp cache (with auto-download fallback).
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_bold = os.path.join(base_dir, "fonts", "Roboto-Bold.ttf")
    local_reg = os.path.join(base_dir, "fonts", "Roboto-Regular.ttf")

    candidates_bold = [
        local_bold,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        os.path.join(tempfile.gettempdir(), "Roboto-Bold.ttf"),
    ]
    candidates_reg = [
        local_reg,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        os.path.join(tempfile.gettempdir(), "Roboto-Regular.ttf"),
    ]

    font_bold_path = next((p for p in candidates_bold if os.path.exists(p)), None)
    font_reg_path = next((p for p in candidates_reg if os.path.exists(p)), None)

    # Auto-download open-source Roboto TTFs into temp cache if running in a minimal container without fonts/
    if not font_bold_path or not font_reg_path:
        try:
            tmp_bold = os.path.join(tempfile.gettempdir(), "Roboto-Bold.ttf")
            tmp_reg = os.path.join(tempfile.gettempdir(), "Roboto-Regular.ttf")
            if not os.path.exists(tmp_bold):
                urllib.request.urlretrieve(
                    "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf",
                    tmp_bold,
                )
            if not os.path.exists(tmp_reg):
                urllib.request.urlretrieve(
                    "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf",
                    tmp_reg,
                )
            if os.path.exists(tmp_bold) and os.path.exists(tmp_reg):
                font_bold_path = tmp_bold
                font_reg_path = tmp_reg
        except Exception:
            pass

    return font_bold_path, font_reg_path


def _load_font(path, size):
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    # Pillow >= 10.1.0 supports sized default font fallback cleanly
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def get_fonts(scale_factor=1.0):
    """
    Load large, sharp, mobile-friendly fonts for PNG rendering.
    """
    font_bold_path, font_reg_path = _ensure_bundled_fonts()

    def s(px):
        return max(12, int(round(px * scale_factor)))

    return {
        "title": _load_font(font_bold_path, s(34)),
        "subtitle": _load_font(font_bold_path, s(20)),
        "badge": _load_font(font_bold_path, s(22)),
        "header": _load_font(font_bold_path, s(18)),
        "cell": _load_font(font_bold_path, s(22)),
        "cell_reg": _load_font(font_reg_path, s(21)),
        "footer": _load_font(font_bold_path, s(23)),
        "highlight": _load_font(font_bold_path, s(24)),
        "small": _load_font(font_reg_path, s(18)),
    }


def format_money(val):
    return f"{val:,.0f}"


def generate_dark_table_png(
    summary,
    iresha_rows,
    dila_rows,
    selected_month,
    selected_date_choice,
    working_days,
    show_daily_col=True,
):
    """
    Renders the exact Dark Theme Daily Target Report as a crisp, large-font, high-resolution PNG image
    optimized for both desktop viewing and mobile WhatsApp sharing.
    """
    fonts = get_fonts()

    # Compact canvas width when showing fewer columns so font-to-width ratio stays large & sharp!
    width = 1660 if show_daily_col else 1360
    margin_x = 32
    banner_w = width - (margin_x * 2)
    half_w = banner_w // 2

    max_rows = max(len(iresha_rows), len(dila_rows), 1)
    banner_h = 98
    group_h = 48
    header_h = 46
    row_height = 54
    tfoot_h = 56
    grand_h = 60
    box_h = 74

    # Exact total height calculation with clean bottom margin
    height = (
        30  # top margin
        + banner_h
        + 16  # gap
        + group_h
        + header_h
        + (max_rows * row_height)
        + tfoot_h
        + grand_h
        + 18  # gap
        + box_h
        + 32  # bottom margin
    )

    img = Image.new("RGB", (width, height), color="#171d2b")
    draw = ImageDraw.Draw(img)

    curr_y = 30

    # 1. Header Banner (Steel Blue-Gray Pill)
    draw.rounded_rectangle(
        [margin_x, curr_y, margin_x + banner_w, curr_y + banner_h],
        radius=12,
        fill="#94a3b8",
    )

    title_text = f"MEMBERSHIP LOAN TARGET - {selected_month.upper()}"
    if show_daily_col:
        sub_text = f"VIEW: ALL DATES  |  REMAINING WORKING DAYS: {working_days} DAYS (EXCL. SAT/SUN)"
    else:
        sub_text = f"DATE: {selected_date_choice.upper()}  |  DAILY TRANSACTIONS PERFORMANCE VIEW"

    draw.text((width // 2, curr_y + 32), title_text, font=fonts["title"], fill="#0f172a", anchor="mm")
    draw.text((width // 2, curr_y + 72), sub_text, font=fonts["subtitle"], fill="#1e293b", anchor="mm")
    curr_y += banner_h + 16

    table_top_y = curr_y

    # 2. Team Sub-headers (Group Iresha vs Group Dila)
    draw.rectangle([margin_x, curr_y, margin_x + half_w, curr_y + group_h], fill="#0b0f19")
    draw.text(
        (margin_x + half_w // 2, curr_y + group_h // 2),
        f"GROUP IRESHA ({len(iresha_rows)} MEMBERS)",
        font=fonts["badge"],
        fill="#fbbf24",
        anchor="mm",
    )

    draw.rectangle([margin_x + half_w, curr_y, margin_x + banner_w, curr_y + group_h], fill="#0b0f19")
    draw.text(
        (margin_x + half_w + half_w // 2, curr_y + group_h // 2),
        f"GROUP DILA ({len(dila_rows)} MEMBERS)",
        font=fonts["badge"],
        fill="#fbbf24",
        anchor="mm",
    )
    curr_y += group_h

    # 3. Table Column Headers
    draw.rectangle([margin_x, curr_y, margin_x + banner_w, curr_y + header_h], fill="#1e293b")

    if show_daily_col:
        # 5 cols per side inside half_w (800px)
        col_w_name = int(half_w * 0.295)
        col_w_tgt = int(half_w * 0.165)
        col_w_ach = int(half_w * 0.165)
        col_w_var = int(half_w * 0.195)
        col_w_dly = half_w - (col_w_name + col_w_tgt + col_w_ach + col_w_var)
        cols_spec = [
            ("NAME", col_w_name, "left"),
            ("TARGET", col_w_tgt, "right"),
            ("ACHIEV.", col_w_ach, "right"),
            ("VARIANCE", col_w_var, "right"),
            (f"DAILY ({working_days}D)", col_w_dly, "right"),
        ]
    else:
        # 3 cols per side inside half_w (648px)
        col_w_name = int(half_w * 0.44)
        col_w_tgt = int(half_w * 0.28)
        col_w_ach = half_w - (col_w_name + col_w_tgt)
        cols_spec = [
            ("NAME", col_w_name, "left"),
            ("TARGET", col_w_tgt, "right"),
            ("ACHIEV.", col_w_ach, "right"),
        ]

    def draw_col_headers(start_x, y_top):
        x = start_x
        mid_y = y_top + header_h // 2
        for title, cw, align in cols_spec:
            color = "#38bdf8" if "DAILY" in title else "#cbd5e1"
            tx = x + 16 if align == "left" else x + cw - 16
            anchor = "lm" if align == "left" else "rm"
            draw.text((tx, mid_y), title, font=fonts["header"], fill=color, anchor=anchor)
            x += cw

    draw_col_headers(margin_x, curr_y)
    draw_col_headers(margin_x + half_w, curr_y)
    draw.line([margin_x, curr_y + header_h, margin_x + banner_w, curr_y + header_h], fill="#334155", width=2)
    curr_y += header_h

    # 4. Data Rows
    for i in range(max_rows):
        i_item = iresha_rows[i] if i < len(iresha_rows) else None
        d_item = dila_rows[i] if i < len(dila_rows) else None
        row_bg = "#171d2b" if i % 2 == 0 else "#131926"
        mid_y = curr_y + row_height // 2

        draw.rectangle([margin_x, curr_y, margin_x + banner_w, curr_y + row_height], fill=row_bg)
        draw.line([margin_x, curr_y + row_height, margin_x + banner_w, curr_y + row_height], fill="#1e293b", width=1)

        # Draw Left (Iresha)
        if i_item:
            x = margin_x
            draw.text((x + 16, mid_y), i_item["officer_name"], font=fonts["cell"], fill="#ffffff", anchor="lm")
            x += cols_spec[0][1]
            draw.text((x + cols_spec[1][1] - 16, mid_y), format_money(i_item["target"]), font=fonts["cell_reg"], fill="#cbd5e1", anchor="rm")
            x += cols_spec[1][1]
            draw.text((x + cols_spec[2][1] - 16, mid_y), format_money(i_item["achieved"]), font=fonts["cell"], fill="#ffffff", anchor="rm")
            x += cols_spec[2][1]
            if show_daily_col:
                var_color = "#4ade80" if i_item["variance"] >= 0 else "#f87171"
                var_str = f"+{format_money(i_item['variance'])}" if i_item["variance"] >= 0 else f"({format_money(abs(i_item['variance']))})"
                draw.text((x + cols_spec[3][1] - 16, mid_y), var_str, font=fonts["cell"], fill=var_color, anchor="rm")
                x += cols_spec[3][1]
                draw.text((x + cols_spec[4][1] - 16, mid_y), format_money(i_item["daily_required"]), font=fonts["cell"], fill="#38bdf8", anchor="rm")
        else:
            draw.text((margin_x + half_w // 2, mid_y), "-", font=fonts["cell"], fill="#64748b", anchor="mm")

        # Draw Right (Dila)
        if d_item:
            x = margin_x + half_w
            draw.text((x + 16, mid_y), d_item["officer_name"], font=fonts["cell"], fill="#ffffff", anchor="lm")
            x += cols_spec[0][1]
            draw.text((x + cols_spec[1][1] - 16, mid_y), format_money(d_item["target"]), font=fonts["cell_reg"], fill="#cbd5e1", anchor="rm")
            x += cols_spec[1][1]
            draw.text((x + cols_spec[2][1] - 16, mid_y), format_money(d_item["achieved"]), font=fonts["cell"], fill="#ffffff", anchor="rm")
            x += cols_spec[2][1]
            if show_daily_col:
                var_color = "#4ade80" if d_item["variance"] >= 0 else "#f87171"
                var_str = f"+{format_money(d_item['variance'])}" if d_item["variance"] >= 0 else f"({format_money(abs(d_item['variance']))})"
                draw.text((x + cols_spec[3][1] - 16, mid_y), var_str, font=fonts["cell"], fill=var_color, anchor="rm")
                x += cols_spec[3][1]
                draw.text((x + cols_spec[4][1] - 16, mid_y), format_money(d_item["daily_required"]), font=fonts["cell"], fill="#38bdf8", anchor="rm")
        else:
            draw.text((margin_x + half_w + half_w // 2, mid_y), "-", font=fonts["cell"], fill="#64748b", anchor="mm")

        curr_y += row_height

    # 5. Team Totals Footer Row
    mid_y = curr_y + tfoot_h // 2
    draw.rectangle([margin_x, curr_y, margin_x + banner_w, curr_y + tfoot_h], fill="#111827")
    draw.line([margin_x, curr_y, margin_x + banner_w, curr_y], fill="#475569", width=2)

    # Highlight background for Team Achieved cells (like the Amber-cream highlight in HTML)
    i_ach_x = margin_x + cols_spec[0][1] + cols_spec[1][1]
    draw.rectangle([i_ach_x + 4, curr_y + 4, i_ach_x + cols_spec[2][1] - 4, curr_y + tfoot_h - 4], fill="#fef3c7")

    d_ach_x = margin_x + half_w + cols_spec[0][1] + cols_spec[1][1]
    draw.rectangle([d_ach_x + 4, curr_y + 4, d_ach_x + cols_spec[2][1] - 4, curr_y + tfoot_h - 4], fill="#fef3c7")

    # Left Team Total
    x = margin_x
    draw.text((x + 16, mid_y), "TOTAL", font=fonts["footer"], fill="#ffffff", anchor="lm")
    x += cols_spec[0][1]
    draw.text((x + cols_spec[1][1] - 16, mid_y), format_money(summary["iresha_target"]), font=fonts["footer"], fill="#e2e8f0", anchor="rm")
    x += cols_spec[1][1]
    draw.text((x + cols_spec[2][1] - 16, mid_y), format_money(summary["iresha_achieved"]), font=fonts["footer"], fill="#78350f", anchor="rm")
    x += cols_spec[2][1]
    if show_daily_col:
        i_tot_var = summary["iresha_achieved"] - summary["iresha_target"]
        i_var_str = f"+{format_money(i_tot_var)}" if i_tot_var >= 0 else f"({format_money(abs(i_tot_var))})"
        draw.text((x + cols_spec[3][1] - 16, mid_y), i_var_str, font=fonts["footer"], fill="#4ade80" if i_tot_var >= 0 else "#f87171", anchor="rm")
        x += cols_spec[3][1]
        i_rem = max(0.0, summary["iresha_target"] - summary["iresha_achieved"])
        i_daily = round(i_rem / working_days) if working_days > 0 else 0
        draw.text((x + cols_spec[4][1] - 16, mid_y), format_money(i_daily), font=fonts["footer"], fill="#38bdf8", anchor="rm")

    # Right Team Total
    x = margin_x + half_w
    draw.text((x + 16, mid_y), "TOTAL", font=fonts["footer"], fill="#ffffff", anchor="lm")
    x += cols_spec[0][1]
    draw.text((x + cols_spec[1][1] - 16, mid_y), format_money(summary["dila_target"]), font=fonts["footer"], fill="#e2e8f0", anchor="rm")
    x += cols_spec[1][1]
    draw.text((x + cols_spec[2][1] - 16, mid_y), format_money(summary["dila_achieved"]), font=fonts["footer"], fill="#78350f", anchor="rm")
    x += cols_spec[2][1]
    if show_daily_col:
        d_tot_var = summary["dila_achieved"] - summary["dila_target"]
        d_var_str = f"+{format_money(d_tot_var)}" if d_tot_var >= 0 else f"({format_money(abs(d_tot_var))})"
        draw.text((x + cols_spec[3][1] - 16, mid_y), d_var_str, font=fonts["footer"], fill="#4ade80" if d_tot_var >= 0 else "#f87171", anchor="rm")
        x += cols_spec[3][1]
        d_rem = max(0.0, summary["dila_target"] - summary["dila_achieved"])
        d_daily = round(d_rem / working_days) if working_days > 0 else 0
        draw.text((x + cols_spec[4][1] - 16, mid_y), format_money(d_daily), font=fonts["footer"], fill="#38bdf8", anchor="rm")

    curr_y += tfoot_h

    # 6. Prominent Grand Total Row (Split Green Left / Gold Right)
    mid_y = curr_y + grand_h // 2
    draw.rectangle([margin_x, curr_y, margin_x + half_w, curr_y + grand_h], fill="#0b0f19")
    draw.rectangle([margin_x + half_w, curr_y, margin_x + banner_w, curr_y + grand_h], fill="#052e16")
    border_top_col = "#10b981" if not show_daily_col else "#d97706"
    draw.line([margin_x, curr_y, margin_x + banner_w, curr_y], fill=border_top_col, width=3)

    tot_pct = (summary["total_achieved"] / summary["total_target"] * 100) if summary["total_target"] > 0 else 0
    gt_target_str = f"GRAND TOTAL TARGET: LKR {format_money(summary['total_target'])}"
    if show_daily_col:
        gt_achieved_str = f"TOTAL ACHIEVED: LKR {format_money(summary['total_achieved'])} ({tot_pct:.1f}%)"
    else:
        gt_achieved_str = f"TOTAL COLLECTED ({selected_date_choice}): LKR {format_money(summary['total_achieved'])}"

    draw.text((margin_x + half_w // 2, mid_y), gt_target_str, font=fonts["highlight"], fill="#fbbf24", anchor="mm")
    draw.text((margin_x + half_w + half_w // 2, mid_y), gt_achieved_str, font=fonts["highlight"], fill="#4ade80", anchor="mm")
    curr_y += grand_h

    # Outer frame + Center Divider for clean crisp edges
    draw.rectangle([margin_x, table_top_y, margin_x + banner_w, curr_y], outline="#334155", width=2)
    draw.line([margin_x + half_w, table_top_y, margin_x + half_w, curr_y], fill="#475569", width=3)

    curr_y += 18

    # 7. Bottom Highlight Card (No GRAND TOTAL REMAINING on specific date view)
    outline_color = "#10b981" if not show_daily_col else "#d97706"
    draw.rounded_rectangle(
        [margin_x, curr_y, margin_x + banner_w, curr_y + box_h],
        radius=10,
        fill="#0f172a",
        outline=outline_color,
        width=2,
    )

    mid_y = curr_y + box_h // 2
    if show_daily_col:
        rem_text = f"GRAND TOTAL REMAINING: LKR {format_money(summary['total_remaining'])}"
        daily_text = f"DAILY REQUIRED ({working_days} DAYS): LKR {format_money(summary['daily_required'])}"
        draw.text((margin_x + 26, mid_y), rem_text, font=fonts["highlight"], fill="#fbbf24", anchor="lm")
        draw.text((margin_x + banner_w - 26, mid_y), daily_text, font=fonts["highlight"], fill="#38bdf8", anchor="rm")
    else:
        # On specific date: completely omit GRAND TOTAL REMAINING
        collected_text = f"TOTAL COLLECTED ON {selected_date_choice}: LKR {format_money(summary['total_achieved'])}"
        teams_text = f"GROUP IRESHA: LKR {format_money(summary['iresha_achieved'])}   |   GROUP DILA: LKR {format_money(summary['dila_achieved'])}"
        draw.text((margin_x + 26, mid_y), collected_text, font=fonts["highlight"], fill="#4ade80", anchor="lm")
        draw.text((margin_x + banner_w - 26, mid_y), teams_text, font=fonts["highlight"], fill="#38bdf8", anchor="rm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def generate_officer_breakdown_png(officer_records, selected_month, selected_date_choice):
    """
    Renders the Officer Performance Breakdown Table as a crisp, large-font, high-resolution PNG image.
    """
    fonts = get_fonts()
    width = 1420
    margin_x = 32
    table_w = width - (margin_x * 2)

    sorted_officers = sorted(officer_records, key=lambda x: x["achieved"], reverse=True)
    num_rows = len(sorted_officers)

    banner_h = 92
    header_h = 46
    row_h = 54
    foot_h = 56

    height = 30 + banner_h + 18 + header_h + (num_rows * row_h) + foot_h + 32

    img = Image.new("RGB", (width, height), color="#0f172a")
    draw = ImageDraw.Draw(img)

    curr_y = 30

    # 1. Header Banner
    draw.rounded_rectangle(
        [margin_x, curr_y, margin_x + table_w, curr_y + banner_h],
        radius=12,
        fill="#1e293b",
        outline="#475569",
        width=2,
    )
    draw.text(
        (width // 2, curr_y + 30),
        f"OFFICER PERFORMANCE BREAKDOWN - {selected_month.upper()}",
        font=fonts["title"],
        fill="#f8fafc",
        anchor="mm",
    )
    draw.text(
        (width // 2, curr_y + 68),
        f"VIEW: {selected_date_choice.upper()}  |  TOTAL OFFICERS: {num_rows}",
        font=fonts["subtitle"],
        fill="#94a3b8",
        anchor="mm",
    )
    curr_y += banner_h + 18
    table_top_y = curr_y

    # 2. Table Column Headers
    cols = [
        ("RANK", int(table_w * 0.08), "center"),
        ("OFFICER NAME", int(table_w * 0.25), "left"),
        ("TEAM", int(table_w * 0.16), "left"),
        ("CONTRACTS", int(table_w * 0.11), "right"),
        ("TARGET (LKR)", int(table_w * 0.14), "right"),
        ("ACHIEVED (LKR)", int(table_w * 0.14), "right"),
        ("PROGRESS %", table_w - int(table_w * 0.88), "right"),
    ]

    draw.rectangle([margin_x, curr_y, margin_x + table_w, curr_y + header_h], fill="#1e293b")
    mid_y = curr_y + header_h // 2

    x = margin_x
    for title, cw, align in cols:
        tx = x + cw // 2 if align == "center" else (x + 16 if align == "left" else x + cw - 16)
        anchor = "mm" if align == "center" else ("lm" if align == "left" else "rm")
        draw.text((tx, mid_y), title, font=fonts["header"], fill="#cbd5e1", anchor=anchor)
        x += cw
    draw.line([margin_x, curr_y + header_h, margin_x + table_w, curr_y + header_h], fill="#334155", width=2)
    curr_y += header_h

    # 3. Data Rows
    tot_target = 0
    tot_achieved = 0
    tot_contracts = 0

    for rank, o in enumerate(sorted_officers, start=1):
        row_bg = "#0f172a" if rank % 2 == 1 else "#141e33"
        mid_y = curr_y + row_h // 2
        draw.rectangle([margin_x, curr_y, margin_x + table_w, curr_y + row_h], fill=row_bg)
        draw.line([margin_x, curr_y + row_h, margin_x + table_w, curr_y + row_h], fill="#1e293b", width=1)

        medal_color = "#fbbf24" if rank == 1 else ("#e2e8f0" if rank == 2 else ("#f59e0b" if rank == 3 else "#94a3b8"))
        pct = o["achieved_pct"]
        pct_color = "#4ade80" if pct >= 100 else ("#facc15" if pct >= 50 else "#f87171")

        tot_target += o["target"]
        tot_achieved += o["achieved"]
        tot_contracts += o["contracts_count"]

        x = margin_x
        draw.text((x + cols[0][1] // 2, mid_y), f"#{rank}", font=fonts["cell"], fill=medal_color, anchor="mm")
        x += cols[0][1]
        draw.text((x + 16, mid_y), o["officer_name"], font=fonts["cell"], fill="#ffffff", anchor="lm")
        x += cols[1][1]
        team_color = "#f472b6" if "Iresha" in o["team_name"] else "#34d399"
        draw.text((x + 16, mid_y), o["team_name"], font=fonts["cell"], fill=team_color, anchor="lm")
        x += cols[2][1]
        draw.text((x + cols[3][1] - 16, mid_y), str(o["contracts_count"]), font=fonts["cell_reg"], fill="#e2e8f0", anchor="rm")
        x += cols[3][1]
        draw.text((x + cols[4][1] - 16, mid_y), format_money(o["target"]), font=fonts["cell_reg"], fill="#cbd5e1", anchor="rm")
        x += cols[4][1]
        draw.text((x + cols[5][1] - 16, mid_y), format_money(o["achieved"]), font=fonts["cell"], fill="#ffffff", anchor="rm")
        x += cols[5][1]
        draw.text((x + cols[6][1] - 16, mid_y), f"{pct:.1f}%", font=fonts["cell"], fill=pct_color, anchor="rm")

        curr_y += row_h

    # 4. Total Footer Row
    mid_y = curr_y + foot_h // 2
    draw.rectangle([margin_x, curr_y, margin_x + table_w, curr_y + foot_h], fill="#1e293b")
    draw.line([margin_x, curr_y, margin_x + table_w, curr_y], fill="#38bdf8", width=2)

    total_pct = (tot_achieved / tot_target * 100) if tot_target > 0 else 0

    x = margin_x
    draw.text((x + cols[0][1] // 2, mid_y), "-", font=fonts["footer"], fill="#94a3b8", anchor="mm")
    x += cols[0][1]
    draw.text((x + 16, mid_y), "GRAND TOTAL", font=fonts["footer"], fill="#ffffff", anchor="lm")
    x += cols[1][1]
    draw.text((x + 16, mid_y), "ALL TEAMS", font=fonts["footer"], fill="#38bdf8", anchor="lm")
    x += cols[2][1]
    draw.text((x + cols[3][1] - 16, mid_y), str(tot_contracts), font=fonts["footer"], fill="#ffffff", anchor="rm")
    x += cols[3][1]
    draw.text((x + cols[4][1] - 16, mid_y), format_money(tot_target), font=fonts["footer"], fill="#cbd5e1", anchor="rm")
    x += cols[4][1]
    draw.text((x + cols[5][1] - 16, mid_y), format_money(tot_achieved), font=fonts["footer"], fill="#4ade80", anchor="rm")
    x += cols[5][1]
    draw.text((x + cols[6][1] - 16, mid_y), f"{total_pct:.1f}%", font=fonts["footer"], fill="#4ade80", anchor="rm")

    curr_y += foot_h
    draw.rectangle([margin_x, table_top_y, margin_x + table_w, curr_y], outline="#334155", width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
