from setuptools import setup, find_packages

setup(
    name="DeepScrape",
    version="0.21",
    packages=find_packages(),
    install_requires=[
        "selenium",
        "webdriver-manager"
    ],
    author="D3-4D",
    description="Allows for free DeepAI API usage through web scraping with Selenium.",
    license="MIT",
    url="https://github.com/D3-4D/DeepScrape",
)
