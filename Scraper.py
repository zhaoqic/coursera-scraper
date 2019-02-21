import selenium.webdriver
import time
import os
import json

from fake_useragent import UserAgent

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

from utils import AllEC


class Scraper(object):
    """
    Wrapper for selenium Chrome driver with methods to scroll through a page and
    to scrape and parse info from a linkedin page

    Params:
        - cookie {str}: li_at session cookie required to scrape linkedin profiles
        - driver {webdriver}: driver to be used for scraping
        - scroll_pause {float}: amount of time to pause (s) while incrementally
        scrolling through the page
        - scroll_increment {int}: pixel increment for scrolling
        - timeout {float}: time to wait for page to load first batch of async content
    """

    def __init__(self, scroll_pause=0.1, scroll_increment=300, timeout=10):
        self.driver = self.set_driver()
        self.scroll_pause = scroll_pause
        self.scroll_increment = scroll_increment
        self.timeout = timeout
        self.driver.set_window_size(1920, 1080)

    def set_driver(self):
        self.visit_count = 0
        ua = UserAgent(verify_ssl=False)
        options = Options()
        options.add_argument(f'user-agent={ua.chrome}')
        return selenium.webdriver.Chrome(chrome_options=options)
         

    def scrape(self, url):
        raise NotImplementedError

    def scroll_to_bottom(self):
        """Scroll to the bottom of the page

        Params:
            - scroll_pause_time {float}: time to wait (s) between page scroll increments
            - scroll_increment {int}: increment size of page scrolls (pixels)
        """
        current_height = 0
        while True:
            # Scroll down to bottom
            new_height = self.driver.execute_script(
                f"return Math.min({current_height + self.scroll_increment}, document.body.scrollHeight)")
            if (new_height == current_height):
                break
            self.driver.execute_script(
                f"window.scrollTo(0, Math.min({new_height}, document.body.scrollHeight));")
            current_height = new_height
            # Wait to load page
            time.sleep(self.scroll_pause)

    def wait(self, condition):
        return WebDriverWait(self.driver, self.timeout).until(condition)

    def wait_for_el(self, selector):
        return self.wait(EC.presence_of_element_located((
            By.CSS_SELECTOR, selector
        )))

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.quit()

    def quit(self):
        if self.driver:
            self.driver.quit()

class CourseScraper(Scraper):
    def __init__(self, save_html=True, save_json=True, **kwargs):
        super().__init__(**kwargs)

        self.save_html = save_html
        if self.save_html:
            os.makedirs('./course/html', exist_ok=True)
        
        self.save_json = save_json
        if self.save_json:
            os.makedirs('./course/json', exist_ok=True)

    def load_page(self, url):
        """Load profile page and all async content

        Params:
            - url {str}: url of the profile to be loaded
        Raises:
            ValueError: If link doesn't match a typical profile url
        """
        if 'coursera.org/learn/' not in url:
            raise ValueError(
                "Url must look like... coursera.org/learn/[course]")

        self.driver.get(url)
        # Wait for page to load dynamically via javascript
        try:
            WebDriverWait(self.driver, self.timeout).until(AllEC(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div.AboutCourse')),
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div.Syllabus')),
                #EC.presence_of_element_located(
                #    (By.CSS_SELECTOR, 'div.CourseReviewOverview')),
            ))
        except TimeoutException:
            raise ValueError("Took too long to load page.")

    def get_html(self, url):
        self.driver.execute_script(
        """
        {
            const xpathExpression = "//button/span[contains(.,'Show More')]";
            const button = document.evaluate(xpathExpression, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (button) {
                button.click(); 
            }
        }
        """)
        self.scroll_to_bottom()
        return self.driver.page_source

    def scrape(self, url):
        name =  url.replace('https://www.coursera.org/learn/', "")
        self.load_page(url)

        self.visit_count += 1
        if self.visit_count % 10 == 0:
            self.driver.quit()
            self.driver = self.set_driver()

        if self.save_html:
            html = self.get_html(url)
            f_html = f'./course/html/{name}.html'
            with open(f_html, 'w') as f:
                f.write(html)
            print(f'{name} - html saved.')
            
        if self.save_json:
            obj = {
                'name': name,
                'url': url,
                'profile': self.get_course_profile()
            }
            f_json = f'./course/json/{name}.json'
            with open(f_json, 'w') as f:
                json.dump(obj, f)  
            print(f'{name} - json saved.')


    def get_course_profile(self):
        return self.driver.execute_script("""
        {
            const profile = {
                title: document.querySelector('.BannerTitle>h1').textContent,
                partner: document.querySelector("div[class^='partnerBanner'] img").getAttribute('alt'),
                content: document.querySelector('.about-section>.content').innerText,

                skills: Array.from(document.querySelectorAll('.Skills>div>span')).map(x => x.innerText),
                glance: Array.from(document.querySelectorAll('.ProductGlance h4')).map(x => x.innerText),

                nweeks: document.querySelectorAll('.SyllabusWeek').length,
                instructors: Array.from(document.querySelectorAll('.Instructors h3>a')).map(x => (
                    {
                        name: x.innerText,
                        url: x.href
                    }
                )),
            }

            if (document.querySelector("div[class^='StarRating']")) {
                profile.rating = {
                    starrating: document.querySelector("div[class^='StarRating']~span").innerText,
                    nratings: document.querySelector("div[class^='StarRating']~div").innerText,
                    nreviews: document.querySelector(".CourseRating:last-child span").innerText,
                };
            }
            
            return profile;
        }
        """)
        

class ReviewScraper(Scraper):
    def __init__(self, save_html=True, save_json=True, **kwargs):
        super().__init__(**kwargs)

        self.save_html = save_html
        if self.save_html:
            os.makedirs('./review/html', exist_ok=True)
        
        self.save_json = save_json
        if self.save_json:
            os.makedirs('./review/json', exist_ok=True)

    def load_page(self, url):
        """Load profile page and all async content

        Params:
            - url {str}: url of the profile to be loaded
        Raises:
            ValueError: If link doesn't match a typical profile url
        """
        if 'coursera.org/learn/' not in url or not url.endswith('/reviews'):
            raise ValueError(
                "Url must look like... coursera.org/learn/[course]/reviews")

        self.driver.get(url)
        # Wait for page to load dynamically via javascript
        try:
            WebDriverWait(self.driver, self.timeout).until(AllEC(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div.rc-TopRatings')),
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div.rc-ReviewsSection')),
            ))
        except TimeoutException:
            raise ValueError("Took too long to load page.")
        
        self.driver.execute_script("""
        {
            const query = "nav[aria-label='Pagination Controls'] li:nth-last-child(2)>button";
            const lastPageButton = document.querySelector(query);
            if (lastPageButton) lastPageButton.click();
        }
        """)

    def get_html(self, url):
        self.load_page(url)
        return self.driver.page_source

    def scrape(self, url):
        name =  url.replace('https://www.coursera.org/learn/', "").replace('/reviews', "")
        self.load_page(url)

        self.visit_count += 1
        if self.visit_count % 10 == 0:
            self.driver.quit()
            self.driver = self.set_driver()

        if self.save_html:
            html = self.get_html(url)
            f_html = f'./review/html/{name}.html'
            with open(f_html, 'w') as f:
                f.write(html)
            print(f'[{self.visit_count:04d}]{name} - html saved.')
            
        if self.save_json:
            obj = {
                'name': name,
                'url': url,
                'profile': self.get_review_profile()
            }
            f_json = f'./review/json/{name}.json'
            with open(f_json, 'w') as f:
                json.dump(obj, f)  
            print(f'[{self.visit_count:04d}]{name} - json saved.')


    def get_review_profile(self):
        self.wait_for_el(".rc-ReviewsSection .review:last-child .dateOfReview")
        return self.driver.execute_script(
        """
        {
            const reviewProfile = {
                title: document.querySelector(".CourseReviewTitle h1").textContent,
                first_comment_date: document.querySelector('.rc-ReviewsSection .review:last-child .dateOfReview').textContent,
            };

            const topRatings = document.querySelectorAll(".rc-TopRatings div[class^='Col']");
            if (topRatings) {
                reviewProfile.top_ratings = Array.from(topRatings).map(x => ({
                    author: x.querySelector('.text-secondary:nth-child(2)').textContent,
                    date: x.querySelector('.text-secondary:nth-child(3)').textContent,
                    review: x.querySelector(':scope > p').textContent,
                }));
            }

            const courseRating = document.querySelector(".CourseRating");
            if (courseRating) {
                reviewProfile.rating = ({
                    starrating: courseRating.querySelector("div[class^='StarRating']~span").textContent,
                    nratings: courseRating.querySelector("div[class^='StarRating']~div").textContent,
                    nreviews: courseRating.querySelector(":scope>div:last-child span").textContent,
                });
            }

            return reviewProfile
        }
        """)


        