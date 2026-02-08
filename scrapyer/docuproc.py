import re
import socket
import ssl
from pathlib import Path
from time import sleep
from typing import List

from bs4 import BeautifulSoup, Tag

from scrapyer.docusource import DocumentSource, SourceType
from scrapyer.httprequest import HttpRequest


# Network exceptions that should trigger retries
NETWORK_EXCEPTIONS = (TimeoutError, socket.gaierror, ssl.SSLError, ConnectionError, OSError)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# HTML elements to remove (non-content)
EXCLUDED_ELEMENTS = ['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript', 'iframe']

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


class DocumentProcessor:
    def __init__(self, req: HttpRequest, p: Path, 
                 strip_html: bool = True, 
                 preserve_structure: bool = False,
                 media_types: List[str] = None):
        """
        Initialize the document processor for extracting main content from web pages.
        
        Args:
            req: HttpRequest object configured with the target URL
            p: Path where extracted content should be saved
            strip_html: Remove all HTML tags and extract plain text (default: True)
            preserve_structure: Keep basic structure like headings and paragraphs (default: False)
            media_types: List of media types to extract (e.g., ['images', 'videos', 'audio'])
        """
        self.dom: BeautifulSoup = None
        self.is_processing: bool = False
        self.save_path: Path = p
        self.strip_html: bool = strip_html
        self.preserve_structure: bool = preserve_structure
        self.media_types: List[str] = media_types or ['images', 'videos', 'audio']
        
        # Store only media sources (no scripts or stylesheets)
        self.media_sources: list[DocumentSource] = []
        
        self.request: HttpRequest = req

        # Create storage directories
        self.create_paths()

    def start(self):
        """
        Main processing loop: fetch HTML, extract content and media, save to disk.
        """
        self.is_processing = True
        print("🌐 Fetching web page...")

        while self.is_processing is True:
            try:
                response = self.request.get()
                
                # Validate that we received HTML content
                content_type = response.getheader('Content-Type', '')
                if 'text/html' not in content_type.lower() and 'application/xhtml' not in content_type.lower():
                    print(f"⚠️  Warning: Response content type is '{content_type}', expected HTML")
                
                # Parse the HTML content
                self.dom = BeautifulSoup(response.read(), 'html.parser')
                print(f"✅ Status: {response.status} {response.reason}")

                # Extract media sources from the page (images, videos, audio)
                self.extract_media_sources()
                
            except NETWORK_EXCEPTIONS as e:
                print(f"❌ Network error: {e}")
                sleep(self.request.timeout)
                continue

            self.is_processing = False

        # Download all media files
        if self.media_sources:
            print(f"\n📥 Downloading {len(self.media_sources)} media files...")
            for source in self.media_sources:
                self.store_media(source)

        # Extract and save text content
        print("\n📝 Extracting text content...")
        self.save_text()
        
        # Optionally save cleaned HTML
        if not self.strip_html or self.preserve_structure:
            self.save_cleaned_html()
        
        print("\n✨ Processing complete!")

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

    def save_text(self) -> str:
        """
        Extract and save plain text content from the HTML document.
        Focuses on main content areas and removes all HTML markup.
        
        Returns:
            Extracted plain text string
        """
        if self.dom is None:
            return ""
        
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
        
        # Convert links to readable format: "link text (URL)"
        for link in main_content.find_all('a'):
            link_text = link.get_text(strip=True)
            href = link.get('href', '')
            if href and link_text:
                try:
                    absolute_href = self.request.absolute_source(href)
                    link.replace_with(f"{link_text} ({absolute_href})")
                except Exception:
                    link.replace_with(link_text)
        
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
        
        # Save to file
        text_file = self.save_path.joinpath('content.txt')
        text_file.write_text(text, encoding='utf-8')
        print(f"💾 Saved plain text content: {text_file}")
        print(f"📊 Extracted {len(text)} characters")
        
        return text

    def save_cleaned_html(self):
        """
        Save a cleaned version of the HTML with only main content and media,
        removing all scripts, stylesheets, and non-content elements.
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
        
        # Save cleaned HTML
        html_file = self.save_path.joinpath('content.html')
        html_file.write_bytes(cleaned_dom.prettify(encoding='utf-8'))
        print(f"💾 Saved cleaned HTML: {html_file}")

    def store_media(self, source: DocumentSource) -> None:
        """
        Download and save a media file (image, video, or audio) to disk.
        
        Args:
            source: DocumentSource object containing the media URL and type
        """
        # Create a new request for the media file
        req = HttpRequest(
            source.url, 
            time_out=self.request.timeout, 
            verify_ssl=self.request.verify_ssl, 
            ssl_context=self.request.ssl_context,
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
                    full_path = self.save_path.joinpath(local_path)
                    
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

    def create_paths(self) -> None:
        """Create the save directory and media subdirectories if they don't exist."""
        if not self.save_path.exists():
            self.save_path.mkdir(exist_ok=True, parents=True)
        
        # Create media subdirectories
        if 'images' in self.media_types:
            self.save_path.joinpath('images').mkdir(exist_ok=True)
        if 'videos' in self.media_types:
            self.save_path.joinpath('videos').mkdir(exist_ok=True)
        if 'audio' in self.media_types:
            self.save_path.joinpath('audio').mkdir(exist_ok=True)
