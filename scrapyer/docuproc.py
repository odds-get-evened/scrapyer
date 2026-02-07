import re
import socket
from pathlib import Path
from time import sleep

from bs4 import BeautifulSoup

from scrapyer.docusource import DocumentSource, SourceType
from scrapyer.httprequest import HttpRequest


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
            except TimeoutError | socket.gaierror as e:
                sleep(self.request.timeout)
                continue

            self.is_processing = False

        [self.store_url(source) for source in self.sources]

        self.save_html()

    def save_html(self):
        html_file = self.save_path.joinpath('index.html')
        if not html_file.exists():
            html_file.write_bytes(self.dom.prettify('utf8'))

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
        contents = html_file.read_bytes()
        html_text = contents.decode('utf8')

        # iterate thru all saved source files
        for p in self.save_path.rglob('*.*'):
            if p.suffix != '.html':
                rel_path = p.relative_to(self.save_path)
                # make slashes web friendly
                rel_urlized = rel_path.as_posix()

                for found in  re.finditer(r"<.*=\"(.*%s)\".*>$" % re.escape(rel_urlized), html_text, re.M):
                    orig = found.group(1)
                    html_text = re.sub(re.escape(orig), rel_urlized, html_text)
        # make content text to bytes
        revised = html_text.encode('utf8')
        # remove old file
        html_file.unlink()
        html_file.write_bytes(revised)
        print("finalized document (index.html)")

    def create_paths(self) -> None:
        if not self.save_path.exists():
            self.save_path.mkdir(exist_ok=True, parents=True)

    def store_url(self, s: DocumentSource, parent_dirname = None) -> None:
        req = HttpRequest(s.url, time_out=self.request.timeout)
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
