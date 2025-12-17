# Microsoft Teams Chat Exporter

A Python script to export long Microsoft Teams chat histories as a single, self-contained, and searchable HTML file.

## The Problem

Microsoft Teams does not offer a user-friendly way to export an entire chat history. Standard "save page" tools fail because Teams uses advanced techniques like "infinite scroll" and UI virtualization to load messages, meaning only a small fraction of the chat is ever visible to simple scrapers.

## The Solution

This project uses the **Playwright** browser automation framework to reliably solve this problem. It intelligently mimics user behavior to ensure every message is captured.

### Key Features ✨

- **Complete History Export:** Automatically scrolls to the beginning of a chat, loading all messages along the way.
    
- **Self-Contained Archives:** Downloads all images, avatars, and captures reactions as screenshots, creating a portable HTML file that works perfectly offline.
    
- **User-Friendly:** Launches its own browser and provides a simple in-page button to start the export. No need to handle complex URLs.
    
- **Secure & Persistent Login:** You only need to log in to Teams once. The script securely saves your session for future runs without ever storing your password in the code.
    
- **Smart & Maintainable:** Uses a modular configuration system, allowing the community to easily update the script when Microsoft changes the Teams UI.
    

## 🔒 Privacy & Data Protection

**Important:** This tool exports sensitive, personal conversations containing private data.

- **Output Location:** By default, chats are saved in the `saved_chats` folder within the project directory.
    
- **Custom Location:** It is strongly recommended to use the `--outdir` option to save exports directly to a secure, encrypted location (e.g., BitLocker drive, Veracrypt container) suitable for personal data.
    
- **Responsibility:** You are responsible for safeguarding the exported data in compliance with your local data privacy laws (e.g., GDPR).
    

## Prerequisites

- **Python 3.12** is highly recommended for the best performance.
    
- The **minimum required version is Python 3.8**.
    
- An installed Chromium-based browser (Google Chrome, Microsoft Edge).
    

## Setup Instructions

1. **Clone the Repository:**
    
    ```
    git clone <your-repo-url>
    cd teams-chat-exporter
    ```
    
2. **Create and Activate a Virtual Environment:**
    
    - **Windows (Command Prompt):**
        
        ```
        python -m venv .venv
        .\.venv\Scripts\activate
        ```
        
    - **macOS / Linux (Bash):**
        
        ```
        python3 -m venv .venv
        source .venv/bin/activate
        ```
        
3. **Install Dependencies:**
    
    ```
    pip install -r requirements.txt
    ```
    
4. **Install Playwright Browsers:** This is a one-time setup that downloads the browser binaries controlled by Playwright.
    
    ```
    playwright install
    ```
    

## Usage

### Basic Usage

Run the script to start the interactive browser:

```
python src/main.py
```

### Command Line Options

**`--outdir <path>`** Specify a custom directory to save exported chats. This is **strongly recommended** for keeping sensitive data separate from the program code (e.g., saving directly to an encrypted drive).

**`--debug`** Enable verbose logging from the browser console. Use this if the script is having trouble detecting chats or if you are developing new features.

**`--help`** Show the help message and exit.

**Example:**

```
python src/main.py --outdir "D:\Secure_Backups\Teams" --debug
```

### Workflow

1. **Login (First-Time Use Only):**
    
    - A new browser window will open, controlled by the script.
        
    - The script will ask you to log in to Microsoft Teams. Please do so as you normally would.
        
    - The script will remember your session for all future runs.
        
2. **Export a Chat:**
    
    - In the browser window opened by the script, **navigate to the chat** you want to export.
        
    - Within a few seconds, a blue **"Export This Chat"** button will appear at the top-right of the page.
        
    - **Click this button.**
        
    - The script will take over, begin scrolling, and print its progress in the terminal. This may take several minutes for very long chats.
        
3. **Output:**
    
    - When finished, a new folder containing the `index.html` file and an `images` subfolder will be created in your specified output directory.
        
    - You can then navigate to another chat in the same browser window, and a new export button will appear, ready for the next export.
        

## ⚠️ A Note on Maintenance

Microsoft will eventually update the Teams UI, which will cause the script to fail. This project is designed to be easily updated by the community.

When the script fails, it's almost always because the CSS selectors have changed. You can fix this by updating the relevant `.ini` file in the `config/` directory.

**How to Find New Selectors:**

1. Open Teams in your regular browser and open the Developer Tools (`F12`).
    
2. Use the "Inspect Element" tool (usually an icon with a mouse pointer in a square).
    
3. Click on the element you need to identify (e.g., the main chat scroll area, a message, a user's name).
    
4. Look for stable attributes in the highlighted HTML, like `data-tid="..."` or `data-testid="..."`.
    
5. Copy this selector, open the latest `.ini` file in the `config` folder, and update the corresponding value. If you create a new file, name it with the current date (e.g., `teams_YYYY-MM-DD.ini`).
    

## License

This project is licensed under the MIT License.