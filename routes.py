import os
from os.path import join
from flask import render_template, redirect, url_for, flash, request, send_file, escape, abort, \
    make_response
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from uuid import uuid4
import pymorphy3

from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException

import tag_parser
from main import app, db
from forms import LoginForm, RegistrationForm, CourseDescForm, SearchForm, EditMainInfo, EditPassword
from models import User, load_user, Course, Lesson, Page, LessonFile, TaskCheck, Tag
from utils import allowed_file


@app.route('/')
@app.route('/index')
def index():
    courses = Course.query.filter(Course.is_published == True).limit(10).all()  # TODO: add order by likes(?..)
    return render_template('index.html', courses=courses)


@app.route('/favicon.ico', methods=['GET', 'POST'])
def favicon():
    return get_file('static/images/favicon.ico')


@app.route('/<string:path>')
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

    courses = len(Course.query.filter_by(author_id=id).all())

    return render_template('profile.html', user=user, courses_cnt=courses)


@app.route('/news', methods=['GET', 'POST'])
@login_required
def news():
    return render_template('news.html')


@app.route('/teaching', methods=['GET', 'POST'])
@login_required
def teaching():
    courses = Course.query.filter_by(author_id=current_user.id).all()
    checks = []
    task_checks = TaskCheck.query.filter(TaskCheck.status.is_(None)).all()
    for task in task_checks:
        if task.page.lesson.course.author_id == current_user.id:
            checks.append(task)

    if request.method == 'POST':
        data = request.form
        for k, v in data.items():
            if v:
                task_check = checks[int(k)]
                checks.pop(int(k))
                task_check.status = 1 if int(v) else 0
                db.session.add(task_check)
                db.session.commit()

    return render_template('teaching.html', courses=courses, checks=checks)


@app.route('/courses/create', methods=['GET', 'POST'])
@login_required
def create_course():
    form = CourseDescForm()
    if form.validate_on_submit():
        course = Course(name=form.name.data, desc=form.desc.data, short_desc=form.short_desc.data, author=current_user)
        f = form.img.data
        ext = secure_filename(f.filename).split('.')[-1]
        _uuid = uuid4().hex
        path = os.path.join(app.config['UPLOAD_FOLDER'], app.config['UPLOAD_IMG_SUBFOLDER'], _uuid + '.' + ext)
        course.img_path = path
        course.img_uuid = _uuid
        f.save(path)
        db.session.add(course)
        db.session.commit()
        return redirect(url_for('teaching'))
    return render_template('create_course.html', form=form)


@app.route('/courses/<int:course_id>', methods=['GET', 'POST'])
@login_required
def course(course_id):
    course = Course.query.filter_by(id=course_id).first_or_404()
    if request.method == 'POST':
        course.users.append(current_user)
        db.session.add(course)
        db.session.commit()
        print(course.users)
        flash('Вы успешно поступили на курс', 'success')
        return redirect(url_for('lessons', course_id=course_id))
    hw_cnt = len(db.engine.execute(
        f"select p.add_task from page as p inner join lesson l on p.lesson_id = l.id where (p.add_task = 1) and (l.course_id = {course_id})").all())
    course_cnt = len(course.lessons)
    started = True if current_user in course.users else False
    return render_template('course.html', course=course, course_cnt=course_cnt, hw_cnt=hw_cnt, started=started)


@app.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.filter_by(id=course_id).first_or_404()
    form = CourseDescForm(obj=course)
    if form.validate_on_submit():
        form.populate_obj(course)
        f = form.img.data
        ext = secure_filename(f.filename).split('.')[-1]
        _uuid = uuid4().hex
        path = os.path.join(app.config['UPLOAD_FOLDER'], app.config['UPLOAD_IMG_SUBFOLDER'],
                            _uuid + '.' + ext)
        os.remove(course.img_path)  # important
        course.img_path = path
        course.img_uuid = _uuid
        f.save(path)
        db.session.commit()
        return redirect(url_for('teaching'))
    return render_template('create_course.html', form=form, path=course.img_path)


@app.route('/courses/<int:course_id>/lessons', methods=['GET'])
@login_required
def lessons(course_id):
    course = Course.query.filter_by(id=course_id).first()
    lessons = Lesson.query.filter_by(course_id=course.id).all()

    if User.query.filter_by(username=current_user.username).first().id == course.author_id:
        return render_template('lessons.html', course=course, lessons=lessons, teacher=True)
    else:
        return render_template('lessons.html', course=course, lessons=lessons)


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
            path = os.path.join(app.config['UPLOAD_FOLDER'], app.config['UPLOAD_IMG_SUBFOLDER'], _uuid + '.' + ext)
            fv.save(path)
            lesson_file = LessonFile(path=path, uuid=_uuid, name=user_filename, lesson=lesson)
            db.session.add(lesson_file)
        # pages
        pages = []
        for k, v in data.items():
            if k.startswith('ta'):
                text = v
                page = Page(text=text, lesson=lesson)
                pages.append(page)
            if k.startswith('ch'):
                page = pages[int(k[2:]) - 1]
                page.add_task = True if v == 'on' else False
                db.session.add(page)
        db.session.commit()
        return redirect(url_for('lessons', course_id=course_id))
    # get
    return render_template('create_lesson.html')


@app.route('/courses/<int:course_id>/lessons/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def lesson(course_id, lesson_id):
    les = Lesson.query.filter_by(id=lesson_id).first()
    if request.method == "POST":
        data = request.files
        for k, v in data.items():
            index = int(k[2:])
            filename = v.filename
            if not filename:
                continue
            if not allowed_file(filename):
                # TODO: do smth
                ...
            _uuid = uuid4().hex
            ext = filename.split('.')[-1]
            path = os.path.join(app.config['UPLOAD_FOLDER'], app.config['UPLOAD_HW_SUBFOLDER'], _uuid + '.' + ext)
            v.save(path)
            task_check = TaskCheck(user=current_user, page=les.pages[index], file=path, page_index=index)
            db.session.add(task_check)
        db.session.commit()
        flash('Домашние задания успешно сохранены', 'success')
    img_convert = {}
    contents = []
    colors = ["#6c757d" for _ in les.pages]
    should_show_homework = False
    draw_hw = [False for _ in les.pages]
    for f in les.files:
        img_convert[f.name] = url_for('get_file', path=f.path)
    for k, p in enumerate(les.pages):
        contents.append(tag_parser.parse(p.text, img_convert))
        checks = TaskCheck.query.filter_by(page_id=p.id).all()
        if p.add_task:
            if len(checks) == 0 or checks[-1].status != 1:
                should_show_homework = True
                draw_hw[k] = True
            if len(checks) != 0 and checks[-1].status == 1:
                colors[k] = "#198754"
            elif len(checks) != 0 and checks[-1].status == 0:
                colors[k] = "#dc3545"
        else:
            colors[k] = "var(--mbgc)"

    return render_template('lesson.html', lesson=les, contents=contents, course=les.course, pages=les.pages,
                           show_hw=should_show_homework, circle_colors=colors, draw_hw=draw_hw)


@app.route('/test', methods=['GET', 'POST'])
@login_required
def test_profile():
    messages = []

    user = User.query.filter(User.id == current_user.id).first()

    main_inf = EditMainInfo()
    pwd = EditPassword()

    if request.method == 'GET':
        main_inf.username.data = user.username
        main_inf.email.data = user.email

    if main_inf.validate_on_submit():
        user.username = main_inf.username.data
        user.email = main_inf.email.data

        db.session.add(user)
        db.session.commit()

    else:
        main_inf.username.data = user.username
        main_inf.email.data = user.email

    if pwd.validate_on_submit():
        if user.check_password(pwd.old_password.data):
            user.set_password(pwd.password1.data)
            db.session.add(user)
            db.session.commit()
    else:
        main_inf.username.data = user.username
        main_inf.email.data = user.email

    return render_template('edit_profile.html', main_inf=main_inf, password_form=pwd)
    # return render_template('test_profile.html', user=user, courses=created_courses, can_edit=can_edit)


@app.route("/api")
def api():
    current_api = [
        {"title": "/api/get_username", "desc": "Used for getting user name", "params": [("id", "user id")],
         "return": ("name", "user name"), "ex": "https://practicehub.org/api/get_username?id=1"},
        {"title": "/api/get_course_icon", "desc": "Used for getting course icon (avatar) by id",
         "params": [("id", "course id")],
         "return": ("img", "course icon"), "ex": "https://practicehub.org/api/get_course_icon?id=1"},
        {"title": "/api/get_course_name", "desc": "Used for getting course name by id",
         "params": [("id", "course id")],
         "return": ("name", "course name"), "ex": "https://practicehub.org/api/get_course_name?id=1"},
        {"title": "/api/get_course_id", "desc": "Used for getting course id by name",
         "params": [("name", "course name")],
         "return": ("id", "course id"), "ex": "https://practicehub.org/api/get_course_id?name=Mega%20python"}
    ]

    return render_template("api.html", apis=current_api)


@app.route("/api/get_username")
def get_name():
    account_id = request.args["id"]
    user = User.query.filter(User.id == account_id).first()
    return user.username


@app.route("/api/get_course_icon")
def get_course_icon():
    course_id = request.args["id"]
    course = Course.query.filter_by(id=course_id).first()
    return send_file(course.img_path)


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()

    if request.method == 'POST' and 'searchInput' in request.form.keys():
        form.req.data = request.form['searchInput']

    tags = [key for key, value in request.form.items() if value == 'on']
    if form.req.data:
        req = form.req.data

        morph = pymorphy3.MorphAnalyzer()
        normal = morph.normal_forms(req)[0]
        courses = Course.query.filter(Course.desc.contains(req) | Course.short_desc.contains(req) |
                                      Course.desc.contains(normal) | Course.short_desc.contains(normal) |
                                      Course.desc.contains(req) | Course.short_desc.contains(req) |
                                      Course.name.contains(req) | Course.name.contains(req)
                                      ).filter(Course.is_published == True).order_by(Course.rating.desc())
    else:
        courses = Course.query.filter(Course.is_published == True)

    if tags:
        for t in tags:
            courses = courses.filter(Course.tags.any(Tag.tag == t))

    courses = courses.all()
    filter_tags = [t.tag for t in Tag.query.all()]

    return render_template('search.html', courses=courses, form=form, tags=filter_tags,
                           active_tags=tags)


@app.route("/api/get_course_name")
def get_course_name():
    course_id = request.args["id"]
    course = Course.query.filter_by(id=course_id).first()
    return course.name


@app.route("/api/get_course_id")
def get_course_id():
    course_name = request.args["name"]
    course = Course.query.filter_by(name=course_name).first()
    if not course:
        abort(404)
    return course.id


@app.errorhandler(HTTPException)
def handle_exception(e):
    return render_template("error.html", errorname=e.name, cat_img=f"https://http.cat/{e.code}")
