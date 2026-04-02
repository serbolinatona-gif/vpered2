import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, g
from werkzeug.utils import secure_filename

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.secret_key = "vpered_secret_123"

DATABASE = "vpered.db"
UPLOAD_FOLDER = "static/uploads"
AVATAR_FOLDER = "static/avatars"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATAR_FOLDER, exist_ok=True)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    db = get_db()
    posts = db.execute("""
        SELECT posts.id, title, content, image, created,
        users.login, users.avatar
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY created DESC
    """).fetchall()
    comments = db.execute("""
        SELECT comments.id, text, post_id, users.login
        FROM comments
        JOIN users ON comments.user_id = users.id
    """).fetchall()
    likes = db.execute("""
        SELECT post_id, COUNT(*) as count
        FROM likes
        GROUP BY post_id
    """).fetchall()
    like_dict = {l["post_id"]: l["count"] for l in likes}
    return render_template("index.html", posts=posts, comments=comments, likes=like_dict)

@app.route("/register", methods=["GET","POST"])
def register():
    error = None
    if request.method=="POST":
        login = request.form["login"]
        password = request.form["password"]
        avatar = request.files.get("avatar")
        db = get_db()
        if db.execute("SELECT id FROM users WHERE login=?",(login,)).fetchone():
            error = "Логин занят"
        else:
            filename = None
            if avatar:
                filename = secure_filename(avatar.filename)
                avatar.save(os.path.join(AVATAR_FOLDER, filename))
            db.execute("INSERT INTO users(login,password,avatar) VALUES(?,?,?)",
                       (login,password,filename))
            db.commit()
            return redirect("/login")
    return render_template("register.html", error=error)

@app.route("/login", methods=["GET","POST"])
def login():
    error=None
    if request.method=="POST":
        login_input = request.form["login"]
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE login=?",(login_input,)).fetchone()
        if user and user["password"]==password:
            session["user_id"]=user["id"]
            session["login"]=user["login"]
            return redirect("/")
        else:
            error="Неверный логин"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/add_post",methods=["GET","POST"])
def add_post():
    if "user_id" not in session:
        return redirect("/login")
    if request.method=="POST":
        title = request.form["title"]
        content = request.form["content"]
        image = request.files.get("image")
        filename = None
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))
        db = get_db()
        db.execute("INSERT INTO posts(title,content,image,user_id) VALUES(?,?,?,?)",
                   (title,content,filename,session["user_id"]))
        db.commit()
        return redirect("/")
    return render_template("add_post.html")

@app.route("/like/<int:id>")
def like(id):
    if "user_id" not in session:
        return redirect("/login")
    db = get_db()
    existing=db.execute("SELECT id FROM likes WHERE user_id=? AND post_id=?",
                        (session["user_id"],id)).fetchone()
    if not existing:
        db.execute("INSERT INTO likes(user_id,post_id) VALUES(?,?)",
                   (session["user_id"],id))
        db.commit()
    return redirect("/")

@app.route("/comment/<int:id>",methods=["POST"])
def comment(id):
    if "user_id" not in session:
        return redirect("/login")
    text = request.form["text"]
    db = get_db()
    db.execute("INSERT INTO comments(text,user_id,post_id) VALUES(?,?,?)",
               (text,session["user_id"],id))
    db.commit()
    return redirect("/")

@app.route("/profile/<login>")
def profile(login):
    db = get_db()
    user=db.execute("SELECT * FROM users WHERE login=?",(login,)).fetchone()
    posts=db.execute("SELECT * FROM posts WHERE user_id=? ORDER BY created DESC",
                     (user["id"],)).fetchall()
    return render_template("profile.html",user=user,posts=posts)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
