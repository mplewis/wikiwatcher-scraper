# From [config.py](config.html).
import config
from peewee import (Model, ForeignKeyField, DateTimeField, TextField,
                    IntegerField)


class BaseModel(Model):
    """Used to set up the database target for all models."""
    class Meta:
        database = config.DatabaseConfig.peewee_db


class User(BaseModel):
    """Represents a MediaWiki user."""
    user_id = TextField()
    username = TextField()


class Page(BaseModel):
    """Represents a MediaWiki page."""
    page_id = IntegerField()
    page_title = TextField()
    page_url = TextField()


class Change(BaseModel):
    """
    Represents a MediaWiki change (from Recent Changes, viewable at
    [Special:RecentChanges](http://www.mediawiki.org/wiki/Help:Recent_changes)
    or accessible
    [via the MediaWiki API](http://www.mediawiki.org/wiki/API:Recentchanges).)
    """
    change_id = IntegerField()
    change_type = TextField()
    user = ForeignKeyField(User, related_name='changes')
    timestamp = DateTimeField()
    page = ForeignKeyField(Page, related_name='changes')
    comment = TextField()
    size_diff = IntegerField()
