# Copy me to config.py and edit config.py before running Wikiwatcher.

# External imports
from peewee import SqliteDatabase


class WikiConfig:
    """
    Used to configure the MediaWiki API URL as well as the User for logging in,
    if necessary.
    """
    site = 'http://example.com/wiki/api.php'
    login = {'username': 'BenderBendingRodriguez',
             'password': 'PleaseInsertGirder'}


class DatabaseConfig:
    """Sets the database storage for scraped objects."""
    peewee_db = SqliteDatabase('wikidata.db')
