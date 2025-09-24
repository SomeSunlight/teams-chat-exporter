# Microsoft Teams Chat Exporter

A Python script to export long Microsoft Teams chat histories as a single, searchable HTML file.

## The Problem

Microsoft Teams does not offer a user-friendly way to export an entire chat history. Standard "save page" tools fail because Teams uses "infinite scroll" and virtualization to load messages, meaning only a small fraction of the chat is ever present in the browser's memory at one time. Furthermore, the web application is heavily secured against in-browser automation, making traditional scraping scripts fail.

## The Solution

This project uses the **Playwright** browser automation framework to solve the problem reliably. It works by:

1.  **Persistent, Secure Login:** The script uses a dedicated browser context. You only need to log in manually once. Your credentials are never stored in the code.
2.  **Intelligent Session Handling:** If your session expires (e.g., after a week), the script will detect this, pause, and wait for you to log in again before continuing.
3.  **Human-Like Scrolling:** It automates the process of scrolling to the top of the chat to trigger the loading of all messages.
4.  **Live Message Collection:** It actively collects every unique message as it appears during the scroll process, defeating the app's virtualization.
5.  **HTML Export:** It finally assembles all collected messages into a clean, searchable HTML file.

## Prerequisites

* Python 3.8+
* pip (Python package installer)

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd teams-chat-exporter
    ```

2.  **Create a virtual environment:** (Recommended)
    ```bash
    python -m venv venv
    ```
    Activate it:
    * Windows: `.\venv\Scripts\activate`
    * macOS/Linux: `source venv/bin/activate`

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright browsers:** (This is a one-time setup)
    ```bash
    playwright install
    ```

## Configuration

Before running, you must configure the script. Open the `src/main.py` file and edit the following constant:

* `TEAMS_CHAT_URL`: **This is mandatory.** Paste the full URL of the Teams chat you want to export. It will look something like `https://teams.microsoft.com/_#/conversations/19:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx@thread.v2?ctx=chat`.

## Usage

1.  **Run the script from the project root:**
    ```bash
    python src/main.py
    ```

2.  **First-Time Run:**
    * A Chromium browser window will open.
    * The script will detect that you are not logged in and will print a message in the console asking you to do so.
    * Log in to Microsoft Teams as you normally would (including any two-factor authentication).
    * Once you are successfully logged in and the script detects the chat, it will automatically proceed.

3.  **Subsequent Runs:**
    * The script will start, open the browser, and you will already be logged in. The process will be fully automatic.

4.  **The Process:**
    * The script will navigate to your chat and begin scrolling up, printing its progress in the console. This may take several minutes for very long chats.
    * Once it reaches the beginning of the chat, it will build the HTML file.

5.  **Output:**
    * A file named `chat_export.html` will be created in the project's root directory.

## License

This project is licensed under the MIT License.