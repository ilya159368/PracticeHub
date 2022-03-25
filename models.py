from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


my_courses = db.Table('tags',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True),
    db.Column('completed', db.Boolean),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    created_courses = db.relationship('Course', backref='author', lazy='dynamic')
    created_posts = db.relationship('Post', backref='author', lazy='dynamic')
    my_courses = db.relationship('Course', secondary=my_courses, lazy='dynamic', backref=db.backref('users', lazy=True))
    img_path = db.Column(db.String(64))
    img_uuid = db.Column(db.String(64), index=True)
    # TODO: date created

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lessons = db.relationship('Lesson', backref='course', lazy='dynamic', cascade="all, delete-orphan")
    desc = db.Column(db.Text, nullable=False)
    short_desc = db.Column(db.Text, nullable=False)
    img_path = db.Column(db.String(64))
    img_uuid = db.Column(db.String(64), index=True)
    # author
    # users

    def __repr__(self):
        return f'<Course {self.name} by {self.author.username}>'


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    pages = db.relationship('Page', backref='lesson', lazy='dynamic', cascade="all, delete-orphan")
    files = db.relationship('LessonFile', backref='lesson', lazy='dynamic', cascade="all, delete-orphan")
    # course

    def __repr__(self):
        return f'<Lesson {self.name} in {self.course.name}>'


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    # lesson

    def __repr__(self):
        return f'<Page {self.name}; {self.lesson.name}; {self.lesson.course.name}>'


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    text = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # author

    def __repr__(self):
        return f'<Post {self.name}> by {self.author.username}'


class LessonFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(64))
    uuid = db.Column(db.String(64), index=True)
    name = db.Column(db.String(64), index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    # lesson
