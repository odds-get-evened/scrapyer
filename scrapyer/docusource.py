from enum import Enum


class SourceType(Enum):
    """Enumeration of media types that can be extracted from web pages."""
    img = "image"        # Image files (jpg, png, gif, svg, etc.)
    video = "video"      # Video files (mp4, webm, etc.)
    audio = "audio"      # Audio files (mp3, wav, ogg, etc.)


class DocumentSource:
    """
    Represents a media resource found in a web page.
    Used to track and download images, videos, and audio files.
    """
    
    def __init__(self, source_type: SourceType, url: str):
        """
        Initialize a document source.
        
        Args:
            source_type: The type of media (image, video, or audio)
            url: The absolute URL of the media resource
        """
        self.type: SourceType = source_type
        self.url: str = url
    
    def __repr__(self):
        return f"DocumentSource(type={self.type.value}, url={self.url})"
