# email_crawler
This is a simple crawler that can find emails from specified domain using selenium with phantomjs webdriver.

### Installing

Install the requirement package from requirements.txt.

```
pip install -r requirements.txt
```

You must define the probable keyword in email_config.py for the crawler to navigate next.

```
keywords = ["kontak", "contact", "contacts", "email", "e-mail", "about", "abouts", "profile",
            "informasi", "hubungi", "iklan", "redaksi", "tentang", "advertise", "privacy-policy"]
```

## Running

You can simply run it like this.

```
python email_crawler.py --url http://yoururl.com
```

## Authors

* **Yusuf Pradana Gautama** - [yusufgtm](https://github.com/yusufgautama)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
