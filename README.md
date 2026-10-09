# YouTube Bulk Channel Subscriber

Automate subscribing to multiple YouTube channels in one go using browser automation. No API keys needed — it uses your existing browser session.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.50+-green?logo=selenium&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

## How It Works

The script launches your **Brave browser** (with your logged-in YouTube session) via Selenium, navigates to each channel's page, and clicks the **Subscribe** button automatically.

**Key features:**
- Reads channel list from a simple text file (`channels.txt`)
- Supports `@handles`, channel names, and full YouTube URLs
- Skips channels you're already subscribed to
- Auto-recovers if the browser window crashes mid-run
- Shows a summary at the end with success/skip/fail counts

## Prerequisites

- **Python 3.8+** — [Download](https://www.python.org/downloads/)
- **Brave Browser** — [Download](https://brave.com/download/)
- **Signed into YouTube** on Brave (the script uses your existing session)

## Installation

1. **Clone the repo:**
   ```
   git clone https://github.com/YOUR_USERNAME/yt-bulk-channel-subscriber.git
   cd yt-bulk-channel-subscriber
   ```

2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

## Usage

### 1. Create your channel list

Copy the example file and add your channels:

```
cp channels.example.txt channels.txt
```

Edit `channels.txt` and add one channel per line:

```
@mkbhd
@Fireship
@TraversyMedia
@NetworkChuck
https://www.youtube.com/@TechWithTim
```

> Lines starting with `#` are comments and blank lines are ignored.

### 2. Close Brave browser

**Important:** Selenium needs exclusive access to the browser profile. Close all Brave windows before running the script.

### 3. Run the script

```
python subscribe.py
```

The script will:
- Show you the list of channels to process
- Wait for you to press Enter
- Open Brave and start subscribing one by one
- Print a summary when done

### Sample Output

```
=======================================================
  YouTube Bulk Subscriber
=======================================================

Channels to process: 5
Browser: Brave

[1/5] @mkbhd
    -> https://www.youtube.com/@mkbhd
    Subscribed!
[2/5] @Fireship
    -> https://www.youtube.com/@Fireship
    Already subscribed - skipped
[3/5] @TraversyMedia
    -> https://www.youtube.com/@TraversyMedia
    Subscribed!

=======================================================
  SUMMARY
=======================================================
  New subscriptions:   2
  Already subscribed:  1
  Failed:              0
=======================================================
```

## Configuration

You can tweak these settings at the top of `subscribe.py`:

| Variable | Default | Description |
|---|---|---|
| `BRAVE_PATH` | `C:\Program Files\BraveSoftware\...` | Path to Brave executable |
| `BRAVE_PROFILE` | `%LOCALAPPDATA%\BraveSoftware\...` | Path to Brave user profile |
| `WAIT_BETWEEN_SUBS` | `3` | Seconds to wait between each subscription |
| `PAGE_LOAD_TIMEOUT` | `15` | Max seconds to wait for page elements |

### Using a different Chromium browser

This script works with any Chromium-based browser (Chrome, Edge, Brave, etc.). Just update `BRAVE_PATH` to point to your browser's executable.

## Project Structure

```
yt-bulk-channel-subscriber/
  subscribe.py          # Main automation script
  channels.example.txt  # Example channel list (template)
  channels.txt          # Your personal channel list (create from example)
  requirements.txt      # Python dependencies
  .gitignore            # Git ignore rules
  README.md             # This file
```

## Troubleshooting

| Issue | Solution |
|---|---|
| **`Failed to subscribe` for all channels** | YouTube may have updated their DOM. Open an issue with the error details. |
| **`NoSuchWindowException`** | Make sure Brave is fully closed before running. The script will auto-recover if this happens mid-run. |
| **Wrong browser profile** | Check that `BRAVE_PROFILE` points to the correct user data directory where you're signed into YouTube. |
| **Script subscribes to wrong channels** | This shouldn't happen — the script targets only the header subscribe button. If it does, please open an issue. |

## Disclaimer

This tool is for personal/educational use. Respect YouTube's [Terms of Service](https://www.youtube.com/t/terms). Use responsibly and don't abuse it for spam or botting.

## License

MIT License — see [LICENSE](LICENSE) for details.
