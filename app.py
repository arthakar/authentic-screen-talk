import os
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, render_template, url_for, flash, redirect, request
import git
import requests
from openai import OpenAI
from db import submit_responses, fetch_responses

app = Flask(__name__)

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Initialize OpenAI client for OpenRouter
client = OpenAI(
    base_url="https://api.x.ai/v1",
    api_key=XAI_API_KEY,
)

# TMDB API configuration
TMDB_API_KEY = "e89cfdf8cc89e3352910b8e7b867628d"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# LLM API configuration
LLM_API_URL = "http://localhost:5000/generate_questions" # Example URL for a local LLM service

def generate_questions_with_gemini(media_title, media_description, media_type):
    """Generate 5 questions using Gemini 2.0 Flash via OpenRouter"""
    try:
        prompt = f"""
        Generate exactly 5 questions about this {media_type} titled \"{media_title}\".
        Description: {media_description}
        The questions should be:
        1. A random fun fill-in-the-blank about the {media_type}
        2. A funny question regarding the {media_type}
        3. A deep question about the {media_type}
        4. A random and silly fill-in-the-blank prompt related to the {media_type}
        5. A deep question or fill-in-the-blank about the {media_type} in relation to the user
        Return only the 5 questions as a JSON array of strings, no additional text.
        Example format: [\"Question 1\", \"Question 2\", \"Question 3\", \"Question 4\", \"Question 5\"]
        """
        
        completion = client.chat.completions.create(
            extra_headers={},
            extra_body={},
            model="grok-3-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                    ]
                }
            ]
        )
        
        response_text = completion.choices[0].message.content.strip()
        print(completion.choices[0].message.content)
        print(response_text)

        # Parse JSON response
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        elif response_text.startswith('```'):
            response_text = response_text.replace('```', '').strip()
        
        import json
        questions = json.loads(response_text)
        
        if len(questions) < 5:
            return ["Error Generating Question"] * 5
        return questions[:5]
        
    except Exception as e:
        print(f"Error generating questions: {e}")
        return ["Error Generating Question"] * 5

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

        return render_template(
            'motionpicture_detail.html',
            media=movie_info,
            media_type='movie',
            media_id=movie_id
        )
        
    except requests.RequestException as e:
        return render_template('motionpicture_detail.html', media=None, media_type='Movie', questions=[])

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
        
        return render_template(
            'motionpicture_detail.html',
            media=tv_info,
            media_type='tv',
            media_id=tv_id
        )
        
    except requests.RequestException as e:
        return render_template('motionpicture_detail.html', media=None, media_type='TV Show', questions=[])


@app.route("/<media_type>/<int:media_id>/submit_thoughts", methods=['POST', 'GET'])
def submit_thoughts(media_type, media_id ):
    # Get Media show details from TMDB API
    endpoint = 'tv' if media_type == 'tv' else 'movie'
    media_url = f"{TMDB_BASE_URL}/{endpoint}/{media_id}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
        'append_to_response': 'credits'
    }

    if request.method == 'GET':
        try:
            response = requests.get(media_url, params=params)
            response.raise_for_status()
            media_data = response.json()
            
            # Extract TV show information
            poster_path = media_data.get('poster_path')
            image_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            
            # Get cast (first 5 actors)
            cast = []
            if media_data.get('credits', {}).get('cast'):
                for actor in media_data['credits']['cast'][:5]:
                    cast.append(actor.get('name', ''))
            
            media_info = {
                'title': media_data.get('name') or media_data.get('title'),
                'description': media_data.get('overview', 'No description available.'),
                'image_url': image_url,
                'cast': cast
            }
            questions = generate_questions_with_gemini(
                media_info['title'],
                media_info['description'],
                endpoint
            )

            return render_template(
                'submit_thoughts.html',
                media=media_info,
                media_type=endpoint,
                media_id=media_id,
                questions=questions,
               # responses=fetch_responses(f"{endpoint}:{media_id}")
            )

        except requests.RequestException as e:
            return render_template('motionpicture_detail.html', media=None, media_type='TV Show', questions=[])
    elif request.method == 'POST':
        # Get form data
        response1 = request.form.get('question1', '')
        response2 = request.form.get('question2', '')
        response3 = request.form.get('question3', '')
        response4 = request.form.get('question4', '')
        response5 = request.form.get('question5', '')
        
        # Here you can process the form data as needed
        # For now, we'll just redirect back to the detail page
        # You could save to a database, send to an API, etc.
        
        data = [
            ['test', response1],
            ['test', response2],
            ['tesst', response3],
            ['test', response4],
            ['test', response5]]
        
        show_title = f"{endpoint}:{media_id}"
        submit_responses(show_title, data)

        # Redirect back to the appropriate detail page
        if media_type == "tv":
            return redirect(url_for('tv_detail', tv_id=media_id))
        else:
            return redirect(url_for('movie_detail', movie_id=media_id))



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