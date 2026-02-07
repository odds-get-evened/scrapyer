from enum import Enum


class SourceType(Enum):
    js = 1
    css = 2
    img = 3

class DocumentSource:
    def __init__(self, t: SourceType, u: str):
        self.type = t
        self.url = u

    def __str__(self):
        return f"type: {self.type.name}; url: {self.url}"