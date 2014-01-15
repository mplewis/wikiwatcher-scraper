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


class FlaskConfig:
    """Passed into the Flask app to set Flask settings."""
    DEBUG = True


class ScoringConfig:
    """Determines scores wiki users receive for their actions."""
    char_add_points = 3
    char_del_points = 1
    new_page_points = 500


class LayoutConfig:
    """Determines cosmetics in the rendered HTML."""
    min_score_bar_pct = 5
    min_char_bar_pct = 10
    num_recent_changes = 10
