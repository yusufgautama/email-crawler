import re, logging, signal
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import requests
from utils import Utility
import email_config as cfg
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

POSSIBLE_POSITION = ['on_page', 'on_link']


class EmailCrawler(object):

    def __init__(self):
        self.init_logger()
        self.driver = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._close()

    def _close(self):
        if self.driver:
            self.driver.service.process.send_signal(signal.SIGTERM)
            self.driver.quit()
            self.driver = None
            self.display = None

    def init_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        logger_handler = logging.FileHandler('email_crawler.log')
        logger_handler.setLevel(logging.DEBUG)
        logger_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        logger_handler.setFormatter(logger_formatter)
        self.logger.addHandler(logger_handler)

    def check_driver(self):
        if self.driver is None:
            self._start()

    def _start(self):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = (
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36"
        )
        service_args = [
            '--load-images=no',
            '--ignore-ssl-errors=true',
            '--cookies-file=/cookies.txt'
        ]
        self.driver = webdriver.PhantomJS(desired_capabilities=dcap, service_args=service_args)
        self.driver.set_window_size(1366, 768)
        self.driver.implicitly_wait(5)
        self.driver.set_page_load_timeout(60)

    def _go_to_page(self, url, _retry=cfg.retry_budget):
        print str("Navigate to %s" % url)
        if _retry == 0:
            raise Exception
        try:
            self.driver.get(url)
        except Exception, e:
            retry_num = cfg.retry_budget - (_retry - 1)
            self.logger.error("Error on domain {} retrying... {}, message: {}"
                              .format(url, retry_num, str(e)))
            self._go_to_page(url, _retry - 1)

    def search_email_in_domain(self, domain):
        self.check_driver()
        try:
            self._go_to_page(domain)
            soup = BS(self.driver.page_source, "lxml")
            # Find email on page and on link
            _email_founds = []
            for pos in POSSIBLE_POSITION:
                action_list = {'on_page': self._on_page,
                               'on_link': self._on_link}
                email = action_list.get(pos)(soup, domain)
                _email_founds.append(email)
            email_candidates = Utility.flatten_list(_email_founds)
            if str(domain).endswith('.id') or str(domain).endswith('.id/'):
                emails = self.search_id_domain(domain)
                if emails not in email_candidates:
                    email_candidates += emails
            if not email_candidates:
                # If email not found
                self.logger.info('Email not found on domain %s', domain)
                # Find it using whois
                return []
            else:
                # If email found, filter it
                final_candidates = self._filter_email_candidates(email_candidates)
                return self.sort_email(final_candidates, domain)
        except Exception as exc:
            print "Error on domain {} {} ".format(domain, str(exc))
            return []

    def _on_page(self, page, domain):
        self.logger.info("Searching email address on page")
        clean_html = Utility.clean_html(str(page))
        emails = re.findall(cfg.email_regex, clean_html, re.I)
        if emails:
            emails = map(Utility.normalize_email, emails)
        return emails

    def _on_link(self, page, domain):
        self.logger.info("Search email address on link to another page")
        _email_founds = []
        # Find all possible link element
        links = page.findAll('a')
        # Find all candidate link with keyword on html page
        keyword_html_link = self._find_keyword_in_html_text(links)
        # Find all candidate link with keyword on url
        keyword_url_link = self._find_keyword_in_url(links, domain)
        # Merge the url result, remove duplicate url
        candidate_links = Utility.uniquify(keyword_html_link + keyword_url_link)
        # Check for invalid url and try to fix it
        invalid_url = [uri for uri in candidate_links if not cfg.url_regex.match(uri)]
        try_fix_invalid_url = map(lambda _uri: Utility.normalize_invalid_url(_uri, domain), invalid_url)
        # Filter invalid url
        candidate_links = candidate_links + try_fix_invalid_url
        candidate_links = Utility.uniquify([_uri for _uri in candidate_links if cfg.url_regex.match(_uri)])
        try:
            for link in candidate_links:
                self.logger.info("Go to next link: " + link)
                try:
                    self._go_to_page(link)
                except Exception, err:
                    print str(err)
                    continue
                soup = BS(self.driver.page_source, "lxml")
                email = self._on_page(soup, domain)
                _email_founds.append(email)
            return _email_founds if not _email_founds else Utility.flatten_list(_email_founds)
        except Exception, e:
            logging.error(str(e))
            return _email_founds if not _email_founds else Utility.flatten_list(_email_founds)

    def sort_email(self, emails, domain):
        # If this is not governor's domain, do not get any email candidate with .go.id domain name
        if '.go.id' not in domain:
            emails = [email for email in emails if '.go.id' not in emails]
        domain_name = Utility.find_domain_name(domain)
        emails = map(lambda email: (email, domain_name), emails)
        # Sort based on score descending
        emails.sort(cmp=lambda a, b: -1 if self.email_scoring(a) > self.email_scoring(b) else 0)
        emails = [x for x, y in emails]
        return emails[:cfg.max_email]

    @staticmethod
    def email_scoring(email_payload):
        email, domain_name = email_payload
        score = 0
        # If email contain domain name
        if domain_name in email:
            score = score + 1
        # If email domain is domain name
        if '@{}'.format(domain_name) in email:
            score = score + 1
        # Scored based on similarity using Levensthein distance
        score = score + (fuzz.ratio(domain_name, email) * 1.0 / 100)
        return score

    @staticmethod
    def _normalize(candidate):
        return str(candidate).lower().strip()

    def _normalize_elems(self, elems):
        return map(lambda elem: self._normalize(elem.get('href', '')), elems)

    @staticmethod
    def _is_contain_keyword(url):
        return cfg.get_keyword_regex().match(url)

    def _find_keyword_in_url(self, links, domain):
        # Get all url and normalize it
        normalized_links = self._normalize_elems(links)
        # Filter url that doesn't contain keyword
        candidate_links = \
            filter(lambda x:
                   self._is_contain_keyword(x.replace(Utility.find_domain_name(domain), '')), normalized_links)
        return candidate_links

    def _find_keyword_in_html_text(self, links):
        # Filter element that doesn't contain keyword
        candidate_links = filter(lambda x: self._is_contain_keyword(self._normalize(x.getText())), links)
        # Get link from that element
        if candidate_links:
            candidate_links = self._normalize_elems(candidate_links)
        return candidate_links

    def _is_contain_domain(self, domain, email):
        email_domain = Utility.find_email_domain(email)
        return email_domain in domain if email_domain else False

    @staticmethod
    def _filter_email_candidates(candidates):
        # Remove duplicate element
        candidates = Utility.uniquify(map(lambda email: str(email).strip().lower(), [] if not candidates else candidates))
        # Filter email that contain blacklist word
        candidates = filter(lambda email: not re.match(cfg.get_blacklist_regex(), email), candidates)
        # Filter short email
        candidates = [candidate for candidate in candidates if len(candidate) > 5]
        # Filter email that contain newline and space
        candidates = [candidate for candidate in candidates if '\n' not in candidate and ' ' not in candidate
                      and '\t' not in candidate]
        return candidates

    def search_id_domain(self, domain):
        try:
            pandi = "https://pandi.id/whois/"
            headers = {'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 "
                                     "(KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36"}
            data = {'domain': domain}
            html = requests.post(url=pandi, data=data, headers=headers)
            soup = BS(html.content, "lxml")
            emails = self._on_page(soup.text, domain)
            candidates = self._filter_email_candidates(emails)
            return candidates
        except Exception as e:
            logging.error(str(e))


def init_parser(parser):
    parser.add_argument('--url', type=str, help='The input url for crawl starting point.')
    return parser.parse_args()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    args = init_parser(parser)
    with EmailCrawler() as crawler:
        emails = crawler.search_email_in_domain(args.url)
        print(str(emails))