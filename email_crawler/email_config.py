import re
import utils

num_of_process = 8
max_email = 5
max_number = 5
retry_budget = 5
keywords = ["kontak", "contact", "contacts", "email", "e-mail", "about", "abouts", "profile",
            "informasi", "hubungi", "iklan", "redaksi", "tentang", "advertise", "privacy-policy"]
secondary_keywords = ['advertise']
black_list_email = ['abuse', 'onlinenic', 'ytcvn', 'publicdomainregistry', 'enom', 'privacyprotect',
                    'domaindataguard', 'tucows', 'masterweb', 'resellercamp', 'webnic', 'protect',
                    'whoisguard', 'yoursite', 'gif', 'png', 'example', 'jpg', 'tiff', 'jpeg',
                    'domaindiscreet', 'domain', 'remove', 'this', 'whois', 'err', 'kominfo',
                    'adsense', 'ad-sense', 'kementrian', 'privacy', 'godaddy', 'port43', 'email.com']
url_regex = re.compile(r'^(?:http|ftp)s?://'
                        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
                        r'localhost|'
                        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                        r'(?::\d+)?'
                        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
phone_number_regex = r'(?:\+\d{2}\s+?[\s.-])?\(?\d+\)?(?:[\s-]+)\d{3}(?:[\s-]+)\d+|' \
                     r'\(\d+\)\s+?\d+|' \
                     r'\+62\s+?\d+\s+\d+'
whois_number_regex = r'(?:\+\d{1,2}[\s.-])?\(?\d+\)?[\s.-]?\d{3}[\s.-]?\d+'
whois_phone_validation_regex = r'(?:Admin|Registrant|Tech) phone:.*\n'
email_regex = r"[a-zA-Z0-9.\-+_]+\s*(?:@|[\[(<{]at[\])>}])\s*[a-zA-Z0-9.\-+_]+\.[a-zA-Z]+"
domain_name_regex = 'https?://(?:.*\.)?([a-zA-Z0-9]{4,})\..*'


def get_keyword_regex():
    keywords_pattern = utils.Utility.mk_string(keywords, ".*", ".*|.*", ".*")
    return re.compile(keywords_pattern)


def get_blacklist_regex():
    blacklists_pattern = utils.Utility.mk_string(black_list_email, ".*", ".*|.*", ".*")
    return re.compile(blacklists_pattern)