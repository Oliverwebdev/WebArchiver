# Website Archiver

<div align="center">

<img src="WebArchiver.jpg" alt="Website Archiver Logo" width="300"/>

**Preserve, manage, and customize web content offline with this powerful archiving tool.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)

</div>

## 🚀 Key Features

- **✨ Smart Web Capturing** - Download complete websites with all resources (images, CSS, JavaScript, fonts)
- **🔄 Multiple Engines** - Choose between standard requests, Selenium, or Playwright for perfect captures
- **📚 Bulk Archive** - Download multiple websites at once with the batch processor
- **🔍 Content Search** - Find exactly what you need with full text search across your archives
- **🏷️ Tagging System** - Organize websites with custom tags for efficient categorization
- **📝 Notes & Annotations** - Add context with your own notes for each saved website
- **✏️ Built-in Editor** - Modify archived content directly within the application
- **📦 Import/Export** - Share your archives with others or back them up securely

## 📸 Screenshots

<div align="center">
<img src="https://via.placeholder.com/800x450?text=Main+Window" alt="Main Window" width="80%"/>
<p><em>Home screen displaying archived websites with tag filtering</em></p>

<img src="https://via.placeholder.com/800x450?text=Website+Editor" alt="Website Editor" width="80%"/>
<p><em>Built-in editor for customizing saved content</em></p>

<img src="https://via.placeholder.com/800x450?text=Download+Options" alt="Download Options" width="80%"/>
<p><em>Advanced download options for perfect website captures</em></p>
</div>

## 🔧 Installation

### Prerequisites

- Python 3.7 or higher
- PyQt6
- Internet connection for downloading websites

### Method 1: Using pip (Recommended)

```bash
# Install from PyPI
pip install website-archiver

# Launch the application
website-archiver
```

### Method 2: From Source

```bash
# Clone the repository
git clone https://github.com/Oliverwebdev/WebArchiver
cd website-archiver

# Create and activate virtual environment (recommended)
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run the application
python main.py
```

### Optional Dependencies

For the best archiving experience, install additional engines:

```bash
# For Playwright support (recommended for complex websites)
pip install playwright
playwright install chromium

# For Selenium support
pip install selenium
```

## 📖 User Guide

### Archiving Your First Website

1. Launch Website Archiver
2. Go to the **Download** tab
3. Enter the URL you want to archive
4. Select your preferred download options
5. Click **Download**
6. Your archived website will appear in the **Home** tab

### Managing Your Archives

- **Search**: Use the search bar to find websites by title, URL, or content
- **Filter by Tags**: Select a tag from the dropdown to filter related websites
- **Edit Website**: Click "Edit" to modify the website's content, tags, or properties
- **Add Notes**: Record your thoughts or context about why you archived the site
- **Export**: Share your archives with others using the export functionality

### Customizing Your Experience

Visit the **Settings** tab to configure:
- Storage location for your archives
- Default download engine
- Resource options (images, CSS, JS, fonts)
- Timeout and concurrency settings
- And much more!

## ⚙️ Technical Details

Website Archiver intelligently captures web content using a multi-step process:

1. **Analysis**: Evaluates the target website structure
2. **Download**: Retrieves HTML content using the selected engine
3. **Resource Collection**: Gathers linked resources (images, styles, scripts)
4. **Path Rewriting**: Modifies resource paths to work offline
5. **Storage**: Organizes content in a structured filesystem
6. **Indexing**: Catalogs the archive in the searchable database

The application architecture includes:
- `config_manager.py`: Manages application configuration
- `database_manager.py`: Handles SQLite database operations
- `scraper.py`: Core web scraping functionality
- `session_manager.py`: Manages application state between sessions
- `ui/`: PyQt6-based user interface components

## 🛠️ Development

Want to contribute to Website Archiver? Great! We welcome contributions of all kinds.

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork: `git clone `https://github.com/Oliverwebdev/WebArchiver
3. Create a virtual environment: `python -m venv venv`
4. Activate it and install dev dependencies: `pip install -r requirements-dev.txt`
5. Make your changes and submit a pull request!

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [PyQt](https://riverbankcomputing.com/software/pyqt/) for the GUI framework
- [Requests](https://requests.readthedocs.io/) for HTTP functionality
- [Selenium](https://selenium-python.readthedocs.io/) and [Playwright](https://playwright.dev/) for browser automation
- All the open source contributors who made this project possible

## 🤝 Support

If you find Website Archiver useful, please consider:
- Star the repository on GitHub
- Reporting issues or suggesting features
- Contributing code or documentation improvements
- Sharing the project with others


<div align="center">
<p><strong>Website Archiver</strong> - Because the web is too important to lose.</p>
</div>