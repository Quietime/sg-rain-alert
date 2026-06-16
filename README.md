# 🌧️ Singapore Rain Alert

Automated rain alert for Singapore. Checks the 2-hour weather forecast every 30 minutes and sends an email notification when rain is expected.

## Monitored Locations
- **Emery Point** (API area: Kallang)
- **Marina Square** (API area: City)

## Setup

### 1. Create GitHub Repository
Push this project to a new GitHub repository.

### 2. Configure Secrets
Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description | Example |
|--------|-------------|---------|
| `SMTP_SERVER` | SMTP server address | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `465` |
| `SMTP_USER` | Sender email address | `your@gmail.com` |
| `SMTP_PASS` | SMTP password / app password | `xxxx xxxx xxxx xxxx` |

#### SMTP Provider Options

**Gmail (Recommended)**
- Server: `smtp.gmail.com`, Port: `465`
- Need to generate an [App Password](https://myaccount.google.com/apppasswords)

**QQ Mail**
- Server: `smtp.qq.com`, Port: `465`
- Need to enable SMTP and get authorization code in QQ Mail settings

**Outlook**
- Server: `smtp.office365.com`, Port: `587`

### 3. Test
Go to **Actions** tab → **Singapore Rain Alert** → **Run workflow** to test manually.

## Data Source
[data.gov.sg](https://data.gov.sg/datasets/d_67a52f3825caddfd3590e74db4438b8c/view) - NEA 2-Hour Weather Forecast
