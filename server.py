import config
from models import User, Change

from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)
app.config.from_object(config.FlaskConfig)


def parse_datetime(datetime_str, timeago=True):
    date_obj = datetime.strptime(datetime_str.split('+')[0],
                                 '%Y-%m-%d %H:%M:%S')
    readable = date_obj.strftime('%Y-%m-%d at %I:%M %p')
    if not timeago:
        return readable
    iso_format = date_obj.strftime('%Y-%m-%dT%H:%M:%SZ')
    return ('<span class="timeago" title="%s">%s</span>' %
            (iso_format, readable))


def pct_from_ints(smaller, larger):
    return int(round(float(smaller) / larger * 100))


def calc_user_score(chars_add, chars_del, new_pages):
    scoring = config.ScoringConfig
    return (chars_add * scoring.char_add_points +
            chars_del * scoring.char_del_points +
            new_pages * scoring.new_page_points)


def all_users_edit_chars_pcts():
    """
    Get the following for all users:

    * added and deleted characters for all users' edits
    * scaled bar percent values for each user's characters added/deleted
    * the number of new pages created by each user
    * the number of points (the score) each user has, based on the scoring
      constants in config.ScoringConfig
    * scaled bar percent values for each user's score

    Return the results in a list with the following format:
    [{'username': 'PhilipJFry',
      'pos_chars': 42,
      'pos_chars_pct': 27,
      'neg_chars': 100,
      'neg_chars_pct': 94,
      'new_pages': 0,
      'score': 3000,
      'score_pct': 12},
      {...}, ...]
    """
    users = []
    chars_max = 0
    score_max = 0
    for user in User.select():
        username = user.username
        pos_chars = 0
        neg_chars = 0
        new_pages = 0
        for change in user.changes:
            diff = change.size_diff
            if diff >= 0:
                pos_chars += diff
            else:
                neg_chars -= diff
            if change.change_type == 'new':
                new_pages += 1
        score = calc_user_score(pos_chars, neg_chars, new_pages)
        users.append({'username': username,
                      'pos_chars': pos_chars,
                      'neg_chars': neg_chars,
                      'new_pages': new_pages,
                      'score': score})
        if pos_chars > chars_max:
            chars_max = pos_chars
        if neg_chars > chars_max:
            chars_max = neg_chars
        if score > score_max:
            score_max = score
    min_char_bar_dec = float(config.LayoutConfig.min_char_bar_pct) / 100
    min_score_bar_dec = float(config.LayoutConfig.min_score_bar_pct) / 100
    pos_chars_add = chars_max * min_char_bar_dec
    neg_chars_add = chars_max * min_char_bar_dec
    score_add = score_max * min_score_bar_dec
    for user_data in users:

        # Positive bar minimum sizing
        if user_data['pos_chars'] == chars_max:
            user_data['pos_chars_pct'] = 100
        else:
            pos_pct = pct_from_ints(user_data['pos_chars'] + pos_chars_add,
                                    chars_max + pos_chars_add)
            user_data['pos_chars_pct'] = pos_pct

        # Negative bar minimum sizing
        if user_data['neg_chars'] == chars_max:
            user_data['neg_chars_pct'] = 100
        else:
            neg_pct = pct_from_ints(user_data['neg_chars'] + neg_chars_add,
                                    chars_max + neg_chars_add)
            user_data['neg_chars_pct'] = neg_pct

        # Score bar minimum sizing
        if user_data['score'] == score_max:
            user_data['score_pct'] = 100
        else:
            score_pct = pct_from_ints(user_data['score'] + score_add,
                                      score_max + score_add)
            user_data['score_pct'] = score_pct

    # Sort the list by most points and return it.
    users.sort(key=lambda u: u['score'], reverse=True)
    return users


def get_recent_change_descs(num_changes=
                            config.LayoutConfig.num_recent_changes):
    changelog = []
    changes = (Change.select()
               .order_by(Change.timestamp.desc())
               .limit(num_changes))
    for change in changes:
        username = change.user.username
        pos_chars = 0
        neg_chars = 0
        new_pages = 0
        if change.size_diff >= 0:
            char_diff = ('<span class="plus-chars">+%s</span> chars' %
                         change.size_diff)
            pos_chars = change.size_diff
        else:
            char_diff = ('<span class="minus-chars">-%s</span> chars' %
                         -change.size_diff)
            neg_chars = change.size_diff
        if change.change_type == 'new':
            change_action = 'created page'
            new_pages = 1
        elif change.change_type == 'edit':
            change_action = 'edited page'
        page_title = change.page.page_title
        page_url = '#'
        page_link = '<a href="%s">%s</a>' % (page_url, page_title)
        timeago = parse_datetime(change.timestamp)
        points = calc_user_score(pos_chars, neg_chars, new_pages)
        points_html = ('<span class="change-points">%s wikipoints</span>' %
                       points)
        # [Ckarpfinger]
        # [created page]
        # [What the f is git]
        # [2 days ago]
        # [(+31 chars)]
        # for [9001 wikipoints].
        summary_str = '<span class="username">%s</span> %s %s %s (%s) for %s.'
        summary = summary_str % (username, change_action, page_link, timeago,
                                 char_diff, points_html)
        changelog.append({'summary': summary, 'change': change})
    return changelog


@app.route('/')
def index():
    return render_template('index.html',
                           users=all_users_edit_chars_pcts(),
                           scoring_config=config.ScoringConfig,
                           recent_changes=get_recent_change_descs())

if __name__ == '__main__':
    app.run()
