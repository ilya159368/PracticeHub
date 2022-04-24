from sqlalchemy import func, select
from sqlalchemy.orm import column_property

from main import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from sqlalchemy.ext.associationproxy import association_proxy


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class MyCourses(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key=True)
    liked = db.Column(db.Boolean, default=False)

    def __init__(self, course=None, user=None):
        self.course = course
        self.user = user


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    created_courses = db.relationship('Course', backref='author', lazy='dynamic')
    created_posts = db.relationship('Post', backref='author', lazy='dynamic')

    img_path = db.Column(db.String(64))
    img_uuid = db.Column(db.String(64), index=True)

    task_check = db.relationship("TaskCheck", backref="user")

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
    lessons = db.relationship('Lesson', backref='course', lazy='select',
                              cascade="all, delete-orphan")
    desc = db.Column(db.Text, nullable=False)

    short_desc = db.Column(db.Text, nullable=False)
    img_path = db.Column(db.String(64))
    img_uuid = db.Column(db.String(64), index=True)

    is_published = db.Column(db.Boolean, default=False)
    users = db.relationship('User', secondary=MyCourses.__table__, backref='course')

    likes = column_property(select(func.count(MyCourses.liked)).where(MyCourses.course_id == id).scalar_subquery())

    # author

    def __repr__(self):
        return f'<Course {self.name} by {self.author.username}>'


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    pages = db.relationship('Page', backref='lesson', lazy='select', cascade="all, delete-orphan")
    files = db.relationship('LessonFile', backref='lesson', lazy='dynamic',
                            cascade="all, delete-orphan")

    # course

    def __repr__(self):
        return f'<Lesson {self.name} in {self.course.name}>'


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    add_task = db.Column(db.Boolean, default=False)
    task_check = db.relationship("TaskCheck", backref="page")

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


class TaskCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey("page.id"))
    page_index = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    file = db.Column(db.String(64))
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    status = db.Column(db.Integer)

    # page
    # user

    def __repr__(self):
        return f"<TaskCheck {self.id} page {self.page_id}>"
