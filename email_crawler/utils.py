import re
from url_normalize import url_normalize
import email_config as cfg


class Utility(object):
    @staticmethod
    def mk_string(collection, start='', sep=', ', end=''):
        ret = start
        for item in collection:
            ret = ret + str(item) + sep
        # Removing the last inserted separator.
        ret = ret[:len(ret) - len(sep)]
        return ret + end

    @staticmethod
    def uniquify(elements):
        return list(set(elements))

    @staticmethod
    def clean_html(raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, ' ', raw_html)
        return cleantext

    @staticmethod
    def find_domain_name(domain):
        match = re.match(cfg.domain_name_regex, domain)
        if match:
            match = str(match.group(1))
        else:
            match = ''
        return match

    @staticmethod
    def find_email_domain(email):
        email_domain = re.match('.*@([a-zA-Z0-9.\-+_]+)\.', email)
        return None if not email_domain else email_domain.group(1)

    @staticmethod
    def flatten_list(elements):
        return reduce(lambda x, y: x + y, elements)

    @staticmethod
    def normalize_url_domain(url):
        url = url_normalize(url)
        return str(url) if str(url).endswith('/') else str(url) + '/'

    @staticmethod
    def normalize_invalid_url(url, domain):
        return domain + (str(url)[1:] if str(url).startswith('/') else '/' + str(url))

    @staticmethod
    def filter_mobile_url(url):
        if str(url).startswith('http://m.') or str(url).startswith('https://m.'):
            return False
        else:
            return True

    @staticmethod
    def normalize_email(email):
        email = email.strip().replace(' ', '')
        return re.sub('[\[(<{]at[\])>}]', '@', email)