import json
import urllib.request
import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

API_URL = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"

LOCATIONS = {
    "Kallang": "Emery Point",
    "City": "Marina Square",
}

RAIN_KEYWORDS = ["rain", "showers", "thundery", "thunder", "drizzle", "storm"]

TO_EMAIL = "2702566686@qq.com"


def fetch_forecast():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "SG-Rain-Alert/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def check_rain(data):
    item = data["items"][0]
    forecasts = item["forecasts"]
    valid_period = item["valid_period"]

    rain_locations = []
    all_checked = []

    for f in forecasts:
        area = f["area"]
        weather = f["forecast"]
        if area in LOCATIONS:
            all_checked.append({"area": area, "name": LOCATIONS[area], "forecast": weather})
            if any(kw in weather.lower() for kw in RAIN_KEYWORDS):
                rain_locations.append({"area": area, "name": LOCATIONS[area], "forecast": weather})

    return rain_locations, all_checked, valid_period


def build_html(rain_locations, valid_period):
    start = valid_period["start"]
    end = valid_period["end"]

    rows = ""
    for loc in rain_locations:
        rows += f"""
        <tr>
            <td style="padding:12px 16px;border-bottom:1px solid #e0e0e0;font-weight:600;">{loc['name']}</td>
            <td style="padding:12px 16px;border-bottom:1px solid #e0e0e0;">{loc['area']}</td>
            <td style="padding:12px 16px;border-bottom:1px solid #e0e0e0;color:#d32f2f;font-weight:600;">{loc['forecast']}</td>
        </tr>"""

    return f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:520px;margin:0 auto;color:#333;">
        <div style="background:linear-gradient(135deg,#1a73e8,#4fc3f7);padding:24px;border-radius:12px 12px 0 0;text-align:center;">
            <h1 style="margin:0;color:#fff;font-size:22px;">&#127783;&#65039; &#26032;&#21152;&#22369;&#19979;&#38632;&#25552;&#37266;</h1>
            <p style="margin:8px 0 0;color:rgba(255,255,255,0.9);font-size:14px;">&#26410;&#26469; 2 &#23567;&#26102;&#22825;&#27668;&#39044;&#35686;</p>
        </div>
        <div style="background:#fff;padding:20px;border:1px solid #e0e0e0;border-top:none;">
            <p style="margin:0 0 12px;font-size:14px;color:#666;">
                &#39044;&#25253;&#26102;&#27573;&#65306;<strong>{start}</strong> &#33267; <strong>{end}</strong>
            </p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                <thead>
                    <tr style="background:#f5f5f5;">
                        <th style="padding:10px 16px;text-align:left;font-size:13px;color:#666;">&#22320;&#28857;</th>
                        <th style="padding:10px 16px;text-align:left;font-size:13px;color:#666;">API &#21306;&#22495;</th>
                        <th style="padding:10px 16px;text-align:left;font-size:13px;color:#666;">&#22825;&#27668;</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        <div style="background:#f9f9f9;padding:14px 20px;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 12px 12px;">
            <p style="margin:0;font-size:12px;color:#999;text-align:center;">
                &#27492;&#37038;&#20214;&#30001; GitHub Actions &#33258;&#21160;&#21457;&#36865;&#65292;&#27599; 30 &#20998;&#38047;&#26816;&#26597;&#19968;&#27425;&#12290;
                <br>&#25968;&#25454;&#26469;&#28304;&#65306;data.gov.sg
            </p>
        </div>
    </div>"""


def send_email(rain_locations, valid_period):
    smtp_server = os.environ["SMTP_SERVER"]
    smtp_port = int(os.environ["SMTP_PORT"])
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]

    html = build_html(rain_locations, valid_period)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🌧️ 新加坡下雨提醒 - {datetime.now().strftime('%H:%M')}"
    msg["From"] = smtp_user
    msg["To"] = TO_EMAIL

    plain = "以下地点未来2小时有雨:\n"
    for loc in rain_locations:
        plain += f"  - {loc['name']} ({loc['area']}): {loc['forecast']}\n"

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
    print(f"[{datetime.now().isoformat()}] Fetching Singapore 2-hour forecast...")
    data = fetch_forecast()
    rain_locations, all_checked, valid_period = check_rain(data)

    print(f"Valid period: {valid_period['start']} ~ {valid_period['end']}")
    for loc in all_checked:
        marker = "🌧️ RAIN" if loc in rain_locations else "✅ OK"
        print(f"  {loc['name']} ({loc['area']}): {loc['forecast']}  [{marker}]")

    if rain_locations:
        names = ", ".join(loc["name"] for loc in rain_locations)
        print(f"\nRain detected at: {names}")
        send_email(rain_locations, valid_period)
        print("Email sent to", TO_EMAIL)
    else:
        print("\nNo rain expected. No email sent.")


if __name__ == "__main__":
    main()
