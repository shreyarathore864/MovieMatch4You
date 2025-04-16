import pandas as pd
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Load datasets
movies = pd.read_csv('data/tmdb_5000_movies.csv')
credits = pd.read_csv('data/tmdb_5000_credits.csv')

# Merge and clean data
df = movies.merge(credits, on='title')[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']].dropna()
df['title_lower'] = df['title'].str.lower()

# Fetch movie details via TMDB API
def fetch_movie_details(title):
    try:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
        response = requests.get(search_url).json()

        if response['results']:
            movie = response['results'][0]
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Poster"

            rating = movie.get("vote_average", "N/A")
            overview = movie.get("overview", "No overview available.")
            release_date = movie.get("release_date", "N/A")
            year = release_date.split("-")[0] if "-" in release_date else "N/A"

            return poster_url, rating, overview, year
        else:
            return "https://via.placeholder.com/500x750?text=Not+Found", "N/A", "No data", "N/A"

    except Exception as e:
        print(f"Error fetching details for {title}: {e}")
        return "https://via.placeholder.com/500x750?text=Error", "N/A", "No data", "N/A"

# Recommend random movies (avoid recommending itself)
def recommend(movie):
    try:
        if movie.lower() not in df['title_lower'].values:
            return []

        recommended_movies = df[df['title_lower'] != movie.lower()].sample(min(5, len(df)-1))['title'].tolist()
        return recommended_movies
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return []

# Get all movie titles
def get_all_titles():
    return df['title'].sort_values().tolist()
