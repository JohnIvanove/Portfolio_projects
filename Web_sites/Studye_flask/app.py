from flask import Flask, render_template, request, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import abort
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'your secret key'
db = SQLAlchemy(app)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    intro = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<Article %r>" % self.id

@app.route("/")
@app.route("/home")
def hello_world():
    return render_template("/")

@app.route("/about")
def func():
    return render_template("about.html")

@app.route("/posts")
def post():
    articles = Article.query.order_by(Article.date.desc()).all()
    return render_template("post.html", articles=articles)

@app.route("/posts/<int:article_id>")
def postes(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template("posts.html", article=article)

@app.route("/posts/<int:article_id>/del")
def post_delet(article_id):
    article = Article.query.get_or_404(article_id)
    try:
        db.session.delete(article)
        db.session.commit()
        return redirect("/posts")
    except Exception as e:
        db.session.rollback()
        return f"There was an error deleting the post: {str(e)}"

@app.route("/posts/<int:article_id>/update", methods=["POST", "GET"])
def update_article(article_id):
    article = Article.query.get_or_404(article_id)
    if request.method == "POST":
        article.title = request.form["title"]
        article.intro = request.form["intro"]
        article.text = request.form["text"]
        try:
            db.session.commit()
            return redirect("/posts")
        except Exception as e:
            db.session.rollback()
            return f"There was an error updating your article: {str(e)}"
    else:
        return render_template("post_update.html", article=article)

@app.route("/create-article", methods=["POST", "GET"])
def create_article():
    if request.method == "POST":
        title = request.form["title"]
        intro = request.form["intro"]
        text = request.form["text"]

        article = Article(title=title, intro=intro, text=text)

        try:
            db.session.add(article)
            db.session.commit()
            return redirect("/posts")
        except Exception as e:
            db.session.rollback()
            return f"There was an error adding your article: {str(e)}"
    else:
        return render_template("create-article.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
