from flask import Flask, render_template, url_for, flash, redirect, request
import git
import requests

app = Flask(__name__)

# TMDB API configuration
TMDB_API_KEY = "e89cfdf8cc89e3352910b8e7b867628d"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

@app.route("/")
def hello():
    return render_template('index.html')

@app.route("/about")
def about():
    return 'This is about us'

@app.route("/search")
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('hello'))
    
    # TMDB API call
    search_url = f"{TMDB_BASE_URL}/search/multi"
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'en-US',
        'page': 1
    }
    
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract results
        results = []
        for item in data.get('results', [])[:10]:  # Limit to first 10 results
            if item.get('media_type') in ['movie', 'tv']:
                poster_path = item.get('poster_path')
                image_url = f"https://image.tmdb.org/t/p/w200{poster_path}" if poster_path else None
                results.append({
                    'id': item.get('id'),
                    'title': item.get('title') or item.get('name'),
                    'type': 'Movie' if item.get('media_type') == 'movie' else 'TV Show',
                    'description': item.get('overview', 'No description available.'),
                    'image_url': image_url
                })
        
        return render_template('search_results.html', query=query, results=results)
        
    except requests.RequestException as e:
        # Return empty results if API call fails
        return render_template('search_results.html', query=query, results=[])

@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    # Get movie details from TMDB API
    movie_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
        'append_to_response': 'credits'
    }
    
    try:
        response = requests.get(movie_url, params=params)
        response.raise_for_status()
        movie_data = response.json()
        
        # Extract movie information
        poster_path = movie_data.get('poster_path')
        image_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        
        # Get cast (first 5 actors)
        cast = []
        if movie_data.get('credits', {}).get('cast'):
            for actor in movie_data['credits']['cast'][:5]:
                cast.append(actor.get('name', ''))
        
        movie_info = {
            'title': movie_data.get('title'),
            'description': movie_data.get('overview', 'No description available.'),
            'image_url': image_url,
            'cast': cast
        }
        
        return render_template('motionpicture_detail.html', media=movie_info, media_type='Movie')
        
    except requests.RequestException as e:
        return render_template('motionpicture_detail.html', media=None, media_type='Movie')

@app.route("/tv/<int:tv_id>")
def tv_detail(tv_id):
    # Get TV show details from TMDB API
    tv_url = f"{TMDB_BASE_URL}/tv/{tv_id}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
        'append_to_response': 'credits'
    }
    
    try:
        response = requests.get(tv_url, params=params)
        response.raise_for_status()
        tv_data = response.json()
        
        # Extract TV show information
        poster_path = tv_data.get('poster_path')
        image_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        
        # Get cast (first 5 actors)
        cast = []
        if tv_data.get('credits', {}).get('cast'):
            for actor in tv_data['credits']['cast'][:5]:
                cast.append(actor.get('name', ''))
        
        tv_info = {
            'title': tv_data.get('name'),
            'description': tv_data.get('overview', 'No description available.'),
            'image_url': image_url,
            'cast': cast
        }
        
        return render_template('motionpicture_detail.html', media=tv_info, media_type='TV Show')
        
    except requests.RequestException as e:
        return render_template('motionpicture_detail.html', media=None, media_type='TV Show')

@app.route("/update_server", methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('/home/authenticscreentalk/authentic-screen-talk')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400

if __name__ == '__main__':
    app.run(debug=True)