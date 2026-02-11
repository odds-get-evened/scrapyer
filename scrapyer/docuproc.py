import hashlib
import re
import socket
import ssl
from pathlib import Path
from time import sleep
from typing import List, Set
from urllib.parse import urljoin, urlparse
from collections import deque

from bs4 import BeautifulSoup, Tag

from scrapyer.docusource import DocumentSource, SourceType
from scrapyer.httprequest import HttpRequest


# Network exceptions that should trigger retries
NETWORK_EXCEPTIONS = (TimeoutError, socket.gaierror, ssl.SSLError, ConnectionError, OSError)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# HTML elements to remove (non-content)
EXCLUDED_ELEMENTS = ['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript', 'iframe', 
                     'form', 'button', 'dialog']

# ARIA roles to exclude (navigation and UI components)
EXCLUDED_ROLES = ['navigation', 'banner', 'complementary', 'contentinfo']

# Regex patterns for class/id attributes that indicate navigation or UI components
EXCLUDED_CLASS_ID_PATTERNS = [
    r'sidebar', r'menu', r'nav[-_]', r'breadcrumb', r'pagination',
    r'advertisement', r'ad[-_]', r'banner', r'popup', r'modal',
    r'widget', r'comment[-_]?(?:s|section)?', r'related', r'newsletter',
    r'social[-_]', r'share[-_]', r'sticky', r'overlay', r'toolbar',
]

# Pre-compiled regex patterns for performance
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in EXCLUDED_CLASS_ID_PATTERNS]

# Main content selectors (in priority order)
CONTENT_SELECTORS = [
    'article',
    'main',
    '[role="main"]',
    '.article-content',
    '.post-content',
    '.entry-content',
    '#content',
    '.content',
    '#main',
    '.main'
]

# URL patterns to remove from text content
# Matches URLs in various formats: http://, https://, www., ftp://
# Including URLs in parentheses, brackets, or standalone

# URL matching components
URL_PROTOCOL = r'(?:https?|ftp):\/\/|www\.'
URL_CHARS = r'[a-zA-Z0-9\-._~:/?#@!$&\'()*+,;=%]+'  # URL-safe characters

# Complete URL pattern for matching standalone URLs
URL_PATTERN = re.compile(
    r'(?:' + URL_PROTOCOL + r')' + URL_CHARS,
    re.IGNORECASE
)


class DocumentProcessor:
    def __init__(self, req: HttpRequest, p: Path, 
                 strip_html: bool = True, 
                 preserve_structure: bool = False,
                 media_types: List[str] = None,
                 crawl: bool = False,
                 crawl_limit: int = None,
                 timeout: int = 30,
                 verify_ssl: bool = True,
                 ssl_context: ssl.SSLContext = None):
        """
        Initialize the document processor for extracting main content from web pages.
        
        Args:
            req: HttpRequest object configured with the target URL
            p: Path where extracted content should be saved
            strip_html: Remove all HTML tags and extract plain text (default: True)
            preserve_structure: Keep basic structure like headings and paragraphs (default: False)
            media_types: List of media types to extract (e.g., ['images', 'videos', 'audio'])
            crawl: If True, crawl linked pages from the initial URL (default: False)
            crawl_limit: Maximum number of pages to crawl; None for unlimited (default: None)
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Enable/disable SSL certificate verification (default: True)
            ssl_context: Custom SSL context for HTTPS connections (default: None)
        """
        self.dom: BeautifulSoup = None
        self.is_processing: bool = False
        self.save_path: Path = p
        self.strip_html: bool = strip_html
        self.preserve_structure: bool = preserve_structure
        self.media_types: List[str] = media_types if media_types is not None else ['images', 'videos', 'audio']
        
        # Crawling configuration
        self.crawl: bool = crawl
        self.crawl_limit: int = crawl_limit
        self.timeout: int = timeout
        self.verify_ssl: bool = verify_ssl
        self.ssl_context: ssl.SSLContext = ssl_context
        
        # Track visited and queued URLs to avoid duplicates
        self.visited_urls: Set[str] = set()
        self.url_queue: deque = deque()
        
        # Store only media sources (no scripts or stylesheets)
        self.media_sources: list[DocumentSource] = []
        
        self.request: HttpRequest = req

    def start(self):
        """
        Main processing loop: fetch HTML, extract content and media, save to disk.
        If crawl mode is enabled, also crawl linked pages.
        """
        if self.crawl:
            print(f"🔍 Crawl mode enabled" + (f" (limit: {self.crawl_limit} pages)" if self.crawl_limit else " (unlimited)"))
        
        # Start with the initial URL
        initial_url = self.request.get_root_url() + self.request.build_url_path()
        self.url_queue.append((initial_url, self.save_path))
        
        while self.url_queue:
            # Check if we've reached the crawl limit
            if self.crawl_limit and len(self.visited_urls) >= self.crawl_limit:
                print(f"\n🛑 Reached crawl limit of {self.crawl_limit} pages")
                break
            
            current_url, current_save_path = self.url_queue.popleft()
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
            
            # Mark as visited
            self.visited_urls.add(current_url)
            
            print(f"\n{'='*80}")
            print(f"🌐 Processing page {len(self.visited_urls)}/{self.crawl_limit if self.crawl_limit else '∞'}: {current_url}")
            print(f"{'='*80}")
            
            # Process this page
            self._process_single_page(current_url, current_save_path)
        
        print(f"\n✨ Processing complete! Crawled {len(self.visited_urls)} page(s).")
    
    def _process_single_page(self, url: str, save_path: Path):
        """
        Process a single page: fetch, extract content and media, save to disk.
        If crawl mode is enabled, extract and queue linked pages.
        
        Args:
            url: The URL to process
            save_path: Directory path to save extracted content
        """
        self.is_processing = True
        self.media_sources = []  # Reset media sources for each page
        
        # Create a new request for this URL
        request = HttpRequest(
            url,
            time_out=self.timeout,
            verify_ssl=self.verify_ssl,
            ssl_context=self.ssl_context,
            fetch_html_only=True
        )

        while self.is_processing is True:
            try:
                response = request.get()
                
                # Check content type
                content_type = response.getheader('Content-Type', '')
                content_type_lower = content_type.lower()
                
                # Parse content based on type
                content = response.read()
                
                if 'text/html' in content_type_lower or 'application/xhtml' in content_type_lower:
                    # Standard HTML content
                    self.dom = BeautifulSoup(content, 'html.parser')
                    print(f"✅ Status: {response.status} {response.reason}")
                elif 'xml' in content_type_lower:
                    # XML content (RSS, Atom, or other XML)
                    print(f"📰 Detected XML content: {content_type}")
                    # Try to use lxml-xml parser first, fallback to html.parser
                    try:
                        self.dom = BeautifulSoup(content, 'lxml-xml')
                    except Exception:
                        self.dom = BeautifulSoup(content, 'html.parser')
                    print(f"✅ Status: {response.status} {response.reason}")
                else:
                    print(f"⚠️  Warning: Response content type is '{content_type}', expected HTML or XML")
                    self.dom = BeautifulSoup(content, 'html.parser')
                    print(f"✅ Status: {response.status} {response.reason}")

                # Extract links if crawl mode is enabled
                if self.crawl:
                    self._extract_and_queue_links(url, request)
                
                # Extract media sources from the page (images, videos, audio)
                # Skip if no media types are configured (text-only mode)
                if self.media_types:
                    self.extract_media_sources()
                
            except ValueError as e:
                # Handle non-HTML content types (e.g., Atom feeds, XML, JSON)
                print(f"⚠️  Skipping: {e}")
                self.is_processing = False
                return  # Skip processing this URL
            except NETWORK_EXCEPTIONS as e:
                print(f"❌ Network error: {e}")
                sleep(self.timeout)
                continue

            self.is_processing = False

        # Download all media files (only if media types are configured)
        if self.media_sources and self.media_types:
            print(f"\n📥 Downloading {len(self.media_sources)} media files...")
            for source in self.media_sources:
                self.store_media(source, save_path, request)

        # Extract and save text content
        print("\n📝 Extracting text content...")
        self.save_text(save_path, request)

    def extract_media_sources(self):
        """
        Extract media elements (images, videos, audio) from the main content area.
        Ignores scripts, stylesheets, and other non-content resources.
        """
        if self.dom is None:
            return
        
        # Find the main content area first
        main_content = self._find_main_content()
        
        # Extract images if requested
        if 'images' in self.media_types:
            self._extract_images(main_content)
        
        # Extract videos if requested
        if 'videos' in self.media_types:
            self._extract_videos(main_content)
        
        # Extract audio if requested
        if 'audio' in self.media_types:
            self._extract_audio(main_content)
    
    def _extract_and_queue_links(self, base_url: str, request: HttpRequest):
        """
        Extract links from the current page and queue them for crawling.
        Only queues links from the same domain.
        
        Args:
            base_url: The current page URL
            request: HttpRequest object for resolving relative URLs
        """
        if self.dom is None:
            return
        
        base_domain = urlparse(base_url).netloc
        links_found = 0
        links_queued = 0
        
        # Find all <a> tags with href attributes
        for link_tag in self.dom.find_all('a', href=True):
            href = link_tag.get('href', '').strip()
            
            # Skip empty, anchor-only, javascript:, and mailto: links
            if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            
            try:
                # Convert to absolute URL
                absolute_url = request.absolute_source(href)
                
                # Parse the URL to check domain and clean it
                parsed_url = urlparse(absolute_url)
                
                # Remove fragments (anchors)
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                if parsed_url.query:
                    clean_url += f"?{parsed_url.query}"
                
                # Only crawl links from the same domain
                if parsed_url.netloc != base_domain:
                    continue
                
                links_found += 1
                
                # Skip if already visited or queued
                if clean_url in self.visited_urls or any(clean_url == url for url, _ in self.url_queue):
                    continue
                
                # Queue the link for processing (use base save_path for all)
                self.url_queue.append((clean_url, self.save_path))
                links_queued += 1
                
            except Exception as e:
                # Skip problematic URLs - this is expected for malformed URLs
                # Could log if needed: print(f"⚠️  Skipping invalid URL {href}: {e}")
                continue
        
        if links_found > 0:
            print(f"🔗 Found {links_found} links on page, queued {links_queued} new links for crawling")
    
    def _generate_content_filename(self, content: str) -> str:
        """
        Generate a unique filename for the text content based on hash of content.
        
        Args:
            content: The text content to hash
            
        Returns:
            String filename for the content file in format content_<hash>.txt
        """
        # Generate hash of content (using 32 characters for lower collision risk)
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:32]
        
        # Generate filename: content_<hash>.txt
        filename = f"content_{content_hash}.txt"
        
        return filename

    def _find_main_content(self) -> Tag:
        """
        Find the main content area of the page using common selectors.
        
        Returns:
            BeautifulSoup Tag object containing the main content, or body/root if not found
        """
        # Try each selector in priority order
        for selector in CONTENT_SELECTORS:
            main_content = self.dom.select_one(selector)
            if main_content:
                print(f"🎯 Found main content using selector: {selector}")
                return main_content
        
        # Fallback to body or entire document
        print("📄 Using entire document as main content")
        return self.dom.body if self.dom.body else self.dom

    def _filter_navigation_and_ui_elements(self, content: Tag) -> None:
        """
        Remove navigation items and UI components from content based on:
        - ARIA role attributes (navigation, banner, complementary, contentinfo)
        - Common class/id patterns (sidebar, menu, nav, breadcrumb, ads, etc.)
        
        Performance optimization: Check ARIA role first (simple string lookup) before
        processing class/id patterns (regex matching), as role checks are faster.
        Elements are collected first then removed to avoid modifying the tree during iteration.
        
        Args:
            content: BeautifulSoup Tag object to filter
        """
        # Collect elements to remove (avoid modifying tree while iterating)
        elements_to_remove = []
        
        # Find all elements with attributes that might need filtering
        for elem in content.find_all(True):
            should_remove = False
            
            # Check ARIA role first (faster than regex matching)
            role = elem.get('role')
            if role and role.lower() in EXCLUDED_ROLES:
                should_remove = True
            
            # Only process class/id if role check didn't trigger removal
            if not should_remove:
                classes = elem.get('class')
                elem_id = elem.get('id')
                
                # Only check if element has class or id attributes
                if classes or elem_id:
                    # Combine class and id for pattern matching
                    combined_attrs = ' '.join(filter(None, [' '.join(classes or []), elem_id]))
                    combined_attrs = combined_attrs.lower()
                    
                    # Check against pre-compiled patterns
                    for pattern in COMPILED_PATTERNS:
                        if pattern.search(combined_attrs):
                            should_remove = True
                            break
            
            if should_remove:
                elements_to_remove.append(elem)
        
        # Remove all identified elements
        for elem in elements_to_remove:
            elem.decompose()
        
        if elements_to_remove:
            print(f"🧹 Filtered {len(elements_to_remove)} navigation/UI elements")


    def _extract_images(self, content: Tag):
        """Extract image URLs from <img>, <picture>, and srcset attributes."""
        img_count = 0
        
        # Standard <img> tags
        for img in content.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src:
                try:
                    img_url = self.request.absolute_source(src)
                    self.media_sources.append(DocumentSource(SourceType.img, img_url))
                    img_count += 1
                except Exception as e:
                    print(f"⚠️  Could not process image: {src} - {e}")
            
            # Handle srcset for responsive images
            srcset = img.get('srcset')
            if srcset:
                for src_item in srcset.split(','):
                    src_url = src_item.strip().split(' ')[0]
                    if src_url:
                        try:
                            img_url = self.request.absolute_source(src_url)
                            self.media_sources.append(DocumentSource(SourceType.img, img_url))
                            img_count += 1
                        except Exception as e:
                            print(f"⚠️  Could not process srcset image: {src_url} - {e}")
        
        # <picture> elements with <source> tags
        for picture in content.find_all('picture'):
            for source in picture.find_all('source'):
                srcset = source.get('srcset')
                if srcset:
                    src_url = srcset.split(',')[0].strip().split(' ')[0]
                    try:
                        img_url = self.request.absolute_source(src_url)
                        self.media_sources.append(DocumentSource(SourceType.img, img_url))
                        img_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not process picture source: {src_url} - {e}")
        
        if img_count > 0:
            print(f"🖼️  Found {img_count} images")

    def _extract_videos(self, content: Tag):
        """Extract video URLs from <video> and embedded players."""
        video_count = 0
        
        # <video> tags
        for video in content.find_all('video'):
            # Direct src attribute
            src = video.get('src')
            if src:
                try:
                    video_url = self.request.absolute_source(src)
                    self.media_sources.append(DocumentSource(SourceType.video, video_url))
                    video_count += 1
                except Exception as e:
                    print(f"⚠️  Could not process video: {src} - {e}")
            
            # <source> child elements
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    try:
                        video_url = self.request.absolute_source(src)
                        self.media_sources.append(DocumentSource(SourceType.video, video_url))
                        video_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not process video source: {src} - {e}")
        
        if video_count > 0:
            print(f"🎬 Found {video_count} videos")

    def _extract_audio(self, content: Tag):
        """Extract audio URLs from <audio> tags."""
        audio_count = 0
        
        for audio in content.find_all('audio'):
            # Direct src attribute
            src = audio.get('src')
            if src:
                try:
                    audio_url = self.request.absolute_source(src)
                    self.media_sources.append(DocumentSource(SourceType.audio, audio_url))
                    audio_count += 1
                except Exception as e:
                    print(f"⚠️  Could not process audio: {src} - {e}")
            
            # <source> child elements
            for source in audio.find_all('source'):
                src = source.get('src')
                if src:
                    try:
                        audio_url = self.request.absolute_source(src)
                        self.media_sources.append(DocumentSource(SourceType.audio, audio_url))
                        audio_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not process audio source: {src} - {e}")
        
        if audio_count > 0:
            print(f"🔊 Found {audio_count} audio files")

    def _remove_urls_from_text(self, text: str) -> str:
        """
        Remove all URLs from text content.
        This removes URLs in any format including:
        - http:// and https:// URLs
        - www. URLs
        - ftp:// URLs
        - URLs in parentheses like (http://example.com)
        - URLs in brackets like [http://example.com]
        
        Args:
            text: The text content to clean
            
        Returns:
            Text with all URLs removed
        """
        # Build patterns using the shared URL components to avoid duplication
        url_in_parens = r'\(\s*(?:' + URL_PROTOCOL + r')' + URL_CHARS + r'\s*\)'
        url_in_brackets = r'\[\s*(?:' + URL_PROTOCOL + r')' + URL_CHARS + r'\s*\]'
        
        # First remove URLs that are enclosed in parentheses or brackets
        # This handles patterns like "(https://example.com)" or "[http://example.com]"
        text = re.sub(url_in_parens, '', text, flags=re.IGNORECASE)
        text = re.sub(url_in_brackets, '', text, flags=re.IGNORECASE)
        
        # Then remove any remaining standalone URLs
        text = URL_PATTERN.sub('', text)
        
        # Clean up any leftover empty parentheses or brackets
        text = re.sub(r'\(\s*\)', '', text)  # Empty parentheses
        text = re.sub(r'\[\s*\]', '', text)  # Empty brackets
        
        # Clean up multiple spaces left by URL removal
        text = re.sub(r' {2,}', ' ', text)
        
        # Clean up lines that are now empty or only whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()

    def save_text(self, save_path: Path, request: HttpRequest) -> str:
        """
        Extract and save plain text content from the HTML document or XML feed.
        For HTML: Focuses on main content areas and removes all HTML markup.
        For XML: Extracts all text nodes including CDATA sections.
        Only creates a file if there is actual content.
        
        Args:
            save_path: Directory path to save the text file
            request: HttpRequest object for resolving relative URLs
            
        Returns:
            Extracted plain text string, or empty string if no content was found.
            When empty string is returned, no file is created.
        """
        if self.dom is None:
            return ""
        
        # Detect if we're dealing with XML content (RSS, Atom, etc.)
        # Check for XML structure more efficiently
        is_xml = (
            self.dom.name in ['xml', '[document]'] and 
            (self.dom.find('rss') or self.dom.find('feed') or self.dom.find('channel'))
        )
        
        if is_xml:
            # For XML/RSS/Atom feeds, extract all text content including CDATA
            print("📰 Extracting text from XML/RSS/Atom feed...")
            
            # Find items/entries in the feed
            items = self.dom.find_all('item') or self.dom.find_all('entry')
            
            text_parts = []
            if items:
                # Extract text from each item/entry
                for item in items:
                    # Find text-containing elements within each item
                    for tag_name in ['title', 'description', 'summary', 'content', 'content:encoded']:
                        elem = item.find(tag_name)
                        if elem:
                            elem_text = elem.get_text(strip=True)
                            # If the text contains HTML tags, parse them to extract clean text
                            if '<' in elem_text and '>' in elem_text:
                                try:
                                    elem_soup = BeautifulSoup(elem_text, 'html.parser')
                                    elem_text = elem_soup.get_text(separator=' ', strip=True)
                                except Exception:
                                    # If parsing fails, use original text
                                    pass
                            if elem_text:
                                text_parts.append(elem_text)
                
                text = '\n\n'.join(text_parts)
            else:
                # No items/entries found, extract all text
                text = self.dom.get_text(separator='\n', strip=True)
        else:
            # Standard HTML processing
            # Clone the DOM to avoid modifying the original
            text_dom = BeautifulSoup(str(self.dom), 'html.parser')
            
            # Remove all non-content elements
            for element in text_dom(EXCLUDED_ELEMENTS):
                element.decompose()
            
            # Find main content area
            main_content = None
            for selector in CONTENT_SELECTORS:
                main_content = text_dom.select_one(selector)
                if main_content:
                    break
            
            # Fallback to body or entire document
            if main_content is None:
                main_content = text_dom.body if text_dom.body else text_dom
            
            # Filter out navigation and UI elements
            self._filter_navigation_and_ui_elements(main_content)
            
            # Remove links but keep link text (text-only mode: no URLs)
            for link in main_content.find_all('a'):
                link_text = link.get_text(strip=True)
                link.replace_with(link_text if link_text else '')
            
            if self.preserve_structure:
                # Keep basic structure with line breaks for headings and paragraphs
                text_parts = []
                for element in main_content.descendants:
                    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        text_parts.append(f"\n\n{'#' * int(element.name[1])} {element.get_text(strip=True)}\n")
                    elif element.name == 'p':
                        text_parts.append(f"\n{element.get_text(strip=True)}\n")
                    elif element.name in ['li']:
                        text_parts.append(f"• {element.get_text(strip=True)}\n")
                text = ''.join(text_parts)
            else:
                # Extract plain text with spacing between elements
                text = main_content.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace and blank lines
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        text = text.strip()
        
        # Remove all URLs from the text content
        text = self._remove_urls_from_text(text)
        
        # Only create file if there is actual content
        if not text:
            print("⚠️  No text content found - skipping file creation")
            return ""
        
        # Generate unique filename based on content hash
        filename = self._generate_content_filename(text)
        
        # Ensure the save directory exists
        if not save_path.exists():
            save_path.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        text_file = save_path.joinpath(filename)
        text_file.write_text(text, encoding='utf-8')
        print(f"💾 Saved plain text content: {text_file}")
        print(f"📊 Extracted {len(text)} characters")
        
        return text

    def save_cleaned_html(self, save_path: Path, request: HttpRequest):
        """
        Save a cleaned version of the HTML with only main content and media,
        removing all scripts, stylesheets, and non-content elements.
        
        Args:
            save_path: Directory path to save the HTML file
            request: HttpRequest object for generating unique filename
        """
        if self.dom is None:
            return
        
        # Clone the DOM to avoid modifying the original
        cleaned_dom = BeautifulSoup(str(self.dom), 'html.parser')
        
        # Remove all non-content elements
        for element in cleaned_dom(EXCLUDED_ELEMENTS):
            element.decompose()
        
        # Remove <link> tags (stylesheets, fonts, etc.)
        for link in cleaned_dom.find_all('link'):
            link.decompose()
        
        # Find and extract only main content
        main_content = None
        for selector in CONTENT_SELECTORS:
            main_content = cleaned_dom.select_one(selector)
            if main_content:
                break
        
        if main_content:
            # Create a new minimal HTML structure with only the main content
            new_html = cleaned_dom.new_tag('html')
            new_head = cleaned_dom.new_tag('head')
            new_title = cleaned_dom.new_tag('title')
            new_title.string = cleaned_dom.title.string if cleaned_dom.title else "Extracted Content"
            new_head.append(new_title)
            new_html.append(new_head)
            
            new_body = cleaned_dom.new_tag('body')
            new_body.append(main_content)
            new_html.append(new_body)
            
            cleaned_dom = BeautifulSoup(str(new_html), 'html.parser')
        
        # Generate unique filename based on URL (same logic as text content, but .html)
        text_filename = self._generate_content_filename(request)
        html_filename = text_filename.replace('_content.txt', '_content.html')
        
        # Save cleaned HTML
        html_file = save_path.joinpath(html_filename)
        html_file.write_bytes(cleaned_dom.prettify(encoding='utf-8'))
        print(f"💾 Saved cleaned HTML: {html_file}")

    def store_media(self, source: DocumentSource, save_path: Path, request: HttpRequest) -> None:
        """
        Download and save a media file (image, video, or audio) to disk.
        
        Args:
            source: DocumentSource object containing the media URL and type
            save_path: Directory path to save the media file
            request: HttpRequest object for inheriting SSL settings
        """
        # Create a new request for the media file
        req = HttpRequest(
            source.url, 
            time_out=self.timeout, 
            verify_ssl=self.verify_ssl, 
            ssl_context=self.ssl_context,
            fetch_html_only=False  # Allow fetching media files
        )
        
        retry_count = 0
        
        while retry_count < MAX_RETRIES:
            try:
                res = req.get()

                # Skip 404 errors - no point retrying
                if res.status == 404:
                    print(f"⚠️  Not found (404): {source.url}")
                    break
                
                if res.status != 200:
                    print(f"⚠️  HTTP {res.status}: {source.url}")
                    break
                
                content = res.read()

                # Determine subdirectory based on media type
                if source.type == SourceType.img:
                    subdir = 'images'
                elif source.type == SourceType.video:
                    subdir = 'videos'
                elif source.type == SourceType.audio:
                    subdir = 'audio'
                else:
                    subdir = 'media'

                # Extract filename from URL path
                local_path = Path(req.url.path[1:]) if req.url.path[1:] else Path('unnamed')
                local_path = Path(subdir, local_path.name)
                
                # Ensure the file has an extension
                if local_path.suffix:
                    full_path = save_path.joinpath(local_path)
                    
                    # Create parent directories if needed
                    if not full_path.parent.exists():
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Save the media file
                    full_path.write_bytes(content)
                    print(f"  ✓ {local_path}")
                
                break  # Success, exit retry loop
                
            except NETWORK_EXCEPTIONS as e:
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    print(f"  ⚠️  Network error for {source.url}, retrying ({retry_count}/{MAX_RETRIES})...")
                    sleep(RETRY_DELAY_SECONDS)
                else:
                    print(f"  ❌ Failed after {MAX_RETRIES} attempts: {source.url}")
                    break
