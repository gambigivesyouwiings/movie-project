from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
from pprint import pprint

# You can get the api_key from settings on https://www.themoviedb.org/settings/api once you log in/sign up
project_api = "YOUR OWN API KEY"

db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies-collection.db"

db.init_app(app)
Bootstrap(app)


# This takes care of requests to https://www.themoviedb.org/
def get_movie(title, id=""):
    # There are 2 types of requests, search by query and search by id.
    # To just use search by query, as in the add route, leave the id parameter as is
    # To use the search by id, then add the movie id, as shown in the select route
    mtitle = str(title)
    if id != "":
        m_id = '/' + str(id)
        request_type = ""
        params = {
            "api_key": project_api,
        }
    else:
        m_id = id
        request_type = "/search"
        params = {
            "query": mtitle,
            "api_key": project_api,
            "include_adult": "True"
        }
    response = requests.get(f"https://api.themoviedb.org/3{request_type}/movie{m_id}", params=params)
    return response.json()


# This is the form in add.html
class AddMovie(FlaskForm):
    movie_title = StringField("Movie Title", validators=[DataRequired()],
                              render_kw={'style': 'width:20rem; text-align: center'})
    add_button = SubmitField("Add")


# This is the form in edit.html
class Update(FlaskForm):
    # rating_label = Label(field_id=1, text="Enter new Rating")
    rating = FloatField("Rating", validators=[DataRequired()], render_kw={'style': 'width:10rem; margin-left:1rem; '})
    # review_label = Label(field_id=2, text='Enter new review')
    review = StringField("Review", validators=[DataRequired()], render_kw={'style': 'width:10rem; margin-left:1rem;'})
    submit = SubmitField("Edit", render_kw={'style': 'margin-left:1rem;'})


# This is the table layout to be displayed in the database
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=False)


# This was to initialize the database with some content, performed using the app.app_context() framework with db.session.create_all()

new_movie = Movie(
    title="Phone Booth",
    year=2002,
    description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    rating=7.3,
    ranking=10,
    review="My favourite character was the caller.",
    img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
)

with app.app_context():
    pass


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating.desc(), Movie.year.asc()).all()
    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = i + 1
    return render_template("index.html", movie_list=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    my_form = Update()
    if my_form.validate_on_submit():
        movie_to_edit = request.args.get('title')
        user_data = Movie.query.filter_by(title=movie_to_edit).first()
        user_data.rating = my_form.data["rating"]
        user_data.review = my_form.data["review"]
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=my_form)


@app.route("/delete", methods=['GET', 'POST'])
def delete():
    movie_to_delete = request.args.get('title')
    user_data = Movie.query.filter_by(title=movie_to_delete).first()
    db.session.delete(user_data)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add():
    add_form = AddMovie()
    if add_form.validate_on_submit():
        title_to_get = add_form.data["movie_title"]
        movie_selection = get_movie(title_to_get)
        return render_template("select.html", choices=movie_selection)
    return render_template("add.html", form=add_form)


@app.route("/select", methods=['GET', 'POST'])
def select():
    movie_id = request.args.get('id')
    movie_title = request.args.get('title')
    movie_to_add = get_movie(title=movie_title, id=movie_id)
    release_year = movie_to_add["release_date"].split("-")[0]
    chosen_movie = Movie(
        title=movie_to_add["title"],
        year=release_year,
        description=movie_to_add["overview"],
        img_url="https://image.tmdb.org/t/p/w500" + movie_to_add["poster_path"]
    )
    db.session.add(chosen_movie)
    db.session.commit()
    return redirect(url_for('edit', title=movie_to_add["title"]))


if __name__ == '__main__':
    app.run(debug=True)

# Authored by Victor Mugambi Kimathi
