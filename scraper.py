# From [config.py](config.html).
import config
# From [models.py](models.html).
from models import User, Page, Change

# External imports
from wikitools import wiki, api, APIError
from peewee import DoesNotExist
from isodate.isodatetime import parse_datetime as parse_iso_dt


def request(params):
    """Requests data from the MediaWiki API and returns the API response."""
    site_url = config.WikiConfig.site
    site = wiki.Wiki(site_url)
    # `while True` makes this act like a do...while loop to ensure login on
    # failure.
    while True:
        # Perform the request if possible.
        try:
            return api.APIRequest(site, params).query()
        # `APIError` with arg[0] of `readapidenied` indicates the user
        # needs to be logged in first. Attempt to log in once, then redo the
        # request. On failure, raise the exception again.
        except APIError, e:
            # We can't handle non-`readapidenied` errors.
            if e.args[0] != 'readapidenied':
                raise e
            username = config.WikiConfig.login['username']
            print('Logging in as %s...' % username),
            if site.login(**config.WikiConfig.login):
                print 'done.'
            else:
                print 'failed.'
                raise e


def get_raw_page_by_id(page_id):
    """
    Request a page from the MediaWiki API using a page ID and
    return the raw API response.
    """
    action = {'action': 'query',
              'pageids': page_id,
              'prop': 'info',
              'inprop': 'pageid|title|url'}
    data = request(action)['query']['pages']
    if not str(page_id) in data:
        raise KeyError('Page with ID %s not found' % page_id)
    return data[str(page_id)]


def get_raw_user_by_username(username):
    """
    Request a user from the MediaWiki API using a username and
    return the raw API response.
    """
    action = {'action': 'query',
              'list': 'users',
              'ususers': username}
    data = request(action)['query']['users']
    for result in data:
        if result['name'] == username:
            if 'missing' in result:
                raise KeyError('User with username %s not found' % username)
            return result
        raise KeyError('User with username %s not found' % username)


def get_page_object(page_id):
    """
    Retrieves a Page from a given page ID, getting page data from
    the API and saving the Page if it doesn't already exist in the DB.
    """
    try:
        return Page.get(Page.page_id == page_id)
    except DoesNotExist:
        data = get_raw_page_by_id(page_id)
        return Page.create(page_id=data['pageid'],
                           page_title=data['title'],
                           page_url=data['fullurl'])


def get_user_object(username):
    """
    Retrieves a User from a given username, getting user data from
    the API and saving the User if it doesn't already exist in the DB.
    """
    try:
        return User.get(User.username == username)
    except DoesNotExist:
        data = get_raw_user_by_username(username)
        return User.create(username=data['name'],
                           user_id=data['userid'])


def get_change_object(change):
    """
    Retrieves a Change from a given change API object, getting user data from
    the API and saving the User if it doesn't already exist in the DB.
    """
    try:
        return Change.get(Change.change_id == change['rcid'])
    except DoesNotExist:
        size_diff = change['newlen'] - change['oldlen']
        timestamp_dt = parse_iso_dt(change['timestamp'])
        return Change.create(change_id=change['rcid'],
                             change_type=change['type'],
                             user=get_user_object(change['user']),
                             timestamp=timestamp_dt,
                             page=get_page_object(change['pageid']),
                             comment=change['comment'],
                             size_diff=size_diff)


def scrape_mediawiki():
    """Scrape MediaWiki for new changes and save them to the database."""
    # Create DB tables if they don't already exist.
    User.create_table(fail_silently=True)
    Page.create_table(fail_silently=True)
    Change.create_table(fail_silently=True)

    # Parse changes from the MediaWiki API.
    print 'Parsing recent changes from MediaWiki API.'
    # Properties to request from the MediaWiki API.
    recent_changes_props = ['user', 'ids', 'title', 'comment', 'sizes',
                            'timestamp']
    # `rctype` specifies that we only want new page and edit page events.
    recent_changes_action = {'action': 'query',
                             'list': 'recentchanges',
                             'rctype': 'new|edit',
                             'rcprop': '|'.join(recent_changes_props)}
    new_changes = []
    req_num = 1
    while True:
        print 'Request %s' % req_num
        # Make the API request.
        resp = request(recent_changes_action)
        # Parse the response data.
        resp_data = resp['query']['recentchanges']
        req_num += 1
        # `changes_exist` is a flag that lets us break out of the double loop.
        changes_exist = False
        for resp_item in resp_data:
            change_id = resp_item['rcid']
            try:
                # `Change.get` either returns a `Change` object if one exists
                # for `change_id` or raises a `DoesNotExist` exception if a
                # `Change` object does not exist.
                Change.get(Change.change_id == change_id)
                # If we've gotten this far, a `DoesNotExist` exception has not
                # been raised, so the `Change` object exists for `change_id`.
                # Set the breakout flag and break out of the inner loop.
                changes_exist = True
                break
            # We're expecting the exception if a `Change` object does not
            # already exist in the DB for the given change. Ignore it.
            except DoesNotExist:
                # Append the response data to the existing data.
                new_changes.append(resp_item)
        # Two conditions break the continuing `recentchanges` request loop:
        #
        # * Reaching changes that exist in the DB
        # * Reaching the end of data, indicated by receiving data that doesn't
        # contain the `query-continue` key
        if changes_exist:
            print 'Reached changes that already exist in DB.'
            break
        if not 'query-continue' in resp:
            print 'No more query-continue; reached end of data.'
            break
        # The request loop hasn't been broken, and the data contains a
        # `query-continue` key. Use it to request the next page of data.
        next_start_point = resp['query-continue']['recentchanges']['rcstart']
        recent_changes_action['rcstart'] = next_start_point
        print '    query-continue: %s' % recent_changes_action['rcstart']
    # Done!
    print 'Done scraping.'

    # Add all User objects to the DB if they don't already exist.
    usernames = {change['user'] for change in new_changes}
    print('Verifying %s users...' % len(usernames)),
    for username in usernames:
        get_user_object(username)
    print 'done.'

    # Add all Page objects to the DB if they don't already exist.
    page_ids = {change['pageid'] for change in new_changes}
    print('Verifying %s pages...' % len(page_ids)),
    for page_id in page_ids:
        get_page_object(page_id)
    print 'done.'

    # Add all new Change objects to the DB.
    print('Verifying %s changes...' % len(new_changes)),
    for change in new_changes:
        get_change_object(change)
    print 'done.'

    print 'Finished!'

if __name__ == '__main__':
    scrape_mediawiki()
