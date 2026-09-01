# Singapore Rain Alert

Cloud-based rain alerts for two Singapore locations. GitHub Actions checks every five minutes and sends an email only when rain is detected or forecast.

## Monitored locations

| User location | NEA forecast area | Nearby rainfall station |
|---|---|---|
| Orchid Apt 42B / Sixth Avenue MRT (DT7) | Bukit Timah | S905 |
| Marina Square | City | S108 Marina Gardens Drive |

## Alert logic

- Checks the NEA five-minute rainfall readings and two-hour forecast.
- Sends an email if either selected rainfall station reports more than `0 mm`, or either forecast area contains a rain-related condition.
- Uses a 30-minute cooldown to avoid repeated emails during the same rain event.
- Retries temporary weather API failures up to three times.
- Runs entirely in GitHub Actions; the user's computer does not need to stay on.

## GitHub configuration

Add these repository secrets under **Settings -> Secrets and variables -> Actions**:

| Secret | Description |
|---|---|
| `SMTP_SERVER` | SMTP server hostname, such as `smtp.qq.com` |
| `SMTP_PORT` | SMTP port, normally `465` for SSL |
| `SMTP_USER` | Sender email address |
| `SMTP_PASS` | SMTP authorization code or app password |

Never commit SMTP credentials to the repository.

## Manual test

Open **Actions -> Singapore Rain Alert -> Run workflow**. A successful run without rain finishes silently; when rain is present, it sends one alert email subject to the cooldown.

## Data sources

- [NEA five-minute rainfall readings](https://data.gov.sg/collections/1459/view)
- [NEA two-hour weather forecast](https://data.gov.sg/collections/1456/view)
