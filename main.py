from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

MOVIE_DB_API_KEY = os.environ.get('API_KEY')
BEARAR_AUTH = os.environ.get('BEARAR_AUTH')
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/original"


headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {BEARAR_AUTH}"
}

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating out of 10")
    review = StringField("Your review")
    submit = SubmitField("Done")


class AddMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movie = result.scalars().all()
    for i in range(len(all_movie)):
        all_movie[i].ranking = len(all_movie) - i
    db.session.commit()
    return render_template("index.html", movies=all_movie)


@app.route("/edit", methods=["POST", "GET"])
def edit():
    id = request.args.get("id")
    selected_movie = db.get_or_404(Movie, id)
    form = RateMovieForm()
    if request.method == "POST":
        selected_movie.rating = float(form.rating.data)
        selected_movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie=selected_movie, form=form)


@app.route("/delete")
def delete():
    id = request.args.get("id")
    selected_movie = db.get_or_404(Movie, id)
    db.session.delete(selected_movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovie()
    if request.method == "POST":
        title = form.title.data
        parameter = {
            "query": title,
            "include_adult": "false",
            "language": "en-US",
            "page": 1
        }
        response = requests.get(url=MOVIE_DB_SEARCH_URL, headers=headers, params=parameter).json()
        data = response["results"]
        return render_template("select.html", movies=data)
    return render_template("add.html", form=form)


@app.route("/find")
def find():
    id = request.args.get("id")
    if id:
        movie_api_url = f"https://api.themoviedb.org/3/movie/{id}?language=en-US"
        response = requests.get(url=movie_api_url, headers=headers)
        data = response.json()
        print(data)
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            description=data["overview"],
            img_url=f"https://image.tmdb.org/t/p/original/{data['poster_path']}"
        )

        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
