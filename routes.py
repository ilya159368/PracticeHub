import json
import os
from os.path import join
from flask import render_template, redirect, url_for, flash, request, send_file, escape, abort, \
    make_response
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from uuid import uuid4
from sqlalchemy import func, desc

from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException

import tag_parser
from main import app, db
from forms import LoginForm, RegistrationForm, CourseDescForm, SearchForm, EditMainInfo, EditPassword
from models import User, load_user, Course, Lesson, Page, LessonFile, TaskCheck, MyCourses
from utils import allowed_file


@app.route('/catalog')
def catalog():
    courses = Course.query.filter(Course.is_published == True).order_by(Course.likes.desc()).limit(20).all()
    # like_cnt_lst = db.engine.execute(
    #     f'select liked from course c left join my_courses mc on mc.course_id = c.id where c.author_id = {current_user.id}').all()
    return render_template('index.html', courses=courses)


@app.route("/")
@app.route("/index")
def promo():
    return render_template("promo.html")


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
            next_page = url_for('catalog')
        return redirect(next_page)
    return render_template('login.html', form=form,
                           is_post=True if request.method == 'POST' else False)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('catalog'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('catalog'))
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
    task_checks = TaskCheck.query.filter(TaskCheck.status.is_(None)).order_by(TaskCheck.date.desc()).all()
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
        return redirect(url_for('teaching'))
    return render_template('teaching.html', courses=courses, checks=checks)


@app.route('/courses/create', methods=['GET', 'POST'])
@login_required
def create_course():
    form = CourseDescForm()
    if form.validate_on_submit():
        course = Course(name=form.name.data, desc=form.desc.data, short_desc=form.short_desc.data,
                        author=current_user)
        f = form.img.data
        ext = secure_filename(f.filename).split('.')[-1]
        _uuid = uuid4().hex
        path = os.path.join(app.config['UPLOAD_FOLDER'], app.config['UPLOAD_IMG_SUBFOLDER'],
                            _uuid + '.' + ext)
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
        db.session.add(current_user)
        db.session.commit()
        print(course.users)
        flash('Вы успешно поступили на курс', 'success')
        return redirect(url_for('lessons', course_id=course_id))

    formatted_description = tag_parser.parse(course.desc, {}, True)
    hw_cnt = len(db.engine.execute(f"select p.add_task from page as p inner join lesson l on p.lesson_id = l.id where (p.add_task = 1) and (l.course_id = {course_id})").all())
    course_cnt = len(course.lessons)
    started = True if current_user in course.users else False
    liked = db.engine.execute(f'select liked from my_courses where user_id = {current_user.id} and course_id = {course_id}').first() or False
    if liked:
        liked = liked[0]
    print(liked)
    like_cnt = len(db.engine.execute(f'select liked from my_courses where course_id = {course_id} and liked = 1').all())
    return render_template('course.html', course=course, course_cnt=course_cnt, hw_cnt=hw_cnt, started=started, published=course.is_published,
                           formatted_desc=formatted_description, liked=liked, like_cnt=like_cnt)


@app.route("/courses/<int:course_id>/publish", methods=['POST'])
def on_publish(course_id):
    course = Course.query.filter_by(id=course_id).first_or_404()
    course.is_published = not bool(course.is_published)
    db.session.add(course)
    db.session.commit()
    return redirect(url_for("course", course_id=course_id))

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
    tag_docs = "<b>[B][/B]</b> - выделение текста жирным<br>" \
               "<b>[I][/I]</b> - выделение текста курсивом<br>" \
               "<b>[CODE][/CODE]</b> - текст принимает стиль кода<br>" \
               "<b>[H][/H]</b> - большой текст (заголовок)<br>" \
               "<b>[HR]</b> - разделяющая линия<br>" \
               "<b>[COLOR #FFFFFF][/COLOR]</b> - выделение текста цветом<br>" \
               "<b>[LINK name='lnk' url='https://youtube.com']</b> - ссылка<br>" \
               '<b>[IMG name="z"]</b> - название изображения указывается в вкладке "Ресурсы"<br>' \
               '<b>[VIDEO name="z"]</b> - название видео указывается в вкладке "Ресурсы"'

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
            path = os.path.join(app.config['UPLOAD_FOLDER'], app.config['UPLOAD_IMG_SUBFOLDER'],
                                _uuid + '.' + ext)
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
    return render_template('create_lesson.html', tag_docs=tag_docs)


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
            path = os.path.join(app.config['UPLOAD_FOLDER'], app.config['UPLOAD_HW_SUBFOLDER'],
                                _uuid + '.' + ext)
            v.save(path)
            task_check = TaskCheck(user=current_user, page=les.pages[index], file=path,
                                   page_index=index)
            db.session.add(task_check)
        db.session.commit()
        flash('Домашние задания успешно сохранены', 'success')
        return redirect(url_for('lesson', course_id=course_id, lesson_id=lesson_id))
    img_convert = {}
    contents = []
    colors = ["#6c757d" for _ in les.pages]
    should_show_homework = False
    draw_hw = [False for _ in les.pages]
    for f in les.files:
        img_convert[f.name] = url_for('get_file', path=f.path)
    for k, p in enumerate(les.pages):
        contents.append(tag_parser.parse(p.text, img_convert))
        checks = TaskCheck.query.filter_by(page_id=p.id, user_id=current_user.id).all()
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

    return render_template('lesson.html', lesson=les, contents=contents, course=les.course,
                           pages=les.pages, show_hw=should_show_homework, circle_colors=colors,
                           draw_hw=draw_hw)


@app.route('/profiles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(id):
    user = User.query.filter(User.id == id).first()

    main_inf = EditMainInfo()
    pwd = EditPassword()

    if main_inf.validate_on_submit():
        have_errors = False
        user_name = User.query.filter_by(username=main_inf.username.data).first()
        if user_name and user_name.id != current_user.id:
            main_inf.username.errors.append('Имя уже занято')
            have_errors = True
        user_email = User.query.filter_by(email=main_inf.email.data).first()
        if user_email and user_email.id != current_user.id:
            main_inf.email.errors.append('Почта уже используется')
            have_errors = True
        if not have_errors:
            user.username = main_inf.username.data
            user.email = main_inf.email.data
            db.session.add(user)
            db.session.commit()
            flash('Основная информация успешно изменена', 'success')
            return redirect(url_for('profile', id=id))
    elif pwd.validate_on_submit():
        if user.check_password(pwd.old_password.data):
            user.set_password(pwd.password1.data)
            db.session.add(user)
            db.session.commit()
            flash('Пароль успешно изменен', 'success')
            return redirect(url_for('profile', id=id))
        else:
            pwd.old_password.errors.append('Неверный старый пароль')
    main_inf.username.data = user.username
    main_inf.email.data = user.email
    return render_template('edit_profile.html', main_inf=main_inf, password_form=pwd, is_post=True if request.method == 'POST' else False)


@app.route("/docs/api")
def api():
    current_api = [
        {"title": "/api/get_user_info", "desc": "Used for getting user info", "params": [("id", "user id")],
         "return": [("name", "user name"), ("avatar", "avatar path"), ("avatar_uuid", "unique id of avatar")], "ex": "https://practicehub.org/api/get_username?id=1"},
        {"title": "/api/get_course_icon", "desc": "Used for getting course icon (avatar) by id", "params": [("id", "course id")],
         "return": [("img", "course icon")], "ex": "https://practicehub.org/api/get_course_icon?id=1"},
        {"title": "/api/get_course_info", "desc": "Used for getting course info by id",
         "params": [("id", "course id")],
         "return": [("name", "course name"), ("description", "course desc")], "ex": "https://practicehub.org/api/get_course_name?id=1"},
        {"title": "/api/get_course_id", "desc": "Used for getting course id by name",
         "params": [("name", "course name")],
         "return": [("id", "course id")], "ex": "https://practicehub.org/api/get_course_id?name=Mega%20python"}
    ]

    return render_template("api.html", apis=current_api)


@app.route("/docs/tags")
def tags():
    tags_api = [
        {
            "name": "[B][/B]",
            "desc": " - это тег для выделения текста жирным, обязательно должен иметь закрывающий тег [/B]",
            "ex": "это обычный текст [B]а это жирный[/B]",
            "res": "это обычный текст <b>а это жирный</b>"
        },
        {
            "name": "[I][/I]",
            "desc": " - это тег для выделения текста курсивом, обязательно должен иметь закрывающий тег [/I]",
            "ex": "это обычный текст [I]а это курсив[/I]",
            "res": "это обычный текст <i>а это курсив</i>"
        },
        {
            "name": "[H][/H]",
            "desc": " - это тег преобразует текст в заголовок, обязательно должен иметь закрывающий тег [/H]",
            "ex": "[H]это заголовок[/H]а это обычный текст",
            "res": "<h1>это заголовок</h1>а это обычный текст"
        },
        {
            "name": "[CODE][/CODE]",
            "desc": " - это тег помещает текст в один блок и меняет шриф, обязательно должен иметь закрывающий тег [/CODE]",
            "ex": "[CODE]print('Hi, PracticeHub!')[/CODE]",
            "res": '<div style="background-color: #f5f5f5; border: 1px solid #d5d5d5; border-radius: 3px; line-height: normal;" class="px-3 py-1 my-3 w-50"><code>print("Hi, PracticeHub!")</code></div>'
        },
        {
            "name": "[COLOR #******][/COLOR]",
            "desc": " - это тег для изменения цвета текста, обязательно должен иметь закрывающий тег [/COLOR]",
            "ex": "[COLOR #FF00FF]привет[/COLOR]",
            "res": "<span style='color: #FF00FF'>привет</span>"
        },
        {
            "name": "[HR]",
            "desc": " - это тег для создания разделяющей полосы",
            "ex": "некоторый текст [HR] еще текст",
            "res": ""
        },
        {
            "name": "[LINK name='' url='']",
            "desc": " - это тег для создания ссылки обязательно должен иметь 2 аргумента (название и ссылку)",
            "ex": "[LINK name='yt' url='https://youtube.com']",
            "res": "<a href='https://youtube.com'>yt</a>"
        },
        {
            "name": "[IMG name='']",
            "desc": " - это тег для вставки картинки, name - название картинки во вкладке ресурсы (только в редакторе уроков)",
            "ex": "[IMG name='z']",
            "res": ""
        },
        {
            "name": "[VIDEO name='']",
            "desc": " - это тег для вставки видко, name - название видео во вкладке ресурсы (только в редакторе уроков)",
            "ex": "[VIDEO name='z']",
            "res": ""
        },
    ]

    return render_template("tag_docs.html", tags=tags_api)


@app.route("/api/get_user_info")
def get_user_info():
    account_id = request.args["id"]
    user = User.query.filter(User.id == account_id).first()
    user_info = {
        "name": user.username,
        "avatar": user.img_path,
        "avatar_uuid": user.img_uuid
    }
    return json.dumps(user_info)


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()

    if request.method == 'POST' and 'searchInput' in request.form.keys():
        form.req.data = request.form['searchInput']

    if form.req.data:
        req = f'%{form.req.data.lower()}%'
        # courses = db.session.query(Course, func.count(MyCourses.liked)).filter((Course.short_desc.ilike(req) | Course.name.ilike(req)) & (Course.is_published == True)).join(MyCourses, Course.id == MyCourses.course_id, isouter=True).group_by(Course).order_by(desc(func.count(MyCourses.liked)))
        courses = Course.query.filter((Course.short_desc.ilike(req) | Course.name.ilike(req)) & (Course.is_published == True)).order_by(Course.likes.desc())
    else:
        courses = Course.query.filter(Course.is_published == True)
    courses = courses.all()
    return render_template('search.html', courses=courses, form=form, active_tags=tags)


@app.route("/api/get_course_info")
def get_course_info():
    course_id = request.args["id"]
    course = Course.query.filter_by(id=course_id).first()
    res = {
        "name": course.name,
        "description": course.desc,
        "short_description": course.short_desc,
        "is_published": course.is_published,
        "author_id": course.author_id
    }
    return json.dumps(res)


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


@app.route("/like/<int:course_id>", methods=["POST"])
def like(course_id):
    db.engine.execute(f'update my_courses set liked = not liked where user_id = {current_user.id} and course_id = {course_id}')
    return redirect(url_for('course', course_id=course_id))
