from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('ANIME_DB')
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE TABLE
class Anime(db.Model):
    rank: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=True)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    result = db.session.execute(db.select(Anime).order_by(Anime.rank))
    all_anime = result.scalars()
    return render_template("index.html", animes=all_anime)


@app.route("/update")
def update_db():
    # get info for database (rank, title, score)
    url_mal = "https://myanimelist.net/topanime.php?type=airing"
    response = requests.get(url_mal)
    soup = BeautifulSoup(response.content, "html.parser")

    anime_list = soup.find_all("tr", class_=["ranking-list"])

    with app.app_context():
        # Delete all records from the anime table
        db.session.query(Anime).delete()
        db.session.commit()
        db.session.close()

        for anime in anime_list[:50]:
            rank = anime.find("td", class_="rank").text.strip()
            title = anime.find("div", class_="detail").find("a").text.strip()
            score = anime.find("td", class_="score").text.strip()

            anime_url = anime.find("div", class_="detail").find("a")["href"]
            anime_response = requests.get(anime_url)
            anime_soup = BeautifulSoup(anime_response.content, "html.parser")

            image = anime_soup.find("img", class_="ac").get("data-src")
            description = anime_soup.find("p", itemprop="description").text.strip()

            new_anime = Anime(rank=rank, title=title, description=description, score=score, img_url=image)

            db.session.add(new_anime)

        db.session.commit()
        db.session.close()
    print("Update successful")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=False)
