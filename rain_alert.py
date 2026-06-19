import json
import urllib.request
import smtplib
import os
import sys
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

FORECAST_URL = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
RAINFALL_URL = "https://api.data.gov.sg/v1/environment/rainfall"

FORECAST_AREAS = {"Kallang": "Emery Point", "City": "Marina Square"}
RAINFALL_STATIONS = {
    "S127": {"name": "Kallang Practice Track", "location": "Emery Point"},
    "S108": {"name": "Marina Gardens Drive", "location": "Marina Square"},
}
RAIN_KEYWORDS = ["rain", "showers", "thundery", "thunder", "drizzle", "storm"]
COOLDOWN_MINUTES = 30
STATE_FILE = "rain_state.json"
TO_EMAIL = "2702566686@qq.com"
SGT = timezone(timedelta(hours=8))


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "SG-Rain-Alert/2.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def check_realtime_rainfall():
    data = fetch_json(RAINFALL_URL)
    readings = data["items"][0]["readings"]
    station_map = {s["device_id"]: s for s in data["metadata"]["stations"]}
    timestamp = data["items"][0]["timestamp"]

    alerts = []
    all_checked = []
    for sid, info in RAINFALL_STATIONS.items():
        reading = next((r for r in readings if r["station_id"] == sid), None)
        value = reading["value"] if reading else 0
        entry = {"station_id": sid, "station_name": info["name"],
                 "location": info["location"], "rainfall_mm": value}
        all_checked.append(entry)
        if value > 0:
            alerts.append(entry)

    return alerts, all_checked, timestamp


def check_forecast():
    data = fetch_json(FORECAST_URL)
    item = data["items"][0]
    valid_period = item["valid_period"]

    alerts = []
    all_checked = []
    for f in item["forecasts"]:
        area = f["area"]
        weather = f["forecast"]
        if area in FORECAST_AREAS:
            entry = {"area": area, "location": FORECAST_AREAS[area], "forecast": weather}
            all_checked.append(entry)
            if any(kw in weather.lower() for kw in RAIN_KEYWORDS):
                alerts.append(entry)

    return alerts, all_checked, valid_period


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_email_ts": 0}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def is_in_cooldown(state):
    last = state.get("last_email_ts", 0)
    elapsed = time.time() - last
    return elapsed < COOLDOWN_MINUTES * 60


def build_html(rainfall_alerts, forecast_alerts, rainfall_ts, valid_period):
    now_sgt = datetime.now(SGT).strftime("%Y-%m-%d %H:%M SGT")

    rainfall_rows = ""
    for a in rainfall_alerts:
        rainfall_rows += f"""
        <tr>
            <td style="padding:10px 14px;border-bottom:1px solid #e0e0e0;font-weight:600;">{a['location']}</td>
            <td style="padding:10px 14px;border-bottom:1px solid #e0e0e0;">{a['station_name']}</td>
            <td style="padding:10px 14px;border-bottom:1px solid #e0e0e0;color:#d32f2f;font-weight:700;">{a['rainfall_mm']} mm</td>
        </tr>"""

    forecast_rows = ""
    for a in forecast_alerts:
        forecast_rows += f"""
        <tr>
            <td style="padding:10px 14px;border-bottom:1px solid #e0e0e0;font-weight:600;">{a['location']}</td>
            <td style="padding:10px 14px;border-bottom:1px solid #e0e0e0;">{a['area']}</td>
            <td style="padding:10px 14px;border-bottom:1px solid #e0e0e0;color:#d32f2f;font-weight:700;">{a['forecast']}</td>
        </tr>"""

    sections = ""
    if rainfall_alerts:
        sections += f"""
        <h2 style="margin:16px 0 8px;font-size:16px;color:#c62828;">&#9748; &#23454;&#26102;&#38477;&#38632;&#26816;&#27979;</h2>
        <p style="margin:0 0 8px;font-size:13px;color:#888;">&#26102;&#38388;&#65306;{rainfall_ts}</p>
        <table style="width:100%;border-collapse:collapse;">
            <thead><tr style="background:#fff3e0;">
                <th style="padding:8px 14px;text-align:left;font-size:12px;color:#666;">&#22320;&#28857;</th>
                <th style="padding:8px 14px;text-align:left;font-size:12px;color:#666;">&#30417;&#27979;&#31449;</th>
                <th style="padding:8px 14px;text-align:left;font-size:12px;color:#666;">&#38632;&#37327; (5min)</th>
            </tr></thead>
            <tbody>{rainfall_rows}</tbody>
        </table>"""

    if forecast_alerts:
        period_str = f"{valid_period['start']} ~ {valid_period['end']}"
        sections += f"""
        <h2 style="margin:16px 0 8px;font-size:16px;color:#1565c0;">&#127783;&#65039; 2&#23567;&#26102;&#22825;&#27668;&#39044;&#25253;</h2>
        <p style="margin:0 0 8px;font-size:13px;color:#888;">&#39044;&#25253;&#26102;&#27573;&#65306;{period_str}</p>
        <table style="width:100%;border-collapse:collapse;">
            <thead><tr style="background:#e3f2fd;">
                <th style="padding:8px 14px;text-align:left;font-size:12px;color:#666;">&#22320;&#28857;</th>
                <th style="padding:8px 14px;text-align:left;font-size:12px;color:#666;">API &#21306;&#22495;</th>
                <th style="padding:8px 14px;text-align:left;font-size:12px;color:#666;">&#22825;&#27668;</th>
            </tr></thead>
            <tbody>{forecast_rows}</tbody>
        </table>"""

    return f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:540px;margin:0 auto;color:#333;">
        <div style="background:linear-gradient(135deg,#d32f2f,#ff7043);padding:22px;border-radius:12px 12px 0 0;text-align:center;">
            <h1 style="margin:0;color:#fff;font-size:22px;">&#127783;&#65039; &#26032;&#21152;&#22369;&#19979;&#38632;&#35686;&#25253;</h1>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.9);font-size:13px;">{now_sgt}</p>
        </div>
        <div style="background:#fff;padding:18px;border:1px solid #e0e0e0;border-top:none;">
            {sections}
        </div>
        <div style="background:#f9f9f9;padding:12px 18px;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 12px 12px;">
            <p style="margin:0;font-size:11px;color:#999;text-align:center;">
                GitHub Actions &#33258;&#21160;&#21457;&#36865; &middot; &#27599;5&#20998;&#38047;&#26816;&#26597; &middot; 30&#20998;&#38047;&#20919;&#21364;&#38450;&#21047;
                <br>&#25968;&#25454;&#26469;&#28304;&#65306;data.gov.sg (NEA)
            </p>
        </div>
    </div>"""


def send_email(rainfall_alerts, forecast_alerts, rainfall_ts, valid_period):
    smtp_server = os.environ["SMTP_SERVER"]
    smtp_port = int(os.environ["SMTP_PORT"])
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]

    html = build_html(rainfall_alerts, forecast_alerts, rainfall_ts, valid_period)

    msg = MIMEMultipart("alternative")
    now_str = datetime.now(SGT).strftime("%H:%M")
    msg["Subject"] = f"\U0001f327️ 新加坡下雨警报 - {now_str}"
    msg["From"] = smtp_user
    msg["To"] = TO_EMAIL

    plain_parts = []
    if rainfall_alerts:
        plain_parts.append("实时降雨检测:")
        for a in rainfall_alerts:
            plain_parts.append(f"  - {a['location']} ({a['station_name']}): {a['rainfall_mm']}mm")
    if forecast_alerts:
        plain_parts.append("2小时天气预报:")
        for a in forecast_alerts:
            plain_parts.append(f"  - {a['location']} ({a['area']}): {a['forecast']}")
    plain = "\n".join(plain_parts)

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    if smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, TO_EMAIL, msg.as_string())
    else:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, TO_EMAIL, msg.as_string())


def main():
    now = datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S SGT")
    print(f"[{now}] Singapore Rain Alert v2.0")
    print("=" * 50)

    print("\n[1/2] Checking real-time rainfall (5-min stations)...")
    rainfall_alerts, rainfall_all, rainfall_ts = check_realtime_rainfall()
    for s in rainfall_all:
        marker = f"\U0001f327️ {s['rainfall_mm']}mm" if s['rainfall_mm'] > 0 else "✅ 0mm"
        print(f"  {s['location']} ({s['station_name']}): {marker}")

    print(f"\n[2/2] Checking 2-hour weather forecast...")
    forecast_alerts, forecast_all, valid_period = check_forecast()
    print(f"  Valid: {valid_period['start']} ~ {valid_period['end']}")
    for f in forecast_all:
        marker = "\U0001f327️ RAIN" if f in forecast_alerts else "✅ OK"
        print(f"  {f['location']} ({f['area']}): {f['forecast']}  [{marker}]")

    has_rain = bool(rainfall_alerts or forecast_alerts)

    if not has_rain:
        print("\n✅ No rain detected or forecast. No email sent.")
        return

    state = load_state()
    if is_in_cooldown(state):
        remaining = COOLDOWN_MINUTES - (time.time() - state["last_email_ts"]) / 60
        print(f"\n⚠️ Rain detected but in cooldown ({remaining:.0f} min remaining). Skipping email.")
        return

    trigger = []
    if rainfall_alerts:
        trigger.append("real-time rainfall")
    if forecast_alerts:
        trigger.append("2h forecast")
    print(f"\n\U0001f4e7 Rain detected via {' + '.join(trigger)}! Sending email...")

    send_email(rainfall_alerts, forecast_alerts, rainfall_ts, valid_period)
    state["last_email_ts"] = time.time()
    save_state(state)
    print(f"Email sent to {TO_EMAIL}")


if __name__ == "__main__":
    main()
