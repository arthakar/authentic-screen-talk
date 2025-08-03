from flask import Flask, render_template, url_for, flash, redirect, request
import git

app = Flask(__name__)

@app.route("/")
def hello():
    return "Authenticity Starts Here"
    # return render_template('index.html')

@app.route("/about")
def about():
    return 'This is about us'

@app.route("/search")
def search():
    query = request.args.get('q', '')
    if query:
        return f'Search results for: {query}'
    else:
        return 'Please enter a search term'

@app.route("/update_server", methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('/home/flaskdeploy1/flask-deploy-1')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400

if __name__ == '__main__':
    app.run()