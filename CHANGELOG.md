# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/ "null").

## \[1.0.0\] - 2025-10-17

### Added

- Initial public release of the Teams Chat Exporter.
    
- Core functionality to export a full Microsoft Teams chat history to a single HTML file.
    
- **Persistent Login:** Script launches its own browser and securely saves the user's session, requiring only a one-time login.
    
- **Dynamic Chat Detection:** Automatically detects when the user navigates to a chat page and injects an "Export" button.
    
- **Automated Scrolling:** Programmatically scrolls to the top of the chat to ensure all messages are loaded for collection.
    
- **Robust Message Collection:** Uses a "collector" pattern to gather every unique message, defeating the UI virtualization used by Teams.
    
- **Self-Contained Exports:**
    
    - Creates a dedicated folder for each export, named with the chat title and a timestamp.
        
    - Downloads content images and user avatars, storing them locally.
        
    - Implements a "graceful fallback" to take a screenshot of any image that fails to download.
        
    - Intelligently captures animated emoticons as clean, static screenshots.
        
- **Maintainable Configuration:**
    
    - All UI selectors are stored in external `.ini` files.
        
    - The script auto-detects the correct configuration file for the current Teams version.
        
- **User-Friendly Interface:** Provides clear feedback in the terminal and uses an in-page button to trigger exports.
    
- **Robust Error Handling:** Gracefully handles premature browser closures and other common errors.
    
- **CLI Arguments:** Added `--outdir` to specify custom save locations and `--debug` for verbose browser logging.
    

### Notes

- Reaction details (who reacted) are currently not scraped due to technical limitations with the tooltip rendering. Basic reaction counts and icons are preserved.