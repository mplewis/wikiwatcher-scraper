import config
from scraper import scrape_mediawiki
from time import sleep


while True:
    interval = config.ScraperConfig.scrape_interval
    scrape_mediawiki()
    print 'Waiting %s seconds...' % interval
    sleep(interval)
