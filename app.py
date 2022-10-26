from os import urandom
from flask import Flask, flash, render_template, request, url_for
from werkzeug.utils import redirect
from utils import get_results, predict_given_review

app = Flask(__name__)
app.secret_key = urandom(24)


@app.route('/favicon.ico')
def redirectHome():
    return render_template('index.html')


@app.route('/', methods=["POST", "GET"])
def index():
    if request.method == "GET":
        return render_template('index.html')
    else:
        movie_name = request.form["name"]
        return redirect(url_for('result_page', mn=movie_name))


@app.route('/index.html', methods=["POST", "GET"])
def returnHome():
    if request.method == "GET":
        return render_template('index.html')
    else:
        movie_name = request.form["name"]
        return redirect(url_for('result_page', mn=movie_name))


@app.route("/<mn>")
def result_page(mn):
    print(mn)
    try:
        doc_sentiments, pos_per, neg_per, total_rev = get_results(mn)
        print(mn)
    except TypeError:
        flash("Name not found. Couldn't retrieve movie, please try again.", "error")
        return redirect(url_for('index'))
    mn = " ".join(word.capitalize() for word in mn.split(" "))
    if pos_per > neg_per:
        s = "If you ask me, I'd probably give it a shot ;)"
        return render_template('results.html', p=pos_per, n=neg_per, t=total_rev, s=s, mn=mn)
    else:
        s = "Mmmm, well, that is embarrassing."
        return render_template('results.html', p=pos_per, n=neg_per, t=total_rev, s=s, mn=mn)


@app.route('/predictReview.html', methods=["POST", "GET"])
def predictReview():
    if request.method == "GET":
        return render_template('predictReview.html')
    else:
        review = request.form["review"]
        return redirect(url_for('get_sentiment', rev=review))


@app.route("/predictReview/<rev>")
def get_sentiment(rev):
    accuracy, sentiment = predict_given_review(rev)
    accuracy = round((accuracy * 100), 2)
    sentiment = sentiment.lower()
    return render_template('revSenRes.html', sen=sentiment, acc=accuracy, r=rev)


@app.route('/theMission.html')
def theMission():
    return render_template('theMission.html')


@app.route('/whoAmI.html')
def whoAmI():
    return render_template('whoAmI.html')


if __name__ == "__main__":
    app.run(debug=True)
