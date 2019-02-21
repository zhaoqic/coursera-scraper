import xml.etree.ElementTree as ET
from tqdm import tqdm
from Scraper import CourseScraper, ReviewScraper

SCRAPE_COURSE = False
SCRAPE_REVIEW = True


if SCRAPE_COURSE:
    courses_xmlroot = ET.parse('sitemap/courses.xml').getroot()
    courses_urls = [url[0].text for url in courses_xmlroot]
    course_scraper = CourseScraper()
    for url in tqdm(courses_urls):
        try:
            course_scraper.scrape(url)
        except Exception as e:
            with open('course/error.log', 'a') as f_log:
                print(f'"{url}","{str(e)}"', file=f_log)

if SCRAPE_REVIEW:
    reviews_xmlroot = ET.parse('sitemap/courses-reviews.xml').getroot()
    reviews_urls = [url[0].text for url in reviews_xmlroot]
    review_scraper = ReviewScraper()
    
    for url in tqdm(reviews_urls):
        try:
            review_scraper.scrape(url)
        except Exception as e:
            with open('review/error.log', 'a') as f_log:
                print(f'"{url}","{str(e)}"', file=f_log)
