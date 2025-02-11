import sqlite3
from flask import Flask, render_template, request, flash, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import session
from babel import Locale
from babel.dates import format_datetime
from datetime import datetime
import re
import os
import itertools
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'ab214fb66b5ea5a09ebd9f73606f794343b1aad7f3051679'

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
UPLOAD_FOLDER = "static/images/user_posts"
UPLOAD_FOLDER_BANNER = "static/images/banners"
UPLOAD_FOLDER_AVATAR = "static/images/user_avatar"

class User(UserMixin):
    def __init__(self, id, name, surname, login, email, password, bio, birth, city, role, avatar):
        self.id = id
        self.name = name
        self.surname = surname
        self.login = login
        self.email = email
        self.password = password
        self.bio = bio
        self.birth = birth
        self.city = city
        self.role = role
        self.avatar = avatar

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect("db/users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, surname, login, email, password, bio, birth, city, role, avatar FROM users WHERE id=?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return User(*user)
        return None

@app.context_processor
def inject_user():
    return dict(user=current_user)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def create_db():
    conn = sqlite3.connect("db/quiz.db")
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')

    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER,
                question TEXT NOT NULL,
                FOREIGN KEY(quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                answer_text TEXT NOT NULL,
                is_correct INTEGER CHECK(is_correct IN (0,1)),
                FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        print("Таблицы успешно созданы!")
    except sqlite3.Error as e:
        print(f"Ошибка при создании таблиц: {e}")
    finally:
        conn.close()

def faq_db():
    conn = sqlite3.connect("db/faq.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS faq (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        answer TEXT
                    )''')
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect("db/users.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        surname TEXT,
                        login TEXT UNIQUE,
                        email TEXT UNIQUE,
                        password TEXT,
                        bio TEXT DEFAULT 'Не указан',
                        birth TEXT,
                        city TEXT DEFAULT 'Не указан',
                        role TEXT DEFAULT 'user',
                        avatar TEXT DEFAULT 'images/no_photo.png'
                    )''')
    conn.commit()
    conn.close()

    conn = sqlite3.connect("db/posts.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_login TEXT,
                        text TEXT,
                        liked INTEGER,
                        comments INTEGER,
                        image_path TEXT,
                        created_at TEXT
                    )''')
    conn.commit()
    conn.close()

    conn = sqlite3.connect("db/likes.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS likes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_owner TEXT,
                        post_id INTEGER,
                        liked_by TEXT
                    )''')
    conn.commit()
    conn.close()

    conn = sqlite3.connect("db/comments.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_owner TEXT,
                        post_id INTEGER,
                        commented_by TEXT,
                        comment_text TEXT,
                        created_at TEXT
                    )''')
    conn.commit()
    conn.close()

def main_db():
    conn = sqlite3.connect("db/banners.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        path TEXT
                    )''')
    conn.commit()
    conn.close()

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_valid_password(password):
    return len(password) >= 6 and re.search(r"\d", password) and re.search(r"[A-Za-z]", password)

def calculate_default_birth():
    today = datetime.today()
    return today.replace(year=today.year - 18).strftime('%Y-%m-%d')

def count_posts_by_user(user_login):
    conn = sqlite3.connect("db/posts.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM posts WHERE user_login=?", (user_login,))
    post_count = cursor.fetchone()[0]
    
    conn.close()
    
    return post_count

def remove_user_from_db(user_login):
    conn = sqlite3.connect("db/users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE login = ?", (user_login,))
    conn.commit()

    conn = sqlite3.connect("db/posts.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE user_login = ?", (user_login,))
    conn.commit()

    conn = sqlite3.connect("db/likes.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM likes WHERE liked_by = ?", (user_login,))
    conn.commit()

    conn = sqlite3.connect("db/comments.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE commented_by = ?", (user_login,))
    conn.commit()
    
    conn.close()

def get_comments_by_post_id(post_id):
    current_user_login = current_user.login
    conn = sqlite3.connect("db/comments.db")
    cursor = conn.cursor()
    cursor.execute('''SELECT id, comment_text, created_at, commented_by
                      FROM comments WHERE post_id = ?
                      ORDER BY created_at DESC''', (post_id,))
    comments = cursor.fetchall()
    conn.close()

    formatted_comments = []
    for comment_id, comment_text, created_at, commented_by in comments:
        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
        formatted_date = format_datetime(created_at, format="d MMMM yyyy 'в' HH:mm", locale='ru')

        conn = sqlite3.connect("db/users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, surname, avatar FROM users WHERE login = ?", (commented_by,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            name, surname, avatar = user_data
        else:
            name, surname, avatar = 'Неизвестно', '', 'images/no_photo.png'

        comment_data = {
            "comment_id": comment_id,
            "comment_text": comment_text,
            "created_at": formatted_date,
            "commented_by": commented_by,
            "commented_name": name,
            "commented_surname": surname,
            "avatar": avatar
        }

        comment_data["is_author"] = commented_by == current_user_login

        formatted_comments.append(comment_data)

    return formatted_comments

def get_like_count_by_post_id(post_id):
    conn = sqlite3.connect("db/likes.db")
    cursor = conn.cursor()

    cursor.execute('''SELECT COUNT(*) FROM likes WHERE post_id = ?''', (post_id,))
    like_count = cursor.fetchone()[0]
    conn.close()
    return like_count

def get_comments_count_by_post_id(post_id):
    conn = sqlite3.connect("db/comments.db")
    cursor = conn.cursor()

    cursor.execute('''SELECT COUNT(*) FROM comments WHERE post_id = ?''', (post_id,))
    comments_count = cursor.fetchone()[0]
    conn.close()
    return comments_count

def delete_quiz(quiz_id):
    conn = sqlite3.connect('db/quiz.db')
    c = conn.cursor()

    try:
        c.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
        
        conn.commit()

    except sqlite3.Error as e:
        print(f"Ошибка при удалении данных: {e}")
        return False
    finally:
        conn.close()

    return True

def delete_faq(faq_id):
    conn = sqlite3.connect('db/faq.db')
    c = conn.cursor()

    try:
        c.execute("DELETE FROM faq WHERE id = ?", (faq_id,))

        conn.commit()

    except sqlite3.Error as e:
        print(f"Ошибка при удалении данных: {e}")
        return False
    finally:
        conn.close()

    return True

def get_quizzes():
    conn = sqlite3.connect('db/quiz.db')
    c = conn.cursor()
    c.execute("""
        SELECT quizzes.id, quizzes.title, COUNT(questions.id) 
        FROM quizzes
        LEFT JOIN questions ON quizzes.id = questions.quiz_id
        GROUP BY quizzes.id
    """)
    quizzes = c.fetchall()
    conn.close()
    return [{"id": q[0], "title": q[1], "question_count": q[2]} for q in quizzes]

def get_question(quiz_id, question_number):
    conn = sqlite3.connect('db/quiz.db')
    c = conn.cursor()
    c.execute("SELECT id, question FROM questions WHERE quiz_id=? LIMIT 1 OFFSET ?", (quiz_id, question_number - 1))
    question = c.fetchone()
    if question:
        c.execute("SELECT id, answer_text FROM answers WHERE question_id=?", (question[0],))
        answers = c.fetchall()
        conn.close()
        return {"id": question[0], "question": question[1], "answers": [{"id": a[0], "text": a[1]} for a in answers]}
    return None

def check_answer(answer_id):
    conn = sqlite3.connect('db/quiz.db')
    c = conn.cursor()
    c.execute("SELECT is_correct FROM answers WHERE id=?", (answer_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_faq_data():
    conn = sqlite3.connect("db/faq.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, answer FROM faq")
    faq_data = cursor.fetchall()
    conn.close()
    return faq_data

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/")
def home():
    conn = sqlite3.connect("db/banners.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, path FROM users")
    banners = cursor.fetchall()
    conn.close()

    conn = sqlite3.connect("db/posts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT text, image_path, created_at, id, user_login FROM posts ORDER BY RANDOM() LIMIT 3")
    posts = []

    for row in cursor.fetchall():
        post_text, image_path, created_at, post_id, user_login = row

        formatted_date = format_datetime(datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S"),
                                         format="d MMMM yyyy 'в' HH:mm", locale='ru')

        user_conn = sqlite3.connect("db/users.db")
        user_cursor = user_conn.cursor()
        user_cursor.execute("SELECT name, surname, avatar FROM users WHERE login=?", (user_login,))
        user_data = user_cursor.fetchone()
        user_conn.close()

        if user_data:
            user_name, user_surname, avatar = user_data
        else:
            user_name, user_surname, avatar = "Неизвестный", "", "default_avatar.jpg"

        posts.append({
            "text": post_text, 
            "image_path": image_path, 
            "created_at": formatted_date, 
            "post_id": post_id,
            "user": {
                "login": user_login,
                "name": user_name,
                "surname": user_surname,
                "avatar": avatar
            }
        })

    conn.close()

    return render_template("home.html", user=current_user, login=current_user.login if current_user.is_authenticated else None, banners=banners, posts=posts)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("view_user_profile", login=current_user.login))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect("db/users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, surname, login, email, password, bio, birth, city, role, avatar FROM users WHERE email=?", (email,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data[5], password):
            user = User(
                id=user_data[0],
                name=user_data[1],
                surname=user_data[2],
                login=user_data[3],
                email=user_data[4],
                password=user_data[5],
                bio=user_data[6],
                birth=user_data[7],
                city=user_data[8],
                role=user_data[9],
                avatar=user_data[10]
            )
            login_user(user)
            return jsonify({"success": True, "message": "Вход успешен!"})
        else:
            errors = []
            if not user_data:
                errors.append("email: Неверный email!")
                errors.append("password: Неверный пароль!")
            else:
                errors.append("password: Неверный пароль!")
            return jsonify({"errors": errors}), 400

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("view_user_profile", login=current_user.login))

    if request.method == "POST":
        name = request.form.get("name")
        surname = request.form.get("surname")
        login = request.form.get("login")
        email = request.form.get("email")
        password = request.form.get("password")
        password_repeat = request.form.get("password_repeat")

        errors = []

        if password != password_repeat:
            errors.append("password_repeat: Пароли не совпадают!")

        if not is_valid_email(email):
            errors.append("email: Неверный формат email!")

        if not is_valid_password(password):
            errors.append("password: Пароль должен быть не менее 6 символов и содержать как минимум одну цифру и одну букву!")

        conn = sqlite3.connect("db/users.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            errors.append("email: Пользователь с таким email уже существует!")

        cursor.execute("SELECT * FROM users WHERE login = ?", (login,))
        if cursor.fetchone():
            errors.append("login: Пользователь с таким логином уже существует!")

        if errors:
            return jsonify({"errors": errors}), 500

        hashed_password = generate_password_hash(password)

        avatar = request.files.get("avatar")
        if avatar:
            avatar_filename = secure_filename(avatar.filename)
            avatar.save(f"static/images/{avatar_filename}")
            avatar_path = f"images/{avatar_filename}"
        else:
            avatar_path = "images/no_photo.png"

        birth_date = calculate_default_birth()

        try:
            cursor.execute("INSERT INTO users (name, surname, login, email, password, avatar, bio, birth, city, role) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                        (name, surname, login, email, hashed_password, avatar_path, "Нет информации", birth_date, "Не указан", "user"))

            conn.commit()

            cursor.execute("SELECT id, name, surname, login, email, role, birth, city, bio, avatar, password FROM users WHERE email=?", (email,))
            user_data = cursor.fetchone()

            if user_data:
                user = User(*user_data)
                login_user(user)

        except sqlite3.IntegrityError:
            return jsonify({"errors": ["Логин или email уже заняты!"]})
        finally:
            conn.close()

        return jsonify({"success": True, "message": "Регистрация успешна!"})

    return render_template("register.html")

@app.route("/profile/<login>")
@login_required
def view_user_profile(login):
    if login != current_user.login:
        return redirect(url_for('view_user_profile', login=current_user.login))

    conn = sqlite3.connect("db/users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, surname, login, email, role, avatar, bio, birth, city FROM users WHERE login=?", (login,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        return "Пользователь не найден", 404

    count_post = count_posts_by_user(login)
    user = {
        "name": user_data[0],
        "surname": user_data[1],
        "login": user_data[2],
        "email": user_data[3],
        "role": user_data[4],
        "avatar": user_data[5],
        "bio": user_data[6],
        "birth": user_data[7],
        "city": user_data[8],
        "count_post": count_post,
    }

    conn = sqlite3.connect("db/posts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT text, image_path, created_at, id FROM posts WHERE user_login=? ORDER BY created_at DESC", (login,))
    posts = cursor.fetchall()
    conn.close()

    formatted_posts = []
    total_likes = 0

    like_conn = sqlite3.connect("db/likes.db")
    like_cursor = like_conn.cursor()
    like_cursor.execute("SELECT post_id FROM likes WHERE liked_by=?", (current_user.login,))
    liked_posts = {row[0] for row in like_cursor.fetchall()}  # Множество постов, на которые поставил лайк текущий пользователь
    like_conn.close()

    for row in posts:
        post_text = row[0]
        image_path = row[1]
        created_at = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
        post_id = row[3]

        formatted_date = format_datetime(created_at, format="d MMMM yyyy 'в' HH:mm", locale='ru')

        like_conn = sqlite3.connect("db/likes.db")
        like_cursor = like_conn.cursor()
        like_cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post_id,))
        like_count = like_cursor.fetchone()[0]
        like_conn.close()

        comment_conn = sqlite3.connect("db/comments.db")
        comment_cursor = comment_conn.cursor()
        comment_cursor.execute("SELECT COUNT(*) FROM comments WHERE post_id = ?", (post_id,))
        comments_count = comment_cursor.fetchone()[0]
        comment_conn.close()

        user_liked_post = post_id in liked_posts

        total_likes += like_count

        formatted_posts.append({
            "text": post_text,
            "image_path": image_path,
            "created_at": formatted_date,
            "post_id": post_id,
            "like_count": like_count,
            "user_liked_post": user_liked_post,
            "comments_count": comments_count
        })

    user["total_likes"] = total_likes

    return render_template("profile.html", user=user, posts=formatted_posts)

@app.route('/upload', methods=['POST'])
def upload_post():
    user_login = request.form.get("user_login")
    text = request.form.get("text", "").strip()
    file = request.files.get("image")

    if not user_login:
        return jsonify({"error": "Не указан логин пользователя"}), 400

    image_path = None
    if file:
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
        image_path = "/" + save_path.replace("\\", "/")

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("db/posts.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO posts (user_login, text, liked, comments, image_path, created_at) VALUES (?, ?, ?, ?, ?, ?)", 
                   (user_login, text, 0, 0, image_path, created_at))
    conn.commit()
    conn.close()

    return jsonify({"message": "Пост успешно загружен", "image_path": image_path, "text": text, "user_login": user_login})

@app.route('/upload/banner', methods=['POST'])
def upload_banner():
    text = request.form.get("text", "").strip()
    file = request.files.get("image")

    image_path = None
    if file:
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        save_path = os.path.join(UPLOAD_FOLDER_BANNER, filename)
        file.save(save_path)
        image_path = f"images/banners/{filename}"

    conn = sqlite3.connect("db/banners.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, path) VALUES (?, ?)", (text, image_path))
    conn.commit()

    return jsonify({"message": "Баннер добавлен"})

@app.route('/block_user', methods=['POST'])
@login_required
def block_user():
    if current_user.role != 'admin':
        return jsonify({"error": "Access denied. Only admins can block users."}), 403
    
    data = request.get_json()
    user_login = data['user_login']

    print(f"{user_login}")

    if current_user.login == user_login:
        logout_user()
        return jsonify({"message": "You cannot block yourself. Session has been terminated."}), 400

    remove_user_from_db(user_login)

@app.route('/delete_post', methods=['POST'])
@login_required
def delete_post():
    data = request.get_json()
    post_id = data['post_id']
    user_login = data['user_login']

    conn_posts = sqlite3.connect("db/posts.db")
    cursor_posts = conn_posts.cursor()

    cursor_posts.execute("SELECT user_login, image_path FROM posts WHERE id = ?", (post_id,))
    post = cursor_posts.fetchone()

    if post:
        if current_user.role == 'admin' or post[0] == user_login:
            image_path = post[1]

            cursor_posts.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            conn_posts.commit()

            conn_likes = sqlite3.connect("db/likes.db")
            cursor_likes = conn_likes.cursor()
            cursor_likes.execute("DELETE FROM likes WHERE post_id = ?", (post_id,))
            conn_likes.commit()

            conn_comments = sqlite3.connect("db/comments.db")
            cursor_comments = conn_comments.cursor()
            cursor_comments.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
            conn_comments.commit()

            full_image_path = os.path.join(UPLOAD_FOLDER, image_path)

            if image_path and os.path.exists(full_image_path):
                try:
                    os.remove(full_image_path)
                    print(f"Файл {full_image_path} успешно удалён.")
                except Exception as e:
                    print(f"Ошибка при удалении файла {full_image_path}: {e}")

            conn_posts.close()
            conn_likes.close()
            conn_comments.close()

            return jsonify({"success": True})
        else:
            conn_posts.close()
            return jsonify({"success": False, "message": "Нет прав для удаления этой публикации"})
    else:
        conn_posts.close()
        return jsonify({"success": False, "message": "Публикация не найдена"})

@app.route('/edit-profile/<login>', methods=['GET', 'POST'])
def edit_profile(login):
    conn = sqlite3.connect("db/users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE login=?", (login,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data is None:
        return "Пользователь не найден", 404

    user = {
        "name": user_data[1],
        "surname": user_data[2],
        "bio": user_data[6],
        "birth": user_data[7],
        "city": user_data[8],
        "avatar": user_data[10],
    }

    if request.method == 'POST':
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        city = request.form['city']
        dob = request.form['dob']
        bio = request.form['bio']

        file = request.files.get("avatar")
        image_path = None
        if file:
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{login}_{file.filename}"
            save_path = os.path.join(UPLOAD_FOLDER_AVATAR, filename)
            file.save(save_path)
            image_path = "/" + save_path.replace("\\", "/")
            avatar_path = f"images/user_avatar/{filename}"

        conn = sqlite3.connect("db/users.db")
        cursor = conn.cursor()
        if image_path:
            cursor.execute("""
                UPDATE users
                SET name=?, surname=?, city=?, birth=?, bio=?, avatar=?
                WHERE login=?
            """, (first_name, last_name, city, dob, bio, avatar_path, login))
        else:
            cursor.execute("""
                UPDATE users
                SET name=?, surname=?, city=?, birth=?, bio=?
                WHERE login=?
            """, (first_name, last_name, city, dob, bio, login))
        conn.commit()
        conn.close()

        return jsonify({"message": "Данные обновлены", "user": user})

    return jsonify({"user": user})

@app.route("/posts")
@login_required
def feed_page():
    conn = sqlite3.connect("db/posts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT text, image_path, created_at, id, user_login FROM posts")
    post_rows = cursor.fetchall()
    conn.close()

    if not post_rows:
        return render_template("feed.html", posts=[])

    liked_by = current_user.login

    post_ids = [row[3] for row in post_rows]

    like_conn = sqlite3.connect("db/likes.db")
    like_cursor = like_conn.cursor()
    like_cursor.execute(
        f"SELECT post_id, COUNT(*) FROM likes WHERE post_id IN ({','.join('?' * len(post_ids))}) GROUP BY post_id",
        post_ids
    )
    like_counts = dict(like_cursor.fetchall())

    like_cursor.execute(
        f"SELECT post_id FROM likes WHERE liked_by = ? AND post_id IN ({','.join('?' * len(post_ids))})",
        [liked_by] + post_ids
    )
    user_liked_posts = set(row[0] for row in like_cursor.fetchall())

    like_conn.close()

    comment_conn = sqlite3.connect("db/comments.db")
    comment_cursor = comment_conn.cursor()
    comment_cursor.execute(
        f"SELECT post_id, COUNT(*) FROM comments WHERE post_id IN ({','.join('?' * len(post_ids))}) GROUP BY post_id",
        post_ids
    )
    comment_counts = dict(comment_cursor.fetchall())
    comment_conn.close()

    posts_by_user = defaultdict(list)

    for row in post_rows:
        post_text, image_path, created_at, post_id, user_login = row
        like_count = like_counts.get(post_id, 0)
        comments_count = comment_counts.get(post_id, 0)
        user_liked_post = post_id in user_liked_posts

        formatted_date = format_datetime(datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S"),
                                         format="d MMMM yyyy 'в' HH:mm", locale='ru')

        user_conn = sqlite3.connect("db/users.db")
        user_cursor = user_conn.cursor()
        user_cursor.execute("SELECT name, surname, avatar FROM users WHERE login=?", (user_login,))
        user_data = user_cursor.fetchone()
        user_conn.close()

        post_data = {
            "text": post_text,
            "image_path": image_path,
            "created_at": formatted_date,
            "post_id": post_id,
            "like_count": like_count,
            "comments_count": comments_count,
            "user": {
                "login": user_login,
                "name": user_data[0],
                "surname": user_data[1],
                "avatar": user_data[2]
            },
            "user_liked_post": user_liked_post
        }

        posts_by_user[user_login].append(post_data)

    for user_posts in posts_by_user.values():
        user_posts.sort(key=lambda p: (-p["like_count"], -p["comments_count"], p["created_at"]))

    sorted_posts = []
    user_iters = [iter(posts) for posts in posts_by_user.values()]
    for post in itertools.chain(*itertools.zip_longest(*user_iters)):
        if post:
            sorted_posts.append(post)

    return render_template("feed.html", posts=sorted_posts)

@app.route("/user/<login>")
@login_required
def view_anon_user_profile(login):
    current_user_login = current_user.login

    if login == current_user_login:
        return redirect(url_for('view_user_profile', login=current_user.login)) 

    conn = sqlite3.connect("db/users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, surname, avatar, bio, city FROM users WHERE login=?", (login,))
    user_data = cursor.fetchone()
    conn.close()

    count_post = count_posts_by_user(login)
    if user_data:
        user_info = {
            "login": login,
            "name": user_data[0],
            "surname": user_data[1],
            "avatar": user_data[2],
            "bio": user_data[3],
            "city": user_data[4],
            "count_post": count_post
        }

        conn = sqlite3.connect("db/posts.db")
        cursor = conn.cursor()
        cursor.execute("SELECT text, image_path, created_at, id FROM posts WHERE user_login=? ORDER BY created_at DESC", (login,))
        posts = cursor.fetchall()
        conn.close()

        formatted_posts = []
        total_likes = 0
        for row in posts:
            post_text = row[0]
            image_path = row[1]
            created_at = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
            post_id = row[3]
            
            formatted_date = format_datetime(created_at, format="d MMMM yyyy 'в' HH:mm", locale='ru')

            like_conn = sqlite3.connect("db/likes.db")
            like_cursor = like_conn.cursor()
            like_cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post_id,))
            like_count = like_cursor.fetchone()[0]

            like_cursor.execute("SELECT 1 FROM likes WHERE post_id = ? AND liked_by = ?", (post_id, current_user_login))
            user_liked_post = like_cursor.fetchone() is not None

            like_conn.close()

            comment_conn = sqlite3.connect("db/comments.db")
            comment_cursor = comment_conn.cursor()
            comment_cursor.execute("SELECT COUNT(*) FROM comments WHERE post_id = ?", (post_id,))
            comments_count = comment_cursor.fetchone()[0]
            comment_conn.close()

            formatted_posts.append({
                "text": post_text,
                "image_path": image_path,
                "created_at": formatted_date,
                "post_id": post_id,
                "like_count": like_count,
                "user_liked_post": user_liked_post, 
                "comments_count": comments_count
            })

            total_likes += like_count

        user_info["total_likes"] = total_likes
        return render_template("user_profile.html", user_info=user_info, posts=formatted_posts)

    return render_template("404.html"), 404

@app.route("/post/<login>/<post_id>")
@login_required
def view_post_for_user(login, post_id):
    conn = sqlite3.connect("db/posts.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT text, image_path, created_at, user_login
        FROM posts 
        WHERE user_login = ? AND id = ?
    """, (login, post_id))
    post_data = cursor.fetchone()
    conn.close()

    if not post_data:
        return render_template("404.html"), 404  

    post_text, image_path, created_at, user_login = post_data

    created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    formatted_date = format_datetime(created_at, format="d MMMM yyyy 'в' HH:mm", locale='ru')

    conn = sqlite3.connect("db/users.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, surname, avatar 
        FROM users 
        WHERE login = ?
    """, (user_login,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        return render_template("404.html"), 404  

    user_name, user_surname, avatar = user_data

    conn = sqlite3.connect("db/likes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post_id,))
    like_count = cursor.fetchone()[0]

    cursor.execute("SELECT 1 FROM likes WHERE post_id = ? AND liked_by = ?", (post_id, current_user.login))
    user_liked_post = cursor.fetchone() is not None
    conn.close()

    comments = get_comments_by_post_id(post_id)
    comments_count = get_comments_count_by_post_id(post_id)

    post_info = {
        "text": post_text,
        "image_path": image_path,
        "created_at": formatted_date,
        "post_id": post_id,
        "user": {
            "login": user_login,
            "name": user_name,
            "surname": user_surname,
            "avatar": avatar
        },
        "like_count": like_count,
        "user_liked_post": user_liked_post,
        "comments": comments,
        "comments_count": comments_count
    }

    return render_template("post.html", post=post_info)

@app.route("/delete_comment/<comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id):
    with sqlite3.connect("db/comments.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT commented_by FROM comments WHERE id = ?", (comment_id,))
        comment_data = cursor.fetchone()

    if comment_data:
        commented_by = comment_data[0]
        if commented_by == current_user.login or current_user.role == 'admin':
            with sqlite3.connect("db/comments.db") as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
                conn.commit()
            return jsonify({"message": "Comment deleted successfully"}), 200
        else:
            return jsonify({"message": "Unauthorized"}), 403
    else:
        return jsonify({"message": "Comment not found"}), 404

@app.route('/like', methods=['POST'])
@login_required
def like_post():
    data = request.get_json()
    post_id = data['post_id']

    liked_by = current_user.login

    conn = sqlite3.connect("db/likes.db")
    cursor = conn.cursor()

    cursor.execute('''SELECT * FROM likes WHERE post_id = ? AND liked_by = ?''', 
                   (post_id, liked_by))
    existing_like = cursor.fetchone()

    if existing_like:
        cursor.execute('''DELETE FROM likes WHERE post_id = ? AND liked_by = ?''',
                       (post_id, liked_by))
        print(f'Пользователь {liked_by} удалил лайк с поста {post_id}')
        liked = False
    else:
        cursor.execute('''INSERT INTO likes (post_id, liked_by) 
                          VALUES (?, ?)''', 
                       (post_id, liked_by))
        print(f'Пользователь {liked_by} поставил лайк на пост {post_id}')
        liked = True

    conn.commit()

    like_count = get_like_count_by_post_id(post_id)

    conn.close()

    return jsonify({'likeCount': like_count, 'liked': liked})

@app.route('/add_comment', methods=['POST'])
@login_required
def add_comment():
    data = request.json
    post_owner = data.get("post_owner")
    post_id = data.get("post_id")
    comment_text = data.get("comment_text")
    commented_by = current_user.login

    if not (post_owner and post_id and comment_text):
        return jsonify({"error": "Все поля обязательны"}), 400

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("db/comments.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO comments (post_owner, post_id, commented_by, comment_text, created_at)
        VALUES (?, ?, ?, ?, ?)''',
        (post_owner, post_id, commented_by, comment_text, created_at)
    )
    conn.commit()

    comments_count = get_comments_count_by_post_id(post_id) 

    conn.close()

    print(f"Написал комментарий")

    return jsonify({'CommentCount': comments_count, 'comment': True})

@app.route('/admin/faq/delete/<int:faq_id>', methods=['DELETE'])
def delete_faq_route(faq_id):
    success = delete_faq(faq_id)
    if success:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "message": "Ошибка при удалении теста"}), 500

@app.route('/admin/quizzes/delete/<int:quiz_id>', methods=['DELETE'])
def delete_quiz_route(quiz_id):
    success = delete_quiz(quiz_id)
    if success:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "message": "Ошибка при удалении теста"}), 500

@app.route('/faq')
def faq():
    faq_data = get_faq_data()
    return render_template('faq.html', faq_data=faq_data)

@app.route('/quizzes')
def quizzes():
    return render_template('quizzes.html', quizzes=get_quizzes())

@app.route('/quiz/<int:quiz_id>')
def quiz(quiz_id):
    conn = sqlite3.connect('db/quiz.db')
    c = conn.cursor()

    c.execute("SELECT title FROM quizzes WHERE id = ?", (quiz_id,))
    quiz = c.fetchone()
    if not quiz:
        return "Тест не найден", 404

    c.execute("SELECT id, question FROM questions WHERE quiz_id = ? LIMIT 1", (quiz_id,))
    question = c.fetchone()
    conn.close()

    if not question:
        return "Вопросы не найдены", 404

    return render_template('quiz.html', quiz_id=quiz_id, quiz_title=quiz[0], first_question=question)

@app.route('/get_question', methods=['POST'])
def get_question():
    data = request.get_json()
    quiz_id = data.get('quiz_id')
    question_number = data.get('question_number')

    if not quiz_id or not question_number:
        return jsonify({'error': 'Неверные данные'}), 400

    conn = sqlite3.connect('db/quiz.db')
    c = conn.cursor()

    c.execute("SELECT id, question FROM questions WHERE quiz_id = ? LIMIT ?, 1", 
              (quiz_id, question_number - 1))
    question = c.fetchone()

    if not question:
        conn.close()
        return jsonify({'error': 'Вопрос не найден'}), 404

    c.execute("SELECT id, answer_text FROM answers WHERE question_id = ?", (question[0],))
    answers = c.fetchall()
    conn.close()

    return jsonify({
        'question': question[1],
        'answers': [{'id': answer[0], 'text': answer[1]} for answer in answers]
    })

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    answer_id = data.get('answer_id')

    if not answer_id:
        return jsonify({'error': 'Ответ не передан'}), 400

    conn = sqlite3.connect('db/quiz.db')
    c = conn.cursor()

    c.execute("SELECT is_correct FROM answers WHERE id = ?", (answer_id,))
    answer = c.fetchone()
    conn.close()

    if not answer:
        return jsonify({'error': 'Ответ не найден'}), 404

    is_correct = answer[0] == 1
    return jsonify({'correct': is_correct})

@app.route("/admin")
@login_required
def admin_add_banner():
    if current_user.role != "admin":
        return render_template("404.html"), 404
    return render_template("admin/admin.html")

@app.route("/admin/banner/add")
@login_required
def admin_panel():
    if current_user.role != "admin":
        return render_template("404.html"), 404
    return render_template("admin/admin-banner-add.html")

@app.route("/admin/banners")
@login_required
def admin_panel_banners():
    if current_user.role != "admin":
        return render_template("404.html"), 404

    conn = sqlite3.connect("db/banners.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    banners = cursor.fetchall()

    conn.close()

    return render_template("admin/admin-banners.html", banners=banners)

@app.route("/admin/delete_banner", methods=["POST"])
@login_required
def delete_banner():
    if current_user.role != "admin":
        return {"success": False}, 403
    
    banner_id = request.form.get("banner_id")
    
    conn = sqlite3.connect("db/banners.db")
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM users WHERE id = ?", (banner_id,))
    conn.commit()
    conn.close()
    
    return {"success": True}

@app.route("/admin/users")
@login_required
def admin_panel_users():
    if current_user.role != "admin":
        return render_template("404.html"), 404

    conn = sqlite3.connect("db/users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    conn.close()

    return render_template('admin/admin-users.html', users=users, total_users=total_users, current_user=current_user)

@app.route("/admin/update-role", methods=["POST"])
@login_required
def update_user_role():
    if current_user.role != "admin":
        return jsonify({"error": "Доступ запрещен"}), 403

    data = request.get_json()
    user_login = data.get("login")

    if not user_login:
        return jsonify({"error": "Логин пользователя не указан"}), 400

    try:
        conn = sqlite3.connect("db/users.db")
        cursor = conn.cursor()

        cursor.execute("SELECT role FROM users WHERE login = ?", (user_login,))
        current_role = cursor.fetchone()

        if not current_role:
            return jsonify({"error": "Пользователь не найден"}), 404

        current_role = current_role[0]

        new_role = "admin" if current_role == "user" else "user"

        cursor.execute("UPDATE users SET role = ? WHERE login = ?", (new_role, user_login))
        conn.commit()

        conn.close()
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/delete-user", methods=["POST"])
@login_required
def delete_user():
    if current_user.role != "admin":
        return jsonify({"error": "Доступ запрещен"}), 403

    data = request.get_json()
    user_login = data.get("login")

    if not user_login:
        return jsonify({"error": "Логин пользователя не указан"}), 400

    conn = sqlite3.connect("db/users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE login = ?", (user_login,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    if current_user.login == user_login:
        logout_user()

    remove_user_from_db(user_login)

    return jsonify({"success": True})

@app.route("/admin/quizzes")
@login_required
def admin_panel_quizzes():
    if current_user.role != "admin":
        return render_template("404.html"), 404
    return render_template('admin/admin-quizzes.html', quizzes=get_quizzes())

@app.route("/admin/faq")
@login_required
def admin_panel_faq():
    if current_user.role != "admin":
        return render_template("404.html"), 404
    faq_data = get_faq_data()
    return render_template('admin/admin-faq.html', faq_data=faq_data)

@app.route("/admin/faq/add", methods=["GET", "POST"])
@login_required
def add_faq():
    if current_user.role != "admin":
        return render_template("404.html"), 404

    if request.method == "POST":
        question = request.form.get("question")
        answer = request.form.get("answer")

        if not question or not answer:
            return jsonify({"message": "Ошибка: Заполните все поля"}), 400


        conn = sqlite3.connect("db/faq.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO faq (name, answer) VALUES (?, ?)", (question, answer))
        conn.commit()
        conn.close()

        return jsonify({"message": "Вопрос и ответ успешно добавлены!"})

    return render_template("admin/admin-faq-add.html")


@app.route("/admin/quizzes/add", methods=["GET", "POST"])
@login_required
def add_quiz():
    if current_user.role != "admin":
        return render_template("404.html"), 404

    if request.method == "POST":
        title = request.form.get("title")

        questions = {}
        for key in request.form:
            if key.startswith('question['):
                question_index = int(key.split('[')[1].split(']')[0])
                questions[question_index] = request.form.get(key)

        print(f"Извлеченные вопросы: {questions}")

        all_answers = {}
        for key in request.form:
            if key.startswith("answer["):
                question_id = int(key.split('[')[1].split(']')[0])

                answers = request.form.getlist(key)

                if question_id not in all_answers:
                    all_answers[question_id] = []

                all_answers[question_id].extend(answers)

        print(f"Ответы по вопросам: {all_answers}")

        correct_answers = {}
        for key, value in request.form.items():
            if key.startswith("correct["):
                question_id = int(key.split('[')[1].split(']')[0])

                correct_answer_index = int(value) - 1

                correct_answers[question_id] = correct_answer_index

        print(f"Правильные ответы: {correct_answers}")

        conn = sqlite3.connect('db/quiz.db')
        c = conn.cursor()

        try:
            c.execute("INSERT INTO quizzes (title) VALUES (?)", (title,))
            quiz_id = c.lastrowid

            for q_idx, question_text in questions.items():
                c.execute("INSERT INTO questions (quiz_id, question) VALUES (?, ?)", (quiz_id, question_text))
                question_id = c.lastrowid

                correct_index = correct_answers.get(q_idx, -1)

                for local_answer_idx, answer_text in enumerate(all_answers.get(q_idx, [])):
                    is_correct = 1 if local_answer_idx == correct_index else 0
                    c.execute("INSERT INTO answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)",
                              (question_id, answer_text, is_correct))

            conn.commit()
            print(f"Тест успешно добавлен с ID: {quiz_id}")
            return jsonify({"message": "Тест успешно сохранен", "quiz_id": quiz_id})
        except Exception as e:
            print(f"Ошибка при сохранении: {str(e)}")
            conn.rollback()
            return jsonify({"error": "Ошибка при сохранении"}), 500
        finally:
            conn.close()

    return render_template("admin/admin-quizzes-add.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
