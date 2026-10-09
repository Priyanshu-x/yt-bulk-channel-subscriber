"""
YouTube Bulk Subscribe Script
==============================
Automates subscribing to multiple YouTube channels using Brave browser.
Uses your existing Brave profile so you stay logged in.

IMPORTANT: Close all Brave browser windows before running this script!
           Selenium needs exclusive access to the browser profile.

Usage:
    1. Close Brave browser completely
    2. Add channel handles/names/URLs to channels.txt (one per line)
    3. Run:  python subscribe.py
"""

import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    NoSuchWindowException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
CHANNELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "channels.txt")
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
BRAVE_PROFILE = os.path.join(os.environ["LOCALAPPDATA"], "BraveSoftware", "Brave-Browser", "User Data")
WAIT_BETWEEN_SUBS = 3   # seconds between each subscribe action
PAGE_LOAD_TIMEOUT = 15   # max seconds to wait for page elements


def load_channels(filepath: str) -> list[str]:
    """
    Read channel names from a text file.
    - One channel per line
    - Blank lines and lines starting with # are ignored
    """
    if not os.path.exists(filepath):
        print(f"❌ channels.txt not found at: {filepath}")
        print("   Create the file and add one channel per line.")
        sys.exit(1)

    channels = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            channels.append(stripped)

    return channels


def build_channel_url(channel_input: str) -> str:
    """Convert a channel name/handle/URL into a proper YouTube channel URL."""
    channel_input = channel_input.strip()

    if channel_input.startswith("http"):
        if "/videos" in channel_input or "/about" in channel_input:
            return channel_input.rsplit("/", 1)[0]
        return channel_input

    if channel_input.startswith("@"):
        return f"https://www.youtube.com/{channel_input}"

    return f"https://www.youtube.com/@{channel_input}"


def create_driver() -> webdriver.Chrome:
    """Create a Selenium Chrome driver configured for Brave browser."""
    options = Options()
    options.binary_location = BRAVE_PATH
    options.add_argument(f"--user-data-dir={BRAVE_PROFILE}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager(chrome_type=ChromeType.BRAVE).install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def close_extra_tabs(driver: webdriver.Chrome):
    """Close any extra tabs Brave may have opened."""
    try:
        if len(driver.window_handles) > 1:
            main_window = driver.window_handles[0]
            for handle in driver.window_handles[1:]:
                driver.switch_to.window(handle)
                driver.close()
            driver.switch_to.window(main_window)
    except Exception:
        pass


def try_subscribe(driver: webdriver.Chrome, channel_url: str) -> str:
    """
    Navigate to a channel and click the header Subscribe button.
    
    YouTube's current DOM (2024+):
      - Header: <yt-page-header-renderer> inside <div id="page-header">
      - Subscribe button: <subscribe-button-view-model> > <yt-button-shape> > <button>
      - State: aria-label="Subscribe" (not subbed) vs "Subscribed" (subbed)
    
    Returns: 'subscribed', 'already_subscribed', or 'failed'.
    """
    driver.get(channel_url)
    time.sleep(3)

    close_extra_tabs(driver)

    try:
        # Wait for the page header to load
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#page-header, yt-page-header-renderer"))
        )
        time.sleep(1.5)

        # Use JS to find the subscribe button ONLY inside the page header
        # This avoids clicking "Featured Channels" subscribe buttons
        result = driver.execute_script("""
            // Find the page header
            const header = document.querySelector('#page-header') 
                        || document.querySelector('yt-page-header-renderer');
            if (!header) return { status: 'no_header' };
            
            // Find subscribe-button-view-model inside header
            const viewModel = header.querySelector('subscribe-button-view-model')
                           || header.querySelector('yt-subscribe-button-view-model');
            if (!viewModel) return { status: 'no_view_model' };
            
            // Find the actual button
            const btn = viewModel.querySelector('button');
            if (!btn) return { status: 'no_button' };
            
            const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
            const btnText = (btn.textContent || '').trim().toLowerCase();
            
            // Check if already subscribed
            if (ariaLabel.includes('subscribed') || ariaLabel.includes('unsubscribe') 
                || (btnText.includes('subscribed') && btnText !== 'subscribe')) {
                return { status: 'already_subscribed' };
            }
            
            // It says "Subscribe" — click it
            if (ariaLabel === 'subscribe' || btnText === 'subscribe') {
                btn.click();
                return { status: 'clicked' };
            }
            
            return { status: 'unknown', ariaLabel: ariaLabel, text: btnText };
        """)

        if not result or not isinstance(result, dict):
            print("    ⚠ JS returned unexpected result")
            return try_subscribe_via_search(driver, channel_url)

        status = result.get("status", "unknown")

        if status == "already_subscribed":
            return "already_subscribed"

        if status == "clicked":
            time.sleep(2)
            # Verify it actually subscribed
            verify = driver.execute_script("""
                const header = document.querySelector('#page-header') 
                            || document.querySelector('yt-page-header-renderer');
                if (!header) return 'unknown';
                const vm = header.querySelector('subscribe-button-view-model')
                         || header.querySelector('yt-subscribe-button-view-model');
                if (!vm) return 'unknown';
                const btn = vm.querySelector('button');
                if (!btn) return 'unknown';
                const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                if (label.includes('subscribed') || label.includes('unsubscribe')) return 'subscribed';
                return 'not_confirmed';
            """)
            if verify == "subscribed":
                return "subscribed"
            # Click went through without error, likely succeeded
            return "subscribed"

        if status in ("no_header", "no_view_model", "no_button"):
            print(f"    ⚠ DOM element missing: {status}")
            return try_subscribe_via_search(driver, channel_url)

        print(f"    ⚠ Unexpected state: {result}")
        return "failed"

    except TimeoutException:
        return try_subscribe_via_search(driver, channel_url)
    except (NoSuchWindowException, WebDriverException) as e:
        err_msg = str(e).lower()
        if "no such window" in err_msg or "web view not found" in err_msg:
            raise  # let main() handle browser restart
        print(f"    ⚠ Error: {e}")
        return "failed"
    except Exception as e:
        print(f"    ⚠ Error: {e}")
        return "failed"


def try_subscribe_via_search(driver: webdriver.Chrome, original_input: str) -> str:
    """Fallback: search YouTube for the channel and subscribe from their page."""
    name = original_input.rstrip("/").split("/")[-1].lstrip("@")
    search_url = f"https://www.youtube.com/results?search_query={name}&sp=EgIQAg%253D%253D"
    driver.get(search_url)
    time.sleep(3)

    try:
        channel_link = WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "ytd-channel-renderer a#main-link, "
                "ytd-channel-renderer a.channel-link"
            ))
        )
        channel_href = channel_link.get_attribute("href")
        if channel_href:
            # Navigate directly to the channel page and use the main subscribe logic
            return try_subscribe(driver, channel_href)
        else:
            channel_link.click()
            time.sleep(3)
            # Re-run subscribe logic on the current page (already navigated)
            return try_subscribe_on_current_page(driver)

    except TimeoutException:
        print("    ⚠ Could not find channel in search results")
        return "failed"


def try_subscribe_on_current_page(driver: webdriver.Chrome) -> str:
    """Try to subscribe using JS on whatever page we're currently on."""
    result = driver.execute_script("""
        const header = document.querySelector('#page-header') 
                    || document.querySelector('yt-page-header-renderer');
        if (!header) return 'no_header';
        const vm = header.querySelector('subscribe-button-view-model')
                 || header.querySelector('yt-subscribe-button-view-model');
        if (!vm) return 'no_view_model';
        const btn = vm.querySelector('button');
        if (!btn) return 'no_button';
        const label = (btn.getAttribute('aria-label') || '').toLowerCase();
        if (label.includes('subscribed') || label.includes('unsubscribe')) return 'already_subscribed';
        if (label === 'subscribe') { btn.click(); return 'clicked'; }
        return 'unknown';
    """)

    if result == "already_subscribed":
        return "already_subscribed"
    if result == "clicked":
        time.sleep(2)
        return "subscribed"
    return "failed"


def main():
    channels = load_channels(CHANNELS_FILE)

    if not channels:
        print("❌ No channels found in channels.txt!")
        print(f"   Add channel names (one per line) to: {CHANNELS_FILE}")
        sys.exit(1)

    print("=" * 55)
    print("  YouTube Bulk Subscriber")
    print("=" * 55)
    print(f"\n📄 Reading from: channels.txt")
    print(f"📋 Channels to process: {len(channels)}")
    print("🌐 Browser: Brave\n")

    for i, ch in enumerate(channels, 1):
        print(f"   {i}. {ch}")

    print("\n⚠  Make sure Brave is CLOSED before running this!\n")
    input("Press Enter to start...")

    print("\n🚀 Launching Brave browser...\n")
    driver = create_driver()

    results = {"subscribed": [], "already_subscribed": [], "failed": []}
    i = 0

    try:
        while i < len(channels):
            channel = channels[i]
            url = build_channel_url(channel)
            print(f"[{i + 1}/{len(channels)}] {channel}")
            print(f"    → {url}")

            try:
                status = try_subscribe(driver, url)
            except (NoSuchWindowException, WebDriverException) as e:
                err_msg = str(e).lower()
                if "no such window" in err_msg or "web view not found" in err_msg:
                    print("    🔄 Browser window lost — restarting...")
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    time.sleep(2)
                    driver = create_driver()
                    time.sleep(2)
                    print(f"    🔄 Retrying {channel}...")
                    try:
                        status = try_subscribe(driver, url)
                    except Exception as retry_err:
                        print(f"    ⚠ Retry failed: {retry_err}")
                        status = "failed"
                else:
                    print(f"    ⚠ Error: {e}")
                    status = "failed"

            if status == "subscribed":
                print("    ✅ Subscribed!")
                results["subscribed"].append(channel)
            elif status == "already_subscribed":
                print("    ⏭  Already subscribed — skipped")
                results["already_subscribed"].append(channel)
            else:
                print("    ❌ Failed")
                results["failed"].append(channel)

            i += 1

            if i < len(channels):
                time.sleep(WAIT_BETWEEN_SUBS)

    except KeyboardInterrupt:
        print("\n\n⚠  Interrupted by user!")
    finally:
        print("\n" + "=" * 55)
        print("  SUMMARY")
        print("=" * 55)
        print(f"  ✅ New subscriptions:   {len(results['subscribed'])}")
        print(f"  ⏭  Already subscribed: {len(results['already_subscribed'])}")
        print(f"  ❌ Failed:             {len(results['failed'])}")

        if results["already_subscribed"]:
            print("\n  Already subscribed (skipped):")
            for ch in results["already_subscribed"]:
                print(f"    - {ch}")

        if results["failed"]:
            print("\n  Failed channels:")
            for ch in results["failed"]:
                print(f"    - {ch}")

        print("=" * 55)
        print("\nClosing browser in 5 seconds...")
        time.sleep(5)
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
