import streamlit as st
import pandas as pd
import calendar
from datetime import date, datetime, timedelta
import os
import io

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------
st.set_page_config(page_title="Forex PnL Dashboard", page_icon="📈", layout="wide")

DATA_FILE = "trades.csv"
SETTINGS_FILE = "settings.csv"
APP_PASSWORD = "1458"

# ---------------------------------------------------------------------
# PASSWORD GATE
# ---------------------------------------------------------------------
def show_lock_screen():
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at top, #1b2436 0%, #0a0e17 65%);
        }
        [data-testid="stHeader"] { background: transparent; }
        .lock-wrap {
            max-width: 380px;
            margin: 8vh auto 0 auto;
            text-align: center;
            padding: 40px 32px 32px 32px;
            border-radius: 20px;
            background: linear-gradient(145deg, #131a29, #0d1220);
            border: 1px solid #253045;
            box-shadow: 0 0 0 1px rgba(59,130,246,0.08), 0 20px 60px rgba(0,0,0,0.5);
        }
        .lock-icon {
            width: 64px; height: 64px; margin: 0 auto 18px auto;
            border-radius: 50%;
            background: linear-gradient(145deg, #1e2c4a, #0f1626);
            display: flex; align-items: center; justify-content: center;
            font-size: 28px;
            box-shadow: 0 0 24px rgba(59,130,246,0.35), inset 0 0 12px rgba(255,255,255,0.03);
        }
        .lock-title {
            font-size: 22px; font-weight: 700; color: #e6edf3; margin-bottom: 4px;
            letter-spacing: 0.02em;
        }
        .lock-sub {
            font-size: 13px; color: #6f7d94; margin-bottom: 26px;
        }
        div[data-testid="stTextInput"] input {
            text-align: center;
            font-size: 22px;
            letter-spacing: 10px;
            font-weight: 700;
            background: #0a0e17 !important;
            border: 1px solid #2a3550 !important;
            color: #7fd4ff !important;
            border-radius: 10px !important;
            padding: 10px !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59,130,246,0.25) !important;
        }
        div.stButton > button {
            width: 100%;
            background: linear-gradient(145deg, #3b82f6, #2563eb);
            color: white; font-weight: 700; border: none;
            padding: 10px; border-radius: 10px; margin-top: 10px;
            box-shadow: 0 6px 18px rgba(37,99,235,0.35);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="lock-wrap">
            <div class="lock-icon">🔒</div>
            <div class="lock-title">Welcome Ahsan</div>
            <div class="lock-sub">Enter your PIN to access the dashboard</div>
        </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        pin = st.text_input(
            "", type="password", max_chars=4, placeholder="••••",
            label_visibility="collapsed", key="pin_input"
        )
        submit = st.button("Unlock")
        if submit or (pin and len(pin) == 4):
            if pin == APP_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            elif pin:
                st.error("Incorrect PIN")


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    show_lock_screen()
    st.stop()

# ---------------------------------------------------------------------
# STORAGE HELPERS
# ---------------------------------------------------------------------
def load_trades():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, parse_dates=["date"])
        df["date"] = df["date"].dt.date
        return df.sort_values("date").reset_index(drop=True)
    return pd.DataFrame(columns=["date", "pnl", "note"])


def save_trades(df):
    df.to_csv(DATA_FILE, index=False)


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        s = pd.read_csv(SETTINGS_FILE).iloc[0]
        return float(s["starting_capital"]), float(s["target_pct"]), s["target_mode"]
    return 1000.0, 1.0, "Compounding"


def save_settings(starting_capital, target_pct, target_mode):
    pd.DataFrame([{
        "starting_capital": starting_capital,
        "target_pct": target_pct,
        "target_mode": target_mode
    }]).to_csv(SETTINGS_FILE, index=False)


def upsert_trade(df, trade_date, pnl, note):
    df = df[df["date"] != trade_date]
    new_row = pd.DataFrame([{"date": trade_date, "pnl": pnl, "note": note}])
    df = pd.concat([df, new_row], ignore_index=True)
    return df.sort_values("date").reset_index(drop=True)


# ---------------------------------------------------------------------
# LOAD STATE
# ---------------------------------------------------------------------
trades = load_trades()
starting_capital, target_pct, target_mode = load_settings()

# ---------------------------------------------------------------------
# SIDEBAR — SETTINGS
# ---------------------------------------------------------------------
st.sidebar.header("⚙️ Settings")
starting_capital = st.sidebar.number_input(
    "Starting Capital ($)", min_value=0.0, value=starting_capital, step=50.0
)
target_pct = st.sidebar.number_input(
    "Daily Profit Target (%)", min_value=0.0, value=target_pct, step=0.1
)
target_mode = st.sidebar.radio(
    "Target Basis",
    ["Compounding (on current equity)", "Fixed (on starting capital)"],
    index=0 if target_mode.startswith("Compounding") else 1
)
if st.sidebar.button("💾 Save Settings"):
    save_settings(starting_capital, target_pct, target_mode)
    st.sidebar.success("Settings saved")

st.sidebar.divider()
st.sidebar.header("➕ Log a Trade Day")
entry_date = st.sidebar.date_input("Date", value=date.today())
entry_pnl = st.sidebar.number_input("PnL for this day ($)", value=0.0, step=1.0, format="%.2f")
entry_note = st.sidebar.text_input("Note (optional)")
if st.sidebar.button("Save Entry"):
    trades = upsert_trade(trades, entry_date, entry_pnl, entry_note)
    save_trades(trades)
    st.sidebar.success(f"Saved PnL for {entry_date}")

# ---------------------------------------------------------------------
# CALCULATIONS
# ---------------------------------------------------------------------
total_pnl = trades["pnl"].sum() if not trades.empty else 0.0
current_equity = starting_capital + total_pnl

today = date.today()
today_row = trades[trades["date"] == today]
today_pnl = float(today_row["pnl"].sum()) if not today_row.empty else 0.0

# equity as of start of today (excludes today's own pnl)
equity_before_today = current_equity - today_pnl

if target_mode.startswith("Compounding"):
    today_target_amount = equity_before_today * (target_pct / 100)
else:
    today_target_amount = starting_capital * (target_pct / 100)

today_progress = (today_pnl / today_target_amount * 100) if today_target_amount > 0 else 0

# tomorrow's target — projects equity assuming today's actual result stands
equity_after_today = current_equity
if target_mode.startswith("Compounding"):
    tomorrow_target_amount = equity_after_today * (target_pct / 100)
else:
    tomorrow_target_amount = starting_capital * (target_pct / 100)


def week_bounds(d):
    start = d - timedelta(days=d.weekday())  # Monday
    end = start + timedelta(days=6)
    return start, end


def month_bounds(d):
    start = d.replace(day=1)
    last_day = calendar.monthrange(d.year, d.month)[1]
    end = d.replace(day=last_day)
    return start, end


w_start, w_end = week_bounds(today)
m_start, m_end = month_bounds(today)

week_pnl = trades[(trades["date"] >= w_start) & (trades["date"] <= w_end)]["pnl"].sum()
month_pnl = trades[(trades["date"] >= m_start) & (trades["date"] <= m_end)]["pnl"].sum()

# ---------------------------------------------------------------------
# HEADER METRICS
# ---------------------------------------------------------------------
st.title("📈 Forex PnL Dashboard")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's PnL", f"${today_pnl:,.2f}")
c2.metric("This Week", f"${week_pnl:,.2f}")
c3.metric("This Month", f"${month_pnl:,.2f}")
c4.metric("Current Equity", f"${current_equity:,.2f}", f"{total_pnl:+,.2f} total")

st.divider()

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("🎯 Today's Target")
    st.write(f"Target amount: **${today_target_amount:,.2f}** ({target_pct}%)")
    st.progress(min(max(today_progress / 100, 0), 1.0))
    st.caption(f"{today_progress:.1f}% of today's target reached")

with col_b:
    st.subheader("🔮 Tomorrow's Target")
    st.write(f"Projected target amount: **${tomorrow_target_amount:,.2f}** ({target_pct}%)")
    st.caption(
        "Based on compounding equity" if target_mode.startswith("Compounding")
        else "Based on fixed starting capital"
    )

st.divider()

# ---------------------------------------------------------------------
# CALENDAR VIEW
# ---------------------------------------------------------------------
st.subheader("🗓️ Monthly Calendar")

cal_col1, cal_col2 = st.columns([1, 3])
with cal_col1:
    view_year = st.number_input("Year", min_value=2000, max_value=2100, value=today.year, step=1)
    view_month = st.selectbox(
        "Month", list(range(1, 13)), index=today.month - 1,
        format_func=lambda m: calendar.month_name[m]
    )

pnl_by_date = dict(zip(trades["date"], trades["pnl"])) if not trades.empty else {}

cal = calendar.Calendar(firstweekday=0)  # Monday first
month_days = cal.monthdatescalendar(view_year, view_month)

header_cols = st.columns(7)
for i, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
    header_cols[i].markdown(f"**{day_name}**")

for week in month_days:
    row_cols = st.columns(7)
    for i, d in enumerate(week):
        with row_cols[i]:
            in_month = d.month == view_month
            pnl_val = pnl_by_date.get(d)
            if not in_month:
                st.markdown(
                    f"<div style='opacity:0.25;padding:6px;text-align:center'>{d.day}</div>",
                    unsafe_allow_html=True
                )
            elif pnl_val is None:
                st.markdown(
                    f"<div style='padding:6px;text-align:center;border:1px solid #333;border-radius:6px'>{d.day}</div>",
                    unsafe_allow_html=True
                )
            else:
                color = "#1e7d32" if pnl_val >= 0 else "#b71c1c"
                st.markdown(
                    f"<div style='background:{color};padding:6px;text-align:center;"
                    f"border-radius:6px;color:white'><b>{d.day}</b><br>"
                    f"{pnl_val:+,.2f}</div>",
                    unsafe_allow_html=True
                )

st.divider()

# ---------------------------------------------------------------------
# WEEK / MONTH BREAKDOWN TABLE
# ---------------------------------------------------------------------
st.subheader("📊 History")

tab1, tab2, tab3 = st.tabs(["This Week", "This Month", "All Entries"])
with tab1:
    st.dataframe(
        trades[(trades["date"] >= w_start) & (trades["date"] <= w_end)]
        .sort_values("date", ascending=False),
        use_container_width=True, hide_index=True
    )
with tab2:
    st.dataframe(
        trades[(trades["date"] >= m_start) & (trades["date"] <= m_end)]
        .sort_values("date", ascending=False),
        use_container_width=True, hide_index=True
    )
with tab3:
    st.dataframe(trades.sort_values("date", ascending=False), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------
# DOWNLOAD SUMMARY
# ---------------------------------------------------------------------
st.divider()
st.subheader("⬇️ Download Summary")

summary_lines = [
    f"Forex PnL Summary — generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    "-" * 50,
    f"Starting Capital: ${starting_capital:,.2f}",
    f"Current Equity: ${current_equity:,.2f}",
    f"Total PnL: ${total_pnl:,.2f}",
    "",
    f"Today's PnL ({today}): ${today_pnl:,.2f}",
    f"Today's Target: ${today_target_amount:,.2f} ({target_pct}%)",
    f"Tomorrow's Target: ${tomorrow_target_amount:,.2f} ({target_pct}%)",
    "",
    f"This Week PnL ({w_start} to {w_end}): ${week_pnl:,.2f}",
    f"This Month PnL ({m_start} to {m_end}): ${month_pnl:,.2f}",
    "",
    "Full Trade Log:",
]
buf = io.StringIO()
buf.write("\n".join(summary_lines) + "\n")
if not trades.empty:
    trades.sort_values("date").to_csv(buf, index=False)

st.download_button(
    label="Download Summary (.txt + CSV log)",
    data=buf.getvalue(),
    file_name=f"pnl_summary_{today.isoformat()}.txt",
    mime="text/plain"
)

if not trades.empty:
    st.download_button(
        label="Download Raw Trade Log (.csv)",
        data=trades.sort_values("date").to_csv(index=False),
        file_name=f"trades_{today.isoformat()}.csv",
        mime="text/csv"
    )
