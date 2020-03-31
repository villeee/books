import os
import requests

from helpers import *
from flask import Flask, session, render_template, request, redirect, url_for, Markup
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/", methods=["GET","POST"])
@login_required
def index():  
    message = ("")
    username = session.get("username")
    session["books"]=[]
    if request.method == "POST":
        message=("")
        text = request.form.get('text')
        data = db.execute("SELECT * FROM books WHERE author iLIKE '%"+text+"%' or title iLIKE '%"+text+"%' or isbn iLIKE '%"+text+"%'").fetchall()
        for x in data:
            session['books'].append(x)
        if len(session["books"]) == 0:
            message = ("Nothing found. Try again.")       
    return render_template("index.html", data=session['books'], message=message, username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        emailLogin = request.form.get("emailLogin")
        passwordLogin = request.form.get("passwordLogin")
        data = db.execute("SELECT * from users WHERE username = :a", { "a": emailLogin }).fetchone()
        if data != None:
            if data.username == emailLogin and data.password == passwordLogin:
                session["username"] = emailLogin
                return redirect( url_for("index"))                         
            else:
                error = "Wrong password. Please try again."     
        else:
            error = "Wrong email. Please try again."    # Wrong USERNAME:  data.username != emailLogin:
    return render_template("login.html", error=error)


@app.route("/signup", methods=("GET", "POST"))
def signup():
    error = None
    apu = 0
    if request.method == "POST":
        username = request.form.get("emailSignup")
        password = request.form.get("passwordSignup")
        password2 = request.form.get("passwordSignup_RE")
        penname = request.form.get("penname")
        if password != password2:   # Salasanan tarkistus
            apu = 1
            error = "Incorrect password. Please try again."
        data = db.execute("SELECT username FROM users").fetchall()
        for x in range (len(data)):
           # print(data[x]["username"])
            if data[x]["username"] == username:
                apu = 1
                error = "Username already exists. Please try again."           
        if apu == 0:    # Kirjoitetaan, jos username on uniikki
            db.execute("INSERT INTO users (username, password, penname) VALUES (:username, :password, :penname)", { "username":username, "password":password, "penname":penname })
            db.commit()
            return render_template("login.html")
    return render_template("signup.html", error=error)


@app.route("/isbn/<string:isbn>", methods=["GET","POST"])
@login_required
def bookpage(isbn):     
    warning = ""
    writtenreview = ""   #--THIS user has not written review for this book yet
    username = session.get("username")
    x = db.execute("SELECT penname FROM users WHERE username = :username", {"username": username}).fetchone()
    penname = x.penname
    session["reviews"]=[]
    if request.method == 'POST':
        onerating = request.form.get('onerating')
        onereview = request.form.get('onereview')
        db.execute("INSERT INTO reviews (isbn, review, username, rating) VALUES (:isbn,:onereview,:username,:onerating)", { "isbn":isbn, "onereview":onereview, "username":username, "onerating":onerating })
        db.commit()
    #allreviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()    
    allreviews = db.execute("SELECT reviews.username, penname, review, rating, isbn FROM reviews INNER JOIN users ON reviews.username=users.username WHERE isbn = :isbn", {"isbn": isbn}).fetchall()     
 
    for i in allreviews:
        session["reviews"].append(i)
        if i.username == session.get("username"):
            writtenreview = "1"   #-- This user has written review to this book
    selectedbook = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    data = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchall()
    return render_template("book.html", data=data, penname=penname, writtenreview=writtenreview, reviews=session['reviews'], username=username, allreviews=allreviews, selectedbook=selectedbook, warning=warning) 


@app.route("/logout")
def logout():
    session.clear()
    return redirect( url_for("login"))



