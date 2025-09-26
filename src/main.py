import asyncio
import configparser
import argparse
import sys
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError, Page, Frame, ElementHandle, Locator, \
    Error as PlaywrightError
import datetime
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import base64

# --- PATH DEFINITIONS ---
PROJECT_ROOT = Path(__file__).parent.parent
USER_DATA_DIR = PROJECT_ROOT / "playwright_user_data"
# Default output dir, can be overridden by CLI args
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "saved_chats"
CONFIG_DIR = PROJECT_ROOT / "config"
HEADLESS = False

# --- JAVASCRIPT FOR INJECTION ---
INJECT_JS = """
(function() {
    const buttonId = 'teams-exporter-button';
    if (document.getElementById(buttonId)) { return 'already_injected'; }
    const button = document.createElement('button');
    button.id = buttonId;
    button.textContent = 'Export This Chat';
    Object.assign(button.style, {
        position: 'fixed', top: '10px', right: '10px', zIndex: '9999',
        padding: '10px 20px', backgroundColor: '#4A90E2', color: 'white',
        border: 'none', borderRadius: '5px', cursor: 'pointer',
        fontSize: '14px', boxShadow: '0 2px 5px rgba(0,0,0,0.2)', transition: 'background-color 0.3s'
    });
    button.onclick = () => {
        button.textContent = 'Exporting, please wait...';
        button.style.backgroundColor = '#777';
        button.disabled = true;
    };
    document.body.appendChild(button);
    return 'injected';
})();
"""

FETCH_IMAGE_AS_BASE64_JS = """
async (url) => {
    if (url.startsWith('data:image')) { return { success: url }; }
    try {
        const response = await fetch(url, {credentials: 'include'});
        if (!response.ok) { return { error: `Failed to fetch: ${response.status} ${response.statusText}` }; }
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.startsWith('image/')) { return { error: `URL is not an image. Content-Type: ${contentType}` }; }
        const blob = await response.blob();
        const reader = new FileReader();
        return new Promise((resolve) => {
            reader.onloadend = () => resolve({ success: reader.result });
            reader.onerror = (err) => resolve({ error: `FileReader error: ${err}` });
            reader.readAsDataURL(blob);
        });
    } catch (error) { return { error: `JavaScript fetch error: ${error.message}` }; }
}
"""


class Config:
    def __init__(self, data):
        self.app_shell_selector = data.get('app_shell_selector')
        self.scroll_container_selector = data.get('scroll_container_selector')
        self.chat_title_selector = data.get('chat_title_selector')
        self.message_selector = data.get('message_selector')
        self.force_screenshot_selector = data.get('force_screenshot_selector')
        self.message_id_selector = data.get('message_id_selector')
        self.sender_selector = data.get('sender_selector')
        self.timestamp_selector = data.get('timestamp_selector')
        self.content_selector = data.get('content_selector')
        self.avatar_image_selector = data.get('avatar_image_selector')
        self.reaction_summary_selector = data.get('reaction_summary_selector')
        self.reaction_pill_selector = data.get('reaction_pill_selector')
        # Tooltip logic removed for stability in v1.0
        # self.reaction_tooltip_selector = data.get('reaction_tooltip_selector')
        # self.reaction_user_list_selector = data.get('reaction_user_list_selector')
        # self.reaction_user_list_item_selector = data.get('reaction_user_list_item_selector')
        # self.reaction_user_name_selector = data.get('reaction_user_name_selector')
        self.scroll_delay_ms = 3000
        self.max_attempts_without_change = 3
        # Load screenshot substrings
        force_screenshot_str = data.get('force_screenshot_url_substrings', '')
        self.force_screenshot_substrings = [s.strip() for s in force_screenshot_str.split(',') if s.strip()]


def sanitize_filename(name: str) -> str:
    if not name: return "Untitled_Chat"
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.replace(' ', '_')
    return name


async def find_and_load_config(search_scope, silent: bool = False):
    if not CONFIG_DIR.is_dir(): return None
    config_files = sorted(CONFIG_DIR.glob('*.ini'), reverse=True)
    if not config_files: return None
    for config_file in config_files:
        try:
            parser = configparser.ConfigParser()
            parser.read(config_file)
            key_selector = parser['Selectors'].get('app_shell_selector')
            if not key_selector: continue

            try:
                await search_scope.wait_for_selector(key_selector, timeout=500, state='attached')
            except Exception:
                continue

            if not silent: print(f"Success! Using configuration: {config_file.name}", flush=True)
            return Config(parser['Selectors'])
        except Exception:
            continue
    return None


async def capture_element_as_image(element: [ElementHandle, Locator], folder_path: Path,
                                   base_filename: str) -> str | None:
    try:
        image_bytes = await element.screenshot(type='png')
        image_filename = f"{base_filename}.png"
        with open(folder_path / image_filename, 'wb') as f:
            f.write(image_bytes)
        return f"images/{image_filename}"
    except Exception as e:
        print(f"    - Warning: Could not take screenshot for {base_filename}. Error: {e}", flush=True)
        return None


async def run_export_process(scope: [Page, Frame], config: Config, page: Page, output_root: Path):
    print("\n--- Export Triggered! Starting Chat History Loading ---", flush=True)

    try:
        chat_title_element = await scope.locator(config.chat_title_selector).first.text_content()
        chat_title_sanitized = sanitize_filename(chat_title_element)
    except Exception:
        chat_title_sanitized = "Teams_Chat_Export"

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    export_folder_name = f"{chat_title_sanitized}_{timestamp}"

    # Use the configured output directory
    export_path = output_root / export_folder_name
    images_path = export_path / "images"
    images_path.mkdir(parents=True, exist_ok=True)

    print(f"Export will be saved in: {export_path}", flush=True)

    scroll_container = scope.locator(config.scroll_container_selector)
    collected_messages = {}
    last_message_count = -1
    attempts = 0
    image_counter = 0
    downloaded_avatars = {}

    while True:
        visible_messages = await scope.query_selector_all(config.message_selector)
        for message_handle in visible_messages:
            try:
                msg_id_element = await message_handle.query_selector(config.message_id_selector)
                if msg_id_element:
                    msg_id = await msg_id_element.get_attribute('data-mid')
                    if msg_id and msg_id not in collected_messages:
                        sender_element = await message_handle.query_selector(config.sender_selector)
                        timestamp_element = await message_handle.query_selector(config.timestamp_selector)
                        content_element = await message_handle.query_selector(config.content_selector)
                        avatar_img_element = await message_handle.query_selector(config.avatar_image_selector)

                        page_url = scope.url

                        content_html = await content_element.inner_html() if content_element else ''
                        soup = BeautifulSoup(content_html, 'html.parser')

                        if config.force_screenshot_selector:
                            for element_to_screenshot in soup.select(config.force_screenshot_selector):
                                try:
                                    unique_id = element_to_screenshot.get('data-tid') or element_to_screenshot.get('id')
                                    if not unique_id: continue
                                    live_element_handle = await content_element.query_selector(
                                        f'[data-tid="{unique_id}"]')
                                    if not live_element_handle: continue

                                    # print(f"    -> Capturing special element as screenshot: {unique_id}", flush=True)
                                    image_counter += 1
                                    local_src = await capture_element_as_image(live_element_handle, images_path,
                                                                               f"image_{image_counter}")
                                    if local_src:
                                        new_img_tag = soup.new_tag("img", src=local_src,
                                                                   alt=element_to_screenshot.get('title', 'emoticon'))
                                        element_to_screenshot.replace_with(new_img_tag)
                                except Exception as ss_e:
                                    print(f"    - Warning: Could not process forced screenshot element. Error: {ss_e}",
                                          flush=True)

                        for img in soup.find_all('img'):
                            src = img.get('src')
                            if not src or not src.startswith(('http://', 'https://')): continue

                            force_screenshot = any(sub in src for sub in config.force_screenshot_substrings)

                            if force_screenshot:
                                img_element_handle = await content_element.query_selector(f'img[src="{src}"]')
                                if img_element_handle:
                                    image_counter += 1
                                    local_src = await capture_element_as_image(img_element_handle, images_path,
                                                                               f"image_{image_counter}")
                                    if local_src:
                                        img['src'] = local_src
                                continue

                            result = await scope.evaluate(FETCH_IMAGE_AS_BASE64_JS, src)
                            if result and result.get('success'):
                                data_url = result['success']
                                header, encoded = data_url.split(",", 1)
                                image_bytes = base64.b64decode(encoded)
                                content_type = header.split(';')[0].split(':')[1]
                                extension = content_type.split('/')[-1]
                                image_counter += 1
                                image_filename = f"image_{image_counter}.{extension}"
                                with open(images_path / image_filename, 'wb') as f:
                                    f.write(image_bytes)
                                img['src'] = f"images/{image_filename}"
                            else:
                                print(f"    - Base64 fetch failed for {src[:60]}. Fallback to screenshot...",
                                      flush=True)
                                img_element_handle = await content_element.query_selector(f'img[src="{src}"]')
                                if img_element_handle:
                                    image_counter += 1
                                    local_src = await capture_element_as_image(img_element_handle, images_path,
                                                                               f"image_{image_counter}")
                                    if local_src:
                                        img['src'] = local_src

                        for a in soup.find_all('a'):
                            href = a.get('href')
                            if href and href.startswith('/'): a['href'] = urljoin(page_url, href)

                        processed_html = str(soup)

                        avatar_local_src = None
                        if avatar_img_element:
                            avatar_url = await avatar_img_element.get_attribute('src')
                            if avatar_url and avatar_url in downloaded_avatars:
                                avatar_local_src = downloaded_avatars[avatar_url]
                            elif avatar_url and avatar_url.startswith(('http://', 'https://')):
                                result = await scope.evaluate(FETCH_IMAGE_AS_BASE64_JS, avatar_url)
                                if result and result.get('success'):
                                    data_url = result['success']
                                    header, encoded = data_url.split(",", 1)
                                    image_bytes = base64.b64decode(encoded)
                                    content_type = header.split(';')[0].split(':')[1]
                                    extension = content_type.split('/')[-1]
                                    sender_name = await sender_element.text_content() if sender_element else "unknown_sender"
                                    avatar_filename = f"avatar_{sanitize_filename(sender_name)}.{extension}"
                                    with open(images_path / avatar_filename, 'wb') as f:
                                        f.write(image_bytes)
                                    avatar_local_src = f"images/{avatar_filename}"
                                    downloaded_avatars[avatar_url] = avatar_local_src
                                else:
                                    # print(f"    - Base64 fetch failed for avatar {avatar_url[:60]}. Fallback to screenshot...", flush=True)
                                    sender_name = await sender_element.text_content() if sender_element else "unknown_sender"
                                    local_src = await capture_element_as_image(avatar_img_element, images_path,
                                                                               f"avatar_{sanitize_filename(sender_name)}")
                                    if local_src:
                                        avatar_local_src = local_src
                                        downloaded_avatars[avatar_url] = avatar_local_src

                        reactions_html = ""
                        if config.reaction_summary_selector:
                            # Simplified logic: Just capture the reaction pills as images.
                            # The detailed hover logic has been removed for stability.
                            reaction_summary_locator = scope.locator(
                                f'div[data-mid="{msg_id}"] >> {config.reaction_summary_selector}')
                            if await reaction_summary_locator.count() > 0:
                                reactions_soup = BeautifulSoup("<div></div>", 'html.parser').div
                                reactions_soup['style'] = "margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px;"

                                pill_locators = reaction_summary_locator.locator(config.reaction_pill_selector)

                                for i in range(await pill_locators.count()):
                                    pill_locator = pill_locators.nth(i)
                                    try:
                                        tooltip_text = await pill_locator.text_content()

                                        image_counter += 1
                                        local_src = await capture_element_as_image(pill_locator, images_path,
                                                                                   f"reaction_{image_counter}")
                                        if local_src:
                                            # We use the text content as title, providing basic info on hover
                                            safe_title = tooltip_text.replace('"', '&quot;')
                                            new_reaction_img = BeautifulSoup(
                                                f'<img src="{local_src}" alt="Reaction" title="{safe_title}" />',
                                                'html.parser').img
                                            new_reaction_img[
                                                'style'] = "height: 24px; width: auto; vertical-align: middle;"
                                            reactions_soup.append(new_reaction_img)
                                    except Exception as reaction_e:
                                        print(f"    - Warning: Could not process a reaction. Error: {reaction_e}",
                                              flush=True)

                                reactions_html = str(reactions_soup)

                        final_content_html = processed_html + reactions_html

                        collected_messages[msg_id] = {
                            'sender': await sender_element.text_content() if sender_element else 'Unknown Sender',
                            'timestamp': await timestamp_element.get_attribute(
                                'title') if timestamp_element else 'Unknown Time',
                            'content_html': final_content_html,
                            'avatar_src': avatar_local_src,
                            'mid': msg_id
                        }
            except Exception as e:
                print(f"Warning: Could not process a message. Error: {e}", flush=True)

        current_message_count = len(collected_messages)
        print(f"Collected {current_message_count} unique messages so far...", flush=True)
        if current_message_count == last_message_count:
            attempts += 1
            if attempts >= config.max_attempts_without_change:
                print("Assuming chat start has been reached.", flush=True)
                break
        else:
            attempts = 0
        last_message_count = current_message_count
        await scroll_container.focus()
        await scroll_container.press('PageUp')
        await asyncio.sleep(config.scroll_delay_ms / 1000)

    print("\n--- Exporting to HTML ---", flush=True)
    if not collected_messages:
        print("No messages were collected.", flush=True)
        await scope.evaluate("document.getElementById('teams-exporter-button')?.remove();")
        return

    output_filepath = export_path / "index.html"
    sorted_messages = sorted(collected_messages.values(), key=lambda m: m['mid'])

    html_parts = [
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Teams Chat Export</title><style>',
        'body{font-family:"Segoe UI",sans-serif;line-height:1.6;padding:20px;max-width:900px;margin:0 auto}',
        '.message-container{display:flex;align-items:flex-start;border-bottom:1px solid #eee;padding:12px 0}',
        '.avatar{width:36px;height:36px;border-radius:50%;margin-right:12px;flex-shrink:0;object-fit:cover;}',
        '.message-body{display:flex;flex-direction:column;width:100%}',
        '.header{display:flex;align-items:baseline;margin-bottom:5px}',
        '.sender{font-weight:bold;margin-right:10px}',
        '.timestamp{color:#666;font-size:.85em}',
        '.content{word-wrap:break-word}',
        '.content img{max-width:500px;height:auto;border-radius:4px}',
        'a{color:#0066cc;text-decoration:none} a:hover{text-decoration:underline}',
        '.emoticon-sprite { height: 20px; width: 20px; object-fit: cover; object-position: top; }',
        '</style></head><body>',
        f'<h1>Chat Export: {chat_title_sanitized}</h1><p>Exported on {datetime.datetime.now().strftime("%Y-%m-%d %H%M%S")} ({len(sorted_messages)} messages)</p><hr>'
    ]
    for message in sorted_messages:
        sender_escaped = message['sender'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        timestamp_escaped = message['timestamp'].replace('&', '&lt;').replace('>', '&gt;')

        avatar_html = f'<img src="{message["avatar_src"]}" class="avatar">' if message[
            "avatar_src"] else '<div class="avatar"></div>'

        html_parts.append(
            f'<div class="message-container">{avatar_html}<div class="message-body"><div class="header"><p class="sender">{sender_escaped}</p><p class="timestamp">({timestamp_escaped})</p></div><div class="content">{message["content_html"]}</div></div></div>')

    html_parts.append('</body></html>')
    final_html = "".join(html_parts)

    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"\n--- SUCCESS! Exported {len(sorted_messages)} messages to '{output_filepath.resolve()}' ---", flush=True)
    await scope.evaluate(f"alert('Export complete! Saved to folder: {export_folder_name}')")
    await scope.evaluate("document.getElementById('teams-exporter-button')?.remove();")


async def get_active_scope(page: Page):
    config = await find_and_load_config(page, silent=True)
    if config: return page, config
    for frame in page.frames:
        if frame.parent_frame:
            config = await find_and_load_config(frame, silent=True)
            if config: return frame, config
    return None, None


async def main_logic(p, output_dir, debug_mode):
    browser_context = None
    try:
        print("--- Launching browser with persistent context ---", flush=True)
        browser_context = await p.chromium.launch_persistent_context(USER_DATA_DIR, headless=HEADLESS)
        page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()

        if debug_mode:
            print("DEBUG: Browser console logging enabled.", flush=True)
            page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}", flush=True))

        if "teams.microsoft.com" not in page.url:
            print("Navigating to Microsoft Teams homepage...", flush=True)
            await page.goto("https://teams.microsoft.com/")

        print("\n--- Script is now active and monitoring ---", flush=True)
        print("Please navigate to a chat. An 'Export' button will appear.", flush=True)

        is_exporting = False

        while True:
            if page.is_closed():
                print("\nBrowser-Fenster wurde geschlossen. Skript wird beendet.", flush=True)
                break

            try:
                if is_exporting:
                    await asyncio.sleep(1)
                    continue

                active_scope, config = await get_active_scope(page)
                if active_scope and config:
                    result = await active_scope.evaluate(INJECT_JS)
                    if result == 'injected':
                        print("--> 'Export This Chat' button has been injected.", flush=True)

                    button_selector = '#teams-exporter-button'
                    button_handle = await active_scope.query_selector(button_selector)
                    if button_handle:
                        button_text = await button_handle.text_content()
                        if "Exporting" in button_text:
                            is_exporting = True
                            await run_export_process(active_scope, config, page, output_dir)
                            is_exporting = False

                await asyncio.sleep(1)

            except PlaywrightError as e:
                if "Target page, context or browser has been closed" in str(e):
                    print("\nBrowser was closed during monitoring. Exiting loop.", flush=True)
                    break
                else:
                    raise

    except KeyboardInterrupt:
        print("\nScript interrupted by user.", flush=True)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", flush=True)
    except PlaywrightError as e:
        if "Target page, context or browser has been closed" in str(e):
            print("\nBrowser was closed prematurely. Script will now exit gracefully.", flush=True)
        else:
            print(f"\nAn unexpected Playwright error occurred: {e}", flush=True)
    finally:
        print("--- Script finished (Browser remains open) ---", flush=True)


async def main():
    parser = argparse.ArgumentParser(description="Microsoft Teams Chat Exporter")
    parser.add_argument("--outdir", type=str,
                        help="Directory to save exported chats. Defaults to 'saved_chats' in the script directory.")
    parser.add_argument("--debug", action="store_true", help="Enable browser console logging for debugging.")

    # If no arguments provided, print a friendly status message but proceed with defaults
    # This aligns with the request to show options/status when running bare
    args = parser.parse_args()

    if args.outdir:
        output_dir = Path(args.outdir)
    else:
        output_dir = DEFAULT_OUTPUT_DIR
        print(f"No output directory specified. Using default: {output_dir}")
        print("Tip: You can use --outdir to specify a custom location.")

    if not args.debug:
        print("Debug logging is OFF. Use --debug to enable.")

    async with async_playwright() as p:
        await main_logic(p, output_dir, args.debug)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting.", flush=True)