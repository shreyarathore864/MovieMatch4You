import streamlit as st
import pandas as pd
import requests
import ast
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set Streamlit page config
st.set_page_config(page_title="Movie Recommender", layout="wide")

# Fetch TMDB API Key from environment variable
if "api" in st.secrets:
    TMDB_API_KEY = st.secrets["api"]["tmdb_key"]  # Streamlit Cloud
else:
    from dotenv import load_dotenv
    load_dotenv()
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")  # Local .env

# Load data
movies = pd.read_csv('data/tmdb_5000_movies.csv')
credits = pd.read_csv('data/tmdb_5000_credits.csv')

# Merge and clean data
movies = movies.merge(credits, on='title')
df = movies[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']].dropna()

df['title_lower'] = df['title'].str.lower()

# Parse genres for genre-based browsing
def parse_genres(genre_str):
    return [g['name'] for g in ast.literal_eval(genre_str)]
df['genre_list'] = df['genres'].apply(parse_genres)

# Fetch movie details from TMDB
def fetch_movie_details(title):
    try:
        movie = df[df['title'] == title].iloc[0]
        tmdb_id = movie['movie_id']
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=videos"
        response = requests.get(url).json()
        poster_path = "https://image.tmdb.org/t/p/w500" + response.get("poster_path", "")
        rating = response.get("vote_average", "N/A")
        overview = response.get("overview", "No overview available.")
        release_date = response.get("release_date", "N/A")
        year = release_date.split("-")[0] if "-" in release_date else "N/A"

        trailer = ""
        if 'videos' in response:
            for video in response['videos']['results']:
                if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                    trailer = f"https://www.youtube.com/watch?v={video['key']}"
                    break

        return poster_path, rating, overview, year, trailer
    except Exception as e:
        return "", "N/A", "No data", "N/A", ""

# Simplified placeholder recommend function
def recommend(movie):
    try:
        genres = df[df['title'] == movie]['genre_list'].values[0]
        similar_movies = df[df['genre_list'].apply(lambda g_list: any(g in g_list for g in genres))]
        recommended_titles = similar_movies[similar_movies['title'] != movie].sample(5)['title'].tolist()
        return recommended_titles
    except:
        return ["No recommendations available!"]

# App Title
st.markdown("""
    <h1 style='text-align: center; color: #ff4b4b;'>🎬🎞️🍿MovieMatch4You🍿🎞️🎬</h1>
    <p style='text-align: center;'>Discover movies based on what you love or explore by genre!📺✨</p>
    <style>
    .movie-poster {
        transition: all 0.3s ease-in-out;
        border-radius: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .movie-card:hover .movie-poster {
        transform: scale(1.05);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .movie-info {
        font-size: 0.95rem;
        padding-top: 0.6rem;
    }
    </style>
""", unsafe_allow_html=True)

# Movie input
selected_movie = st.selectbox("🔍 Start typing a movie name:", df['title'].sort_values())

if st.button("🎯 Get Recommendations"):
    st.markdown(f"## 🎞️ {selected_movie}")
    poster_url, rating, overview, year, trailer = fetch_movie_details(selected_movie)
    if poster_url:
        st.image(poster_url, width=250)
    st.markdown(f"**Release Year:** {year}")
    st.markdown(f"**IMDb Rating:** {rating}")
    st.markdown(f"**Overview:** {overview}")
    if trailer:
        st.markdown(f"📽️ [Watch Trailer]({trailer})")

    st.markdown("### 🤖 Recommended Movies:")
    recommended_titles = recommend(selected_movie)
    cols = st.columns(len(recommended_titles))

    for i, title in enumerate(recommended_titles):
        with cols[i]:
            poster_url, rating, overview, year, trailer = fetch_movie_details(title)
            if poster_url:
                st.markdown(f"""
                <div class='movie-card'>
                    <img class='movie-poster' src='{poster_url}' width='150'/>
                    <div class='movie-info'>
                        <strong>{title} ({year})</strong><br>
                        ⭐ {rating}<br>
                        {overview[:80]}...<br>
                        {'<a href="'+trailer+'" target="_blank">🎥 Trailer</a>' if trailer else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# Genre-based browsing
selected_genres = st.multiselect("🎭 Explore by Genre(s):", sorted(set(g for sublist in df['genre_list'] for g in sublist)))
if selected_genres:
    genre_filtered = df[df['genre_list'].apply(lambda x: any(g in x for g in selected_genres))]
    if not genre_filtered.empty:
        st.markdown("### 🍿 Movies Matching Your Genre:")
        sample_movies = genre_filtered.sample(min(5, len(genre_filtered)))
        cols = st.columns(len(sample_movies))

        for idx, row in enumerate(sample_movies.itertuples()):
            with cols[idx]:
                poster_url, rating, overview, year, trailer = fetch_movie_details(row.title)
                if poster_url:
                    st.markdown(f"""
                    <div class='movie-card'>
                        <img class='movie-poster' src='{poster_url}' width='150'/>
                        <div class='movie-info'>
                            <strong>{row.title} ({year})</strong><br>
                            ⭐ {rating}<br>
                            {overview[:80]}...<br>
                            {'<a href="'+trailer+'" target="_blank">🎥 Trailer</a>' if trailer else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("No movies found for the selected genres.")
