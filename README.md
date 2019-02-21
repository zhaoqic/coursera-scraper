# Coursera Scraper

A naïve Python script to scrape the course profiles and top reviews on Coursera.

## Dependency

Run `pip install -r requirements.txt` to install required libraries.

Run `brew cask install chromedriver` (macOS users) or `sudo apt-get install chromium-chromedriver` (Ubuntu users) to install chromedriver.

Google Chrome or Chromium is required. 

## Usage

First, download sitemaps from Coursera

```
mkdir -p sitemap
curl -o ./sitemap/courses.xml https://www.coursera.org/sitemap~www~courses.xml
curl -o ./sitemap/courses-reviews.xml https://www.coursera.org/sitemap~www~course-reviews.xml
```

Second, specify the type of data (profile and / or review) you want to download in `main.py`.

Run `python main.py`.
