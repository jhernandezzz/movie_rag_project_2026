import httpx
from app.config import settings

TMDB_BASE_URL = "https://api.themoviedb.org/3"

class TMDBClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.TMDB_READ_ACCESS_TOKEN}",
            "Accept": "application/json"
        }

    async def fetch_popular_movies(self, page: int = 1):
        """Fetch popular/trending movies from TMDB."""
        url = f"{TMDB_BASE_URL}/movie/popular"
        params = {"page": page}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("results", [])

    async def fetch_top_rated_movies(self, page: int = 1):
        """Fetch top-rated movies from TMDB for high-quality content."""
        url = f"{TMDB_BASE_URL}/movie/top_rated"
        params = {"page": page}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("results", [])

    async def fetch_movie_details(self, movie_id: int):
        url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

tmdb_client = TMDBClient()
