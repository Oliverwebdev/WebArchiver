import os
import re
import shutil
import urllib.parse
import urllib.robotparser
import datetime
import time
import json
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed

# Web scraping imports
import requests
from bs4 import BeautifulSoup

# Image handling
from PIL import Image

# File operations
import zipfile

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import chromedriver_autoinstaller

# Optional Playwright support if available
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Import local modules
from config_manager import ConfigManager
from database_manager import DatabaseManager


class RobotsChecker:
    """Checks if scraping is allowed according to robots.txt"""
    def __init__(self, user_agent="WebArchiver/2.0"):
        self.user_agent = user_agent
        self.parsers = {}
    
    @lru_cache(maxsize=100)
    def can_fetch(self, url):
        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        if base_url not in self.parsers:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{base_url}/robots.txt")
            try:
                rp.read()
                self.parsers[base_url] = rp
            except Exception as e:
                print(f"Error reading robots.txt for {base_url}: {e}")
                return True
        return self.parsers[base_url].can_fetch(self.user_agent, url)


class WebScraper:
    """Handles downloading websites and their resources"""
    def __init__(self, config):
        self.config = config
        self.base_dir = config.get("base_dir", "saved_websites")
        self.timeout = config.get("timeout", 30)
        self.user_agent = config.get("user_agent", "WebArchiver/2.0")
        self.respect_robots_txt = config.get("respect_robots_txt", True)
        self.sanitize_html = config.get("sanitize_html", False)
        self.max_workers = config.get("max_concurrent_downloads", 8)
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
        self.driver = None
        if self.respect_robots_txt:
            self.robots_checker = RobotsChecker(self.user_agent)
        
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
    
    def _setup_selenium(self):
        try:
            if self.driver:
                try:
                    _ = self.driver.current_url
                    return True
                except:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
            
            chromedriver_autoinstaller.install()
            chrome_options = Options()
            if self.config.get("selenium_headless", True):
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_experimental_option("detach", True)
            
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            return True
        except Exception as e:
            print(f"Error setting up Selenium: {str(e)}")
            return False
    
    def _close_selenium(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def _setup_playwright(self):
        return PLAYWRIGHT_AVAILABLE
    
    def download_page(self, url, callback=None, engine=None, options=None):
        if options is None:
            options = {}
        
        if self.respect_robots_txt and not options.get('ignore_robots_txt', False):
            if not self.robots_checker.can_fetch(url):
                raise PermissionError(f"robots.txt disallows scraping of {url}")
        
        try:
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc
            page_path = parsed_url.path
            if page_path in ['', '/']:
                page_path = '/index'
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            dir_name = f"{domain.replace('.', '_')}_{timestamp}"
            page_dir = os.path.join(self.base_dir, dir_name)
            
            os.makedirs(page_dir)
            os.makedirs(os.path.join(page_dir, 'assets', 'images'))
            os.makedirs(os.path.join(page_dir, 'assets', 'css'))
            os.makedirs(os.path.join(page_dir, 'assets', 'js'))
            os.makedirs(os.path.join(page_dir, 'assets', 'fonts'))
            
            if engine is None:
                engine = self.config.get("preferred_engine", "requests")
            
            if callback:
                callback(f"Downloading main HTML using {engine}...", 5)
            
            if engine == "selenium":
                html_content = self._download_with_selenium(url, page_dir, callback)
            elif engine == "playwright" and self._setup_playwright():
                html_content = self._download_with_playwright(url, page_dir, callback)
            else:
                html_content = self._download_with_requests(url, page_dir, callback)
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            if self.sanitize_html or options.get('sanitize_html', False):
                if callback:
                    callback("Sanitizing HTML...", 10)
                soup = self._sanitize_html(soup)
            
            if callback:
                callback("Processing resources...", 15)
            
            self._process_resources(soup, url, page_dir, callback)
            
            if callback:
                callback("Saving modified HTML...", 90)
            with open(os.path.join(page_dir, "index.html"), 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            if callback:
                callback("Creating thumbnail...", 95)
            thumbnail_path = self._create_thumbnail(page_dir)
            
            title = soup.title.string if soup.title else "Unknown Title"
            metadata = {
                'url': url,
                'title': title,
                'domain': domain,
                'timestamp': timestamp,
                'date_saved': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'thumbnail': thumbnail_path,
                'directory': page_dir,
                'engine_used': engine
            }
            
            with open(os.path.join(page_dir, "metadata.json"), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4)
            
            if callback:
                callback("Website saved successfully!", 100)
            return metadata
        
        except Exception as e:
            if 'page_dir' in locals() and os.path.exists(page_dir):
                shutil.rmtree(page_dir)
            raise
    
    def _download_with_requests(self, url, page_dir, callback=None):
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error downloading with requests: {str(e)}")
    
    def _download_with_selenium(self, url, page_dir, callback=None):
        if not self.driver and not self._setup_selenium():
            raise Exception("Failed to initialize Selenium WebDriver")
        if callback:
            callback("Loading page with Selenium...", 10)
        try:
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.get(url)
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located(("tag name", "body"))
                )
            except TimeoutException:
                if callback:
                    callback("Page took too long to load, continuing anyway...", 15)
            time.sleep(2)
            return self.driver.page_source
        except Exception as e:
            raise Exception(f"Error downloading with Selenium: {str(e)}")
    
    def _download_with_playwright(self, url, page_dir, callback=None):
        if callback:
            callback("Starting Playwright browser...", 5)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=self.user_agent)
                if callback:
                    callback("Loading page with Playwright...", 10)
                page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
                page.wait_for_timeout(2000)
                html_content = page.content()
                browser.close()
                return html_content
        except Exception as e:
            raise Exception(f"Error downloading with Playwright: {str(e)}")
    
    def _sanitize_html(self, soup):
        for script in soup.find_all('script'):
            script.decompose()
        for tag in soup.find_all(True):
            for attr in list(tag.attrs):
                if attr.startswith('on'):
                    del tag[attr]
        for iframe in soup.find_all('iframe'):
            iframe.decompose()
        for tag in soup.find_all(['object', 'embed']):
            tag.decompose()
        return soup
    
    def _process_resources(self, soup, base_url, page_dir, callback=None):
        resources = []
        if self.config.get("download_css", True):
            for link in soup.find_all('link', rel='stylesheet'):
                if 'href' in link.attrs:
                    resources.append(('css', link['href'], link, 'href'))
        if self.config.get("download_js", True):
            for script in soup.find_all('script', src=True):
                resources.append(('js', script['src'], script, 'src'))
        if self.config.get("download_images", True):
            for img in soup.find_all('img', src=True):
                if not img['src'].startswith('data:'):
                    resources.append(('img', img['src'], img, 'src'))
        
        total = len(resources)
        if total == 0:
            if callback:
                callback("No resources to download", 20)
            return
        
        if callback:
            callback(f"Downloading {total} resources...", 20)
        
        def download_worker(res_type, url_path, element, attr):
            try:
                resource_url = url_path
                if resource_url.startswith('//'):
                    resource_url = 'https:' + resource_url
                elif not resource_url.startswith(('http://', 'https://')):
                    resource_url = urllib.parse.urljoin(base_url, resource_url)
                
                if self.respect_robots_txt and not self.robots_checker.can_fetch(resource_url):
                    print(f"Skipping {resource_url} (blocked by robots.txt)")
                    return None
                
                if res_type == 'css':
                    new_path = self._download_css(resource_url, page_dir, base_url)
                elif res_type == 'js':
                    new_path = self._download_js(resource_url, page_dir)
                elif res_type == 'img':
                    new_path = self._download_image(resource_url, page_dir)
                else:
                    return None
                if new_path:
                    return (element, attr, new_path)
            except Exception as e:
                print(f"Error downloading {res_type} {url_path}: {str(e)}")
            return None
        
        completed = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_res = {
                executor.submit(download_worker, rt, up, el, at): (i, rt)
                for i, (rt, up, el, at) in enumerate(resources)
            }
            for future in as_completed(future_to_res):
                completed += 1
                result = future.result()
                if callback:
                    progress = 20 + int((completed / total) * 70)
                    callback(f"Downloaded {completed}/{total} resources", progress)
                if result:
                    element, attr, new_path = result
                    element[attr] = new_path
    
    def _download_css(self, css_url, page_dir, base_url):
        try:
            r = self.session.get(css_url, timeout=self.timeout)
            r.raise_for_status()
            css_content = r.text
            css_filename = os.path.basename(urllib.parse.urlparse(css_url).path)
            if not css_filename or '.' not in css_filename:
                css_filename = f"style_{hash(css_url) % 10000}.css"
            css_content = self._fix_css_urls(css_content, css_url, page_dir, base_url)
            css_path = os.path.join(page_dir, 'assets', 'css', css_filename)
            with open(css_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(css_content)
            return os.path.join('assets', 'css', css_filename).replace('\\', '/')
        except Exception as e:
            print(f"Error downloading CSS {css_url}: {str(e)}")
            return None
    
    def _fix_css_urls(self, css_content, css_url, page_dir, base_url):
        url_pattern = re.compile(r'url\([\'"]?(.*?)[\'"]?\)')
        replacements = []
        for match in url_pattern.finditer(css_content):
            resource_url = match.group(1)
            if resource_url.startswith('data:'):
                continue
            if resource_url.startswith('//'):
                absolute_url = 'https:' + resource_url
            elif not resource_url.startswith(('http://', 'https://')):
                css_base = os.path.dirname(css_url)
                absolute_url = urllib.parse.urljoin(css_base + '/', resource_url)
            else:
                absolute_url = resource_url
            
            ext = os.path.splitext(absolute_url)[1].lower()
            try:
                if ext in ['.woff', '.woff2', '.ttf', '.eot', '.otf']:
                    if self.config.get("download_fonts", True):
                        local_path = self._download_font(absolute_url, page_dir)
                        if local_path:
                            replacements.append((match.group(0), f'url({local_path})'))
                elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']:
                    if self.config.get("download_images", True):
                        local_path = self._download_image(absolute_url, page_dir)
                        if local_path:
                            replacements.append((match.group(0), f'url({local_path})'))
            except Exception as e:
                print(f"Error processing CSS resource {absolute_url}: {str(e)}")
        
        for old, new in replacements:
            css_content = css_content.replace(old, new)
        return css_content
    
    def _download_js(self, js_url, page_dir):
        try:
            r = self.session.get(js_url, timeout=self.timeout)
            r.raise_for_status()
            js_filename = os.path.basename(urllib.parse.urlparse(js_url).path)
            if not js_filename or '.' not in js_filename:
                js_filename = f"script_{hash(js_url) % 10000}.js"
            js_path = os.path.join(page_dir, 'assets', 'js', js_filename)
            with open(js_path, 'wb') as f:
                f.write(r.content)
            return os.path.join('assets', 'js', js_filename).replace('\\', '/')
        except Exception as e:
            print(f"Error downloading JS {js_url}: {str(e)}")
            return None
    
    def _download_image(self, img_url, page_dir):
        try:
            r = self.session.get(img_url, timeout=self.timeout, stream=True)
            r.raise_for_status()
            img_filename = os.path.basename(urllib.parse.urlparse(img_url).path)
            if not img_filename or '.' not in img_filename:
                content_type = r.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'svg' in content_type:
                    ext = '.svg'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'
                img_filename = f"image_{hash(img_url) % 10000}{ext}"
            
            img_path = os.path.join(page_dir, 'assets', 'images', img_filename)
            with open(img_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return os.path.join('assets', 'images', img_filename).replace('\\', '/')
        except Exception as e:
            print(f"Error downloading image {img_url}: {str(e)}")
            return None
    
    def _download_font(self, font_url, page_dir):
        try:
            r = self.session.get(font_url, timeout=self.timeout)
            r.raise_for_status()
            font_filename = os.path.basename(urllib.parse.urlparse(font_url).path)
            if not font_filename or '.' not in font_filename:
                content_type = r.headers.get('content-type', '')
                if 'woff2' in content_type or 'woff2' in font_url:
                    ext = '.woff2'
                elif 'woff' in content_type or 'woff' in font_url:
                    ext = '.woff'
                elif 'ttf' in content_type or 'ttf' in font_url:
                    ext = '.ttf'
                elif 'otf' in content_type or 'otf' in font_url:
                    ext = '.otf'
                elif 'eot' in content_type or 'eot' in font_url:
                    ext = '.eot'
                elif 'svg' in content_type or 'svg' in font_url:
                    ext = '.svg'
                else:
                    ext = '.woff'
                font_filename = f"font_{hash(font_url) % 10000}{ext}"
            
            font_path = os.path.join(page_dir, 'assets', 'fonts', font_filename)
            with open(font_path, 'wb') as f:
                f.write(r.content)
            return os.path.join('..', 'fonts', font_filename).replace('\\', '/')
        except Exception as e:
            print(f"Error downloading font {font_url}: {str(e)}")
            return None
    
    def _create_thumbnail(self, page_dir):
        img = Image.new('RGB', (200, 150), color='#f0f0f0')
        thumbnail_path = os.path.join(page_dir, "thumbnail.png")
        img.save(thumbnail_path)
        return thumbnail_path
    
    def batch_download(self, urls, callback=None, engine=None, options=None):
        results = []
        errors = []
        total_urls = len(urls)
        for i, url in enumerate(urls):
            overall_progress = int((i / total_urls) * 100) if total_urls > 0 else 0
            if callback:
                callback(f"Processing page {i+1}/{total_urls}: {url}", overall_progress)
            
            def url_callback(message, progress):
                if callback:
                    if progress >= 0:
                        sub_progress = int(overall_progress + (progress / 100) * (100 / total_urls))
                        callback(f"[{i+1}/{total_urls}] {message}", sub_progress)
                    else:
                        callback(f"[{i+1}/{total_urls}] {message}", overall_progress)
            
            try:
                metadata = self.download_page(url, url_callback, engine, options)
                results.append(metadata)
            except Exception as e:
                error_msg = f"Error processing {url}: {str(e)}"
                errors.append({"url": url, "error": str(e)})
                if callback:
                    callback(error_msg, -1)
        
        if engine == "selenium" and self.driver:
            self._close_selenium()
        
        return {
            "success": results,
            "errors": errors,
            "total": total_urls,
            "successful": len(results),
            "failed": len(errors)
        }
    
    def export_to_zip(self, directory, zip_path=None):
        if zip_path is None:
            zip_path = directory + ".zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, os.path.dirname(directory))
                    zipf.write(file_path, arc_name)
        return zip_path
    
    def create_new_version(self, original_dir, new_title=None):
        metadata_path = os.path.join(original_dir, "metadata.json")
        if not os.path.exists(metadata_path):
            raise ValueError("Original website metadata not found")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            original_metadata = json.load(f)
        
        domain = original_metadata.get("domain", "unknown_domain").replace('.', '_')
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        new_dir_name = f"{domain}_{timestamp}"
        new_dir = os.path.join(os.path.dirname(original_dir), new_dir_name)
        
        shutil.copytree(original_dir, new_dir)
        
        if new_title is None:
            new_title = f"{original_metadata.get('title', 'Unknown Title')} (edited)"
        new_metadata = original_metadata.copy()
        new_metadata.update({
            'title': new_title,
            'date_saved': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'directory': new_dir,
            'is_edited': True,
            'original_directory': original_dir,
            'parent_id': original_metadata.get('id')
        })
        
        with open(os.path.join(new_dir, "metadata.json"), 'w', encoding='utf-8') as f:
            json.dump(new_metadata, f, indent=4)
        return new_metadata


class WebArchiver:
    """Core logic layer separated from GUI"""
    def __init__(self, config_path="config.json"):
        self.config_manager = ConfigManager(config_path)
        self.db_manager = DatabaseManager(self.config_manager.get("database_path"))
        self.scraper = WebScraper(self.config_manager)
    
    def download_website(self, url, callback=None, engine=None, options=None):
        metadata = self.scraper.download_page(url, callback, engine, options)
        website_id = self.db_manager.add_website(metadata)
        if website_id:
            metadata['id'] = website_id
        return metadata
    
    def batch_download(self, urls, callback=None, engine=None, options=None):
        result = self.scraper.batch_download(urls, callback, engine, options)
        for metadata in result["success"]:
            website_id = self.db_manager.add_website(metadata)
            if website_id:
                metadata['id'] = website_id
        return result
    
    def get_all_websites(self, search_term=None, tag=None):
        return self.db_manager.get_all_websites(search_term, tag)
    
    def delete_website(self, website_id, directory):
        self.db_manager.delete_website(website_id)
        if os.path.exists(directory) and os.path.isdir(directory):
            shutil.rmtree(directory)
            return True
        return False
    
    def export_website(self, directory, zip_path=None):
        return self.scraper.export_to_zip(directory, zip_path)
    
    def import_website(self, zip_path):
        try:
            temp_dir = os.path.join(self.config_manager.get("base_dir"), "temp_import")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            metadata_path = None
            for root, dirs, files in os.walk(temp_dir):
                if "metadata.json" in files:
                    metadata_path = os.path.join(root, "metadata.json")
                    break
            if not metadata_path:
                raise ValueError("Invalid archive: No metadata.json found")
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            domain = metadata.get('domain', 'unknown_domain').replace('.', '_')
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            dir_name = f"{domain}_{timestamp}"
            target_dir = os.path.join(self.config_manager.get("base_dir"), dir_name)
            extracted_dir = os.path.dirname(metadata_path)
            shutil.move(extracted_dir, target_dir)
            shutil.rmtree(temp_dir)
            
            metadata['directory'] = target_dir
            metadata['timestamp'] = timestamp
            metadata['date_saved'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(os.path.join(target_dir, "metadata.json"), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4)
            
            website_id = self.db_manager.add_website(metadata)
            if website_id:
                metadata['id'] = website_id
            return metadata
        except Exception as e:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise ValueError(f"Error importing from zip: {str(e)}")
    
    def create_new_version(self, directory, new_title=None):
        new_metadata = self.scraper.create_new_version(directory, new_title)
        website_id = self.db_manager.add_website(new_metadata)
        if website_id:
            new_metadata['id'] = website_id
            original = self.db_manager.get_website_by_directory(directory)
            if original:
                original_tags = self.db_manager.get_website_tags(original["id"])
                for tag in original_tags:
                    self.db_manager.add_website_tag(website_id, tag["name"])
        return new_metadata