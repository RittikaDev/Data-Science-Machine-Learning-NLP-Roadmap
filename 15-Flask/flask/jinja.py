### BUILDING URL DYNAMICALLY
## VARIABLE RULE
### JINJA 2 TEMPLATE ENGINE

"""
{{  }} EXPRESSIONS TO PRINT OUTPUT IN HTML
{%...%} CONDITIONS, FOR LOOPS => FIND IN result1.html
{#...#} this is for comments
"""

from flask import Flask, render_template, request, redirect, url_for

"""
 IT CREATES AN INSTANCE OF THE FLASK CLASS, 
 WHICH WILL BE YOUR WSGI (WEB SERVER GATEWAY INTERFACE) APPLICATION.
 JINJA 2 IS A TEMPLATE ENGINE. MAIN IMPORTANCE IS IT COMBINES A WEB TEMPLATE (ANY PAGED OF A WEBSITE) WITH A DATA SOURCE (DQL DB/ CSV SHEET/ ML MODEL) TO GENERATE A DYNAMIC WEB PAGE. IT IS USED TO RENDER HTML TEMPLATES WITH DYNAMIC CONTENT IN FLASK APPLICATIONS.
"""
### WSGI APPLICATION
app = Flask(__name__)


@app.route("/")
def welcome():
    return "<html><H1>Welcome to the flask course</H1></html>"


@app.route("/index", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


## VARIABLE RULE
# <int:score> => FORCES THE SCORE TO BE AN INTEGER IN THE URL, int HERE IS A RULE
@app.route("/success/<int:score>")
def success(score):
    res = ""
    if score >= 50:
        res = "PASSED"
    else:
        res = "FAILED"

    return render_template("result.html", results=res)


## VARIABLE RULE
@app.route("/successres/<int:score>")
def successres(score):
    res = ""
    if score >= 50:
        res = "PASSED"
    else:
        res = "FAILED"

    exp = {"score": score, "res": res}

    return render_template("result1.html", results=exp)


## IF CONDITION
@app.route("/sucessif/<int:score>")
def successif(score):

    return render_template("result.html", results=score)


@app.route("/fail/<int:score>")
def fail(score):
    return render_template("result.html", results=score)


@app.route("/submit", methods=["POST", "GET"])
def submit():
    total_score = 0
    if request.method == "POST":
        science = float(request.form["science"])
        maths = float(request.form["maths"])
        c = float(request.form["c"])
        data_science = float(request.form["datascience"])

        total_score = (science + maths + c + data_science) / 4
    else:
        return render_template("getresult.html")
    return redirect(url_for("successres", score=total_score))


if __name__ == "__main__":
    app.run(debug=True)
