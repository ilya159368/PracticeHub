import os
from os.path import join
from flask import render_template, redirect, url_for, flash, request, send_file, escape
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from uuid import uuid4
import pymorphy3

from werkzeug.utils import secure_filename

from app import app, db
from forms import LoginForm, RegistrationForm, CourseDescForm, SearchForm
from models import User, load_user, Course, Lesson, Page, LessonFile
from utils import allowed_file


@app.route('/')
@app.route('/index')
def index():
    courses = Course.query.limit(10).all()  # TODO: add order by likes(?..)
    return render_template('index.html', courses=courses)


@app.route('/uploads/<string:path>')
def get_file(path):
    return send_file(path)


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
    return render_template('news.html')


@app.route('/teaching', methods=['GET'])
@login_required
def teaching():
    courses = Course.query.filter_by(author_id=current_user.id).all()
    return render_template('teaching.html', courses=courses)


@app.route('/courses/create', methods=['GET', 'POST'])
@login_required
def create_course():
    form = CourseDescForm()
    if form.validate_on_submit():
        course = Course(name=form.name.data, desc=form.desc.data, short_desc=form.short_desc.data, author=current_user)
        f = form.img.data
        ext = secure_filename(f.filename).split('.')[-1]
        _uuid = uuid4().hex
        path = os.path.join(app.config['UPLOAD_PATH'], app.config['UPLOAD_IMG_SUBFOLDER'], _uuid + '.' + ext).replace('/', '\\')
        course.img_path = path
        course.img_uuid = _uuid
        f.save(path)
        db.session.add(course)
        db.session.commit()
        return redirect(url_for('teaching'))
    return render_template('create_course.html', form=form)


@app.route('/courses/<int:course_id>', methods=['GET', 'POST'])
# @login_required
def course(course_id):
    course = Course.query.filter_by(id=course_id).first_or_404()
    return render_template('course.html', course=course)


@app.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.filter_by(id=course_id).first_or_404()
    form = CourseDescForm(obj=course)
    if form.validate_on_submit():
        form.populate_obj(course)
        # TODO: do smth with files!!
        db.session.commit()
        return redirect(url_for('teaching'))
    return render_template('create_course.html', form=form)


@app.route('/courses/<int:course_id>/lessons', methods=['GET'])
@login_required
def lessons(course_id):
    course = Course.query.filter_by(id=course_id).first()
    lessons = Lesson.query.filter_by(course_id=course.id).all()

    if User.query.filter_by(username=current_user.username).first().id == course.author_id:
        return render_template('lessons.html', course=course, lessons=lessons)
    else:
        return 'страница уроков для ученика'


@app.route('/courses/<int:course_id>/lessons/create', methods=['GET', 'POST'])
@login_required
def create_lesson(course_id):
    if request.method == 'POST':
        print(request.form)
        print(request.files)
        course = Course.query.filter_by(id=course_id).first()
        data = dict(request.form)
        files = dict(request.files)
        lesson = Lesson(name=data['title'], course=course)
        # files
        for fk, fv in files.items():
            ind = fk[1:]
            for nk, nv in data.items():
                if not nk.startswith('rn'):
                    continue
                if nk[2:] == ind:
                    user_filename = nv
                    break
            else:
                raise ValueError('no matching resource NAME')
            filename = fv.filename
            if not filename:
                raise ValueError('empty file | null name')
            if not allowed_file(filename):
                # TODO: do smth
                ...
            _uuid = uuid4().hex
            ext = filename.split('.')[-1]
            path = os.path.join(app.config['UPLOAD_PATH'], app.config['UPLOAD_IMG_SUBFOLDER'], _uuid + '.' + ext).replace('/', '\\')
            fv.save(path)
            lesson_file = LessonFile(path=path, uuid=_uuid, name=user_filename, lesson=lesson)
            db.session.add(lesson_file)
        # pages
        for k, v in data.items():
            if not k.startswith('ta'):
                continue
            text = escape(v)
            page = Page(text=text, lesson=lesson)
            db.session.add(page)
        db.session.commit()
        return redirect(url_for('lessons', course_id=course_id))
    # get
    return render_template('create_lesson.html')


@app.route('/courses/<int:course_id>/lessons/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def lesson(course_id, lesson_id):
    lesson = Lesson.query.filter_by(id=course_id).first()


@app.route('/test/<int:id>', methods=['GET', 'POST'])
def test_profile(id):
    user = User.query.filter(User.id == id).first()
    created_courses = Course.query.filter(Course.author_id == user.id).all()

    can_edit = False
    if current_user.__class__.__name__ != 'AnonymousUserMixin' and user.id == current_user.id:
        can_edit = True

    return render_template('test_profile.html', user=user, courses=created_courses, can_edit=can_edit)


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        req = form.req.data

        morph = pymorphy3.MorphAnalyzer()
        normal = morph.normal_forms(req)[0]
        courses = Course.query.filter(Course.desc.contains(req) | Course.short_desc.contains(req) |
                                      Course.desc.contains(normal) | Course.short_desc.contains(normal)
                                      ).filter(Course.is_published == True).order_by().all()
    else:
        print('else')
        courses = Course.query.all()
    print(courses)
    return render_template('search.html', courses=courses, form=form, tags=[f'{i + 1}-ый тег' for i in range(10)])
