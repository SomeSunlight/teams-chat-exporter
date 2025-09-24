import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os

# --- CONFIGURATION ---
# IMPORTANT: You must fill in this URL.
# Go to your chat in Teams, copy the URL from your browser's address bar, and paste it here.
TEAMS_CHAT_URL = "" 

# --- SCRIPT SETTINGS ---
# Directory to store the persistent browser session data (cookies, etc.)
USER_DATA_DIR = os.path.join(os.getcwd(), "playwright_user_data")
# Output file for the exported chat
OUTPUT_FILE = "chat_export.html"
# Set to True to run the browser in the background (not recommended for first run)
HEADLESS = False
# Time in milliseconds to wait between scroll actions
SCROLL_DELAY_MS = 3000
# How many times to try scrolling without finding new messages before stopping
MAX_ATTEMPTS_WITHOUT_CHANGE = 3

# --- SELECTORS ---
# These are the "addresses" of elements on the page. They might change with Teams updates.
# The main container that has the scrollbar for the chat pane.
SCROLL_CONTAINER_SELECTOR = '[data-tid="message-pane-list-viewport"]'
# A selector that identifies a single message container.
MESSAGE_SELECTOR = 'div[data-testid="message-wrapper"]'
# A selector within a message to find its unique ID.
MESSAGE_ID_SELECTOR = '[data-mid]'
# A selector within a message to find the sender's name.
SENDER_SELECTOR = '[data-tid="message-author-name"]'
# A selector within a message to find the timestamp.
TIMESTAMP_SELECTOR = 'time'
# A selector within a message to find the content block.
CONTENT_SELECTOR = '[id^="content-"]'


async def main():
    """
    Main function to launch the browser, handle login, scroll the chat,
    and export the content.
    """
    if not TEAMS_CHAT_URL:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ERROR: Please edit src/main.py and set TEAMS_CHAT_URL.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return

    async with async_playwright() as p:
        print(f"--- Starting Browser ---")
        print(f"Session data will be stored in: {USER_DATA_DIR}")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=HEADLESS,
            args=["--start-maximized"],
            no_viewport=True,
        )
        page = await browser_context.new_page()
        
        print(f"Navigating to Teams chat URL...")
        await page.goto(TEAMS_CHAT_URL)

        # --- Handle Login ---
        try:
            # Wait for the main scroll container to appear, which indicates we are logged in.
            print("Checking for active login session...")
            await page.wait_for_selector(SCROLL_CONTAINER_SELECTOR, timeout=15000)
            print("Login session is active. Proceeding...")
        except TimeoutError:
            print("----------------------------------------------------------------")
            print("--- ACTION REQUIRED: Login session has expired or is invalid ---")
            print("Please log in to Microsoft Teams in the browser window.")
            print("The script will wait indefinitely until you have logged in.")
            print("----------------------------------------------------------------")
            # Wait forever until the user logs in and the chat pane is visible.
            await page.wait_for_selector(SCROLL_CONTAINER_SELECTOR, timeout=0)
            print("Login successful. Resuming script...")

        # --- Automated Scrolling & Data Collection ---
        print("\n--- Starting Chat History Loading ---")
        scroll_container = page.locator(SCROLL_CONTAINER_SELECTOR)
        collected_messages = {}
        last_message_count = -1
        attempts = 0

        while True:
            # Collect all currently visible messages
            visible_messages = await page.query_selector_all(MESSAGE_SELECTOR)
            for message_element in visible_messages:
                try:
                    message_id_element = await message_element.query_selector(MESSAGE_ID_SELECTOR)
                    if message_id_element:
                        message_id = await message_id_element.get_attribute('data-mid')
                        if message_id and message_id not in collected_messages:
                            sender = await message_element.query_selector(SENDER_SELECTOR)
                            timestamp = await message_element.query_selector(TIMESTAMP_SELECTOR)
                            content = await message_element.query_selector(CONTENT_SELECTOR)
                            
                            collected_messages[message_id] = {
                                'sender': await sender.text_content() if sender else 'Unknown Sender',
                                'timestamp': await timestamp.get_attribute('title') if timestamp else 'Unknown Time',
                                'content_html': await content.inner_html() if content else '[Empty Message]',
                                'mid': message_id
                            }
                except Exception as e:
                    print(f"Warning: Could not process a message. Error: {e}")

            current_message_count = len(collected_messages)
            print(f"Collected {current_message_count} unique messages so far...")

            if current_message_count == last_message_count:
                attempts += 1
                print(f"Message count is stable. Attempt {attempts} of {MAX_ATTEMPTS_WITHOUT_CHANGE}.")
                if attempts >= MAX_ATTEMPTS_WITHOUT_CHANGE:
                    print("Message count has been stable for several attempts. Assuming chat start has been reached.")
                    break
            else:
                attempts = 0  # Reset counter if we found new messages

            last_message_count = current_message_count

            # Perform the scroll action
            await scroll_container.focus()
            await scroll_container.press('PageUp')
            await page.wait_for_timeout(SCROLL_DELAY_MS)

        # --- HTML Export ---
        print("\n--- Exporting to HTML ---")
        if not collected_messages:
            print("No messages were collected. Exiting.")
            await browser_context.close()
            return
            
        # Sort messages by their ID (which is chronological)
        sorted_messages = sorted(collected_messages.values(), key=lambda m: m['mid'])
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Teams Chat Export</title>
            <style>
                body {{ font-family: "Segoe UI", sans-serif; line-height: 1.6; padding: 20px; max-width: 900px; margin: 0 auto; }}
                .message-container {{ border-bottom: 1px solid #eee; padding: 12px 0; }}
                .header {{ display: flex; align-items: baseline; margin-bottom: 5px; }}
                .sender {{ font-weight: bold; margin-right: 10px; }}
                .timestamp {{ color: #666; font-size: 0.85em; }}
                .content {{ word-wrap: break-word; }}
                img {{ max-width: 500px; height: auto; border-radius: 4px; }}
                a {{ color: #0066cc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>Teams Chat Export</h1>
            <p>Exported on {asyncio.get_event_loop().run_in_executor(None, lambda: __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))} ({len(sorted_messages)} messages)</p>
            <hr>
        """

        for message in sorted_messages:
            # Basic escaping for sender and timestamp to prevent HTML injection
            sender_escaped = message['sender'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            timestamp_escaped = message['timestamp'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            html_content += f"""
            <div class="message-container">
                <div class="header">
                    <p class="sender">{sender_escaped}</p>
                    <p class="timestamp">({timestamp_escaped})</p>
                </div>
                <div class="content">{message['content_html']}</div>
            </div>
            """
        
        html_content += "</body></html>"

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"--------------------------------------------------")
        print(f"--- SUCCESS! ---")
        print(f"Exported {len(sorted_messages)} messages to '{os.path.abspath(OUTPUT_FILE)}'")
        print(f"--------------------------------------------------")

        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(main())