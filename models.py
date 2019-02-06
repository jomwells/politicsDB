from politicsapp import db, login_magager
from datetime import datetime
from flask_login import UserMixin

@login_magager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

subs = db.Table('subs',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('politician_id', db.Integer, db.ForeignKey('politician.id'))
    )

article_link = db.Table('article_link',
    db.Column('politician_id', db.Integer, db.ForeignKey('politician.id')),
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
    )

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    subscriptions = db.relationship('Politician', secondary=subs, backref=db.backref('subscribers', lazy = 'dynamic'))

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class Politician(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(70), nullable=False)
    first_name = db.Column(db.String(35), nullable=False)
    last_name = db.Column(db.String(35), nullable=False)
    gender = db.Column(db.String(10), nullable=True)
    party = db.Column(db.String(35), nullable=False)
    constituency = db.Column(db.String(70), nullable=False)
    weburl = db.Column(db.String(45), nullable=True)
    twitterurl = db.Column(db.String(45), nullable=True)
    profile_image = db.Column(db.String(70), nullable=True)
    articles = db.relationship('Article', secondary=article_link, backref=db.backref('politicians'))

    def __repr__(self):
        return f"Politician('{self.full_name}', '{self.party}', '{self.constituency}')"

class Article(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    url = db.Column(db.String(), nullable=False)
    source = db.Column(db.String(), nullable=False)
    title = db.Column(db.String(), nullable=True)
    authors = db.Column(db.String(), nullable=True)
    publish_date = db.Column(db.String(), nullable=False)
    text = db.Column(db.String(), nullable=False)
    top_image = db.Column(db.String(), nullable=True)
    movies = db.Column(db.String(), nullable=True)
    summary = db.Column(db.String(), nullable=True)

    def __repr__(self):
        return f"Article('{self.title}', '{self.source}')"

class DiscardedArticle(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    url = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return f"DiscardedArticle('{self.title}', '{self.source}')"

class NonDownloadableArticle(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    url = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return f"NonDownloadableArticle('{self.title}', '{self.source}')"

class RedundantText(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    opening_string = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return f"NonDownloadableArticle('{self.id}, '{self.opening_string}')"
