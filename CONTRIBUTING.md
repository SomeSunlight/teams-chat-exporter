# Contributing to the Teams Chat Exporter

Thank you for your interest in contributing! This document provides a technical overview of the project to help you get started.

## Architecture Overview

This script is built on Python using the Playwright library. It is designed to be robust against the challenges of automating a complex single-page application (SPA) like Microsoft Teams.

The core components are:

- **`main.py`:** The main script that contains the application logic.
    
- **`config/` directory:** Contains `.ini` files with CSS selectors for different versions of the Teams UI. This modular design allows for easy maintenance without touching the core Python code.
    
- **`saved_chats/` directory:** The default output location for exported HTML archives. This is included in `.gitignore`.
    
- **`playwright_user_data/` directory:** Stores the persistent browser context (cookies, local storage) to maintain the login session. This is included in `.gitignore`.
    

### Key Technical Concepts

1. **Persistent Context (`launch_persistent_context`):** The script launches its own browser instance with a dedicated user data directory. This is the key to the user-friendly login system. The user only needs to authenticate once, and the session is securely stored for subsequent runs. We chose this over the `connect_over_cdp` method to avoid requiring the user to launch their browser in a special, cumbersome way.
    
2. **Element-Based Monitoring Loop:** The script does not rely on URL changes to detect a chat. Instead, it continuously polls the page to see if a valid configuration can be found (i.e., if an `app_shell_selector` exists). This is robust against the SPA behavior of Teams where the URL does not always reflect the current view.
    
3. **In-Page Trigger (`INJECT_JS`):** To start an export, the script injects a button onto the page. We discovered that communication from this button's JavaScript back to Python was unreliable (`document.title`, DOM element creation, and `localStorage` all failed due to sandboxing or state synchronization issues). The final, robust solution is a "polling" mechanism: the button's only job is to change its own text, and the Python script polls this text to detect a click.
    
4. **Hybrid Image Saving:** To create a self-contained archive, the script handles images with a two-path "graceful fallback" system:
    
    - **Forced Screenshots:** For special elements like emoticon sprite sheets (identified by substrings in the `config.ini`), the script takes a screenshot of the rendered container element. This ensures a clean, static image is captured. The screenshot is then post-processed with the Pillow library to crop it to the correct dimensions.
        
    - **Graceful Fallback:** For all other images (content pictures, avatars), the script first attempts to download the original, full-quality file by executing a JavaScript `fetch` in the browser's context and passing the result back as a Base64 string. If this fails for any reason (e.g., an API error), it automatically falls back to taking a screenshot of the element.
        

## Known Issues & Future Work

- **Detailed Reactions:** While the script captures the basic reaction counts and icons (using screenshots), identifying _who_ reacted (the list of names that appears on hover) is currently not implemented. We attempted to scrape the hover tooltip, but due to complex timing issues and the React rendering lifecycle, we could not achieve a stable result. The relevant code was removed for stability in v1.0. Contributions to solving this specific "hover-and-scrape" challenge are very welcome!
    

## Our Development Journey & Key Decisions

This project's final design is the result of extensive trial and error. Here are some of the key technical hurdles and why the current solutions were chosen:

- **Automated Scrolling:** We proved that programmatically dispatching events (`scrollTop`, `wheel` events, `KeyboardEvent('PageUp')`) from a browser console or a standard Playwright script is ignored by the Teams application. This is due to security features where the browser flags these events as "untrusted" (`event.isTrusted: false`). ShareX works because it injects input at the Operating System level, creating trusted events. Our final script works by having the user provide the trusted scroll input manually. _Correction:_ The final version _does_ use automated scrolling (`PageUp`), which was eventually made to work by targeting the correct container and ensuring focus.
    
- **State Synchronization:** We encountered numerous issues where the script's "view" of the page was out of sync with what was visibly rendered. This led to the failure of several trigger mechanisms. The final "button state polling" method is the most robust solution against these race conditions.
    
- **`iframe`s:** Teams uses `iframe`s extensively. The script is designed to search for the active chat context in both the main document and any embedded frames.
    

Thank you for helping to improve this tool!