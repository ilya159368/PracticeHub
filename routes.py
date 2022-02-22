from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required

from app import app, db
from forms import LoginForm, RegistrationForm, CreateLesson
from models import User, load_user, Course, Lesson


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя пользователя или пароль', 'danger')
            return render_template('login.html', form=form, is_post=True)
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', form=form, is_post=True if request.method == 'POST' else False)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password1.data)
        db.session.add(user)
        db.session.commit()
        flash('Вы успешно зарегистрировались', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form,
                           is_post=True if request.method == 'POST' else False)


@app.route('/profiles/<int:id>', methods=['GET', 'POST'])
@login_required
def profile(id):
    user = User.query.filter_by(id=id).first()

    return render_template('profile.html', user=user)


@app.route('/news', methods=['GET', 'POST'])
@login_required
def news():
    return 'news'


@app.route('/teaching', methods=['GET'])
@login_required
def teaching():
    courses = Course.query.filter_by(author_id=current_user.id).all()
    return render_template('teaching.html', courses=courses)


@app.route('/create_course', methods=['GET', 'POST'])
@login_required
def create_course():
    form = DescForm()
    if form.validate_on_submit():
        course = Course(name=form.username.data, desc=form.email.data)
        course.author_id = current_user.id
        db.session.add(course)
        db.session.commit()
        return redirect(url_for(''))
    return render_template('create_course.html')


@app.route('/create_lessons/<id>', methods=['GET', 'POST'])
@login_required
def create_lessons(id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    course = Course.query.filter_by(id=id).first()
    lessons = Lesson.query.filter_by(course_id=course.id).all()

    if User.query.filter_by(username=current_user.username).first().id == course.author_id:
        form = CreateLesson()
        if form.validate_on_submit():
            lesson = Lesson(name="Новый урок", course_id=course.id)
            db.session.add(lesson)
            db.session.commit()
            lessons = Lesson.query.filter_by(course_id=course.id).all()
        return render_template('lessons.html', course=course, lessons=lessons, form=form)

    return redirect(url_for('index'))
