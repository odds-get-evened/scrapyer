import re
import socket
import ssl
from pathlib import Path
from time import sleep

from bs4 import BeautifulSoup

from scrapyer.docusource import DocumentSource, SourceType
from scrapyer.httprequest import HttpRequest


# Network exceptions that should trigger retries
NETWORK_EXCEPTIONS = (TimeoutError, socket.gaierror, ssl.SSLError, ConnectionError, OSError)


class DocumentProcessor:
    def __init__(self, req: HttpRequest, p: Path):
        self.dom: BeautifulSoup = None
        self.is_processing: bool = False
        self.save_path: Path = p

        self.sources: list[DocumentSource] = []
        
        self.request: HttpRequest = req

        # create storage path
        self.create_paths()

    def start(self):
        self.is_processing = True

        while self.is_processing is True:
            try:
                response = self.request.get()
                self.dom = BeautifulSoup(response.read(), 'html.parser')
                print(f"status: {response.status} {response.reason}")

                # save source files to storage directory
                self.pop_sources()
            except NETWORK_EXCEPTIONS as e:
                sleep(self.request.timeout)
                continue

            self.is_processing = False

        [self.store_url(source) for source in self.sources]

        self.save_html()

    def save_html(self):
        html_file = self.save_path.joinpath('index.html')
        if not html_file.exists():
            html_file.write_bytes(self.dom.prettify(encoding='utf-8'))

        self.localize_html()

    def save_text(self) -> str:
        """
        Extracts plain text content from the HTML document.
        Focuses on main content areas and preserves link URLs in readable format.
        Returns plain text string without HTML markup.
        """
        if self.dom is None:
            return ""
        
        # remove script and style elements from parsing
        for element in self.dom(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # try to find main content area (common patterns)
        main_content = None
        content_selectors = ['main', 'article', '[role="main"]', '.content', '#content', '.main', '#main']
        
        for selector in content_selectors:
            main_content = self.dom.select_one(selector)
            if main_content:
                break
        
        # if no main content found, use body or entire document
        if main_content is None:
            main_content = self.dom.body if self.dom.body else self.dom
        
        # convert links to readable format: "link text (URL)"
        for link in main_content.find_all('a'):
            link_text = link.get_text(strip=True)
            href = link.get('href', '')
            if href:
                # make absolute URL if relative
                absolute_href = self.request.absolute_source(href)
                # replace link element with formatted text
                link.replace_with(f"{link_text} ({absolute_href})")
        
        # extract text with spacing between elements
        text = main_content.get_text(separator='\n', strip=True)
        
        # clean up excessive whitespace and blank lines
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # save to file
        text_file = self.save_path.joinpath('content.txt')
        text_file.write_text(text, encoding='utf-8')
        print("saved plain text content (content.txt)")
        
        return text

    def localize_html(self):
        html_file = self.save_path.joinpath('index.html')
        try:
            contents = html_file.read_bytes()
            html_text = contents.decode('utf-8', errors='ignore')

            # iterate thru all saved source files
            for p in self.save_path.rglob('*.*'):
                if p.suffix != '.html':
                    rel_path = p.relative_to(self.save_path)
                    # make slashes web friendly
                    rel_urlized = rel_path.as_posix()

                    # Create a safer regex pattern that escapes special characters
                    # re.escape ensures all special regex chars are properly escaped
                    escaped_path = re.escape(rel_urlized)
                    # Look for the path in attribute values (src, href, etc.)
                    # Pattern matches: attribute="...path..." where path might have absolute URL prefix
                    pattern = r'((?:src|href|data-src|data-href)=["\'])([^"\']*' + escaped_path + r')(["\'])'
                    
                    # Use re.sub with lambda to replace all occurrences with the local path
                    html_text = re.sub(pattern, lambda m: m.group(1) + rel_urlized + m.group(3), html_text, flags=re.IGNORECASE)
            
            # make content text to bytes
            revised = html_text.encode('utf-8')
            # remove old file
            html_file.unlink()
            html_file.write_bytes(revised)
            print("finalized document (index.html)")
        except Exception as e:
            print(f"Warning: Could not localize HTML: {e}")
            # If localization fails, at least we have the original HTML saved

    def create_paths(self) -> None:
        if not self.save_path.exists():
            self.save_path.mkdir(exist_ok=True, parents=True)

    def store_url(self, s: DocumentSource, parent_dirname = None) -> None:
        req = HttpRequest(s.url, time_out=self.request.timeout)
        
        # Retry logic for transient SSL/timeout errors
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                res = req.get()

                # don't bother with 404s
                # print(f"status: {res.status} url: {s.url}")
                if res.status != 404:
                    content = res.read()

                    local_path = Path(req.url.path[1:])
                    if parent_dirname is not None:
                        local_path = Path(parent_dirname, req.url.path[1:])

                    # has to have a file extension
                    if local_path.suffix != "":
                        local_path = self.save_path.joinpath(local_path)
                        if not local_path.exists():
                            try:
                                local_path.parent.mkdir(parents=True)
                            except FileExistsError as e:
                                pass
                        # store the files
                        print(f"stored: {local_path}")
                        local_path.write_bytes(content)
                break  # Success, exit retry loop
                
            except NETWORK_EXCEPTIONS as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Timeout/network error for {s.url}, retrying ({retry_count}/{max_retries})...")
                    # Use shorter delay for retries (5 seconds instead of full timeout)
                    sleep(5)
                else:
                    print(f"Failed to retrieve {s.url} after {max_retries} attempts: {e}")
                    break


    def pop_sources(self):
        script_tags = self.dom.find_all('script')
        link_tags = self.dom.find_all('link')
        img_tags = self.dom.find_all('img')

        # @todo scan css for img URLs

        # @todo find inline style and script tags, save as files, and remove tags from body

        for it in img_tags:
            try:
                img = self.request.absolute_source(it['src'])
                self.sources.append(DocumentSource(SourceType.img, img))
                # self.store_url(img, parent_dirname='images')
            except KeyError as e:
                # no src attribute found
                pass

        for st in script_tags:
            try:
                # `src` attribute present so get javascript file content of URL
                js = self.request.absolute_source(st['src'])
                self.sources.append(DocumentSource(SourceType.js, js))
                # self.store_url(js, parent_dirname='js')
            except KeyError as e:
                # src attribute was never found in script tags
                pass

        for lt in link_tags:
            try:
                lt['rel'].index('stylesheet')
                lh = self.request.absolute_source(lt['href'])
                self.sources.append(DocumentSource(SourceType.css, lh))
                # self.store_url(lh, parent_dirname='css')
            except ValueError as e:
                pass
