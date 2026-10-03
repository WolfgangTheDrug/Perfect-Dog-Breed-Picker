import requests
import streamlit as st
from typing import Dict, List, Any

@st.cache_data
def fetch_dog_breeds() -> List[Dict[str, Any]]:
    """
    Fetches all dog breed records from the Dog API by automatically 
    iterating through all pagination pages based on metadata.
    """
    base_url: str = "https://dogapi.dog/api/v2/breeds"
    all_breeds: List[Dict[str, Any]] = []
    
    current_page: int = 1
    total_pages: int = 1  # Will be dynamically adjusted on page 1 response
    
    while current_page <= total_pages:
        paginated_url: str = f"{base_url}?page[number]={current_page}"
        response = requests.get(paginated_url)
        
        if response.status_code != 200:
            break
            
        response_payload: Dict[str, Any] = response.json()
        page_breed_records: List[Dict[str, Any]] = response_payload.get("data", [])
        all_breeds.extend(page_breed_records)
        
        # On the first request, read the meta pagination block to find the last page index
        if current_page == 1:
            pagination_metadata: Dict[str, Any] = response_payload.get("meta", {}).get("pagination", {})
            total_pages = pagination_metadata.get("last", 1)
            
        current_page += 1
        
    return all_breeds

@st.cache_data
def get_breed_image_lazily(breed_id: str) -> str:
    """Lazily fetches and caches the breed image URL on-demand via API redirect."""
    api_endpoint: str = f"https://dogapi.dog/api/v2/breeds/{breed_id}/image"
    response = requests.get(api_endpoint, allow_redirects=True)
    
    if response.status_code == 200:
        return response.url
    return ""

