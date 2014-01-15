import config
from models import User

from flask import Flask, render_template

app = Flask(__name__)
app.config.from_object(config.FlaskConfig)


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
    * the relative percent of edits compared to the maximum pos/neg edits in
      the collection, scaled with a minimum percent factor for graphs
    * the number of new pages created by each user
    * the number of points each user has, based on the scoring constants in
      config.ScoringConfig

    Return the results in a dict with the following format:
    {'UserOne': {'pos_chars': 42,
                 'neg_chars': 43,
                 'pos_chars_pct': 27,
                 'neg_chars_pct': 94},
     'UserTwo': {...},
     ...}
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


@app.route('/')
def index():
    return render_template('index.html',
                           users=all_users_edit_chars_pcts(),
                           scoring_config=config.ScoringConfig)

if __name__ == '__main__':
    app.run()
