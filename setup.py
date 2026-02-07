from setuptools import setup, find_packages

setup(
    name="scrapyer",
    author="Chris Walsh",
    author_email="chris.is.rad@pm.me",
    classifiers=[],
    description="a web page scraper",
    license="MIT",
    version="0.0.1",
    url="https://github.com/mintaka5/scrapyer",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "aiohttp>=3.8.0",
    ],
    extras_require={
        "nlp": [
            "onnxruntime>=1.15.0",
            "transformers>=4.30.0",
            "numpy>=1.24.0",
            "torch>=2.0.0",
        ]
    },
    entry_points={
        'console_scripts': [
            'scrapyer = scrapyer.main:boot_up'
        ]
    }
)