import sys
from pathlib import Path

from scrapyer.docuproc import DocumentProcessor
from scrapyer.httprequest import HttpRequest


def boot_up():
    try:
        url = sys.argv[1]
        print(f"URL: {url}")
        save_dir = sys.argv[2]
        save_path = Path(save_dir)
        print(f"Save path: {save_path}")

        request = HttpRequest(url)

        '''
        process content
        '''
        doc = DocumentProcessor(request, save_path)
        doc.start()
    except IndexError as e:
        print("1st and 2nd arguments required (e.g. scrapyer <url> <save path>)")
