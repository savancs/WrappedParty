#last.fm API req to pull scrobbles

import requests
import json
import time
from tqdm import tqdm
import sys

API_KEY = 'APIKEY'
LASTFM_USERNAME = 'USERNAME'
OUTPUT_FILE = f"{LASTFM_USERNAME}_plays.json"

ROOT_URL = 'http://ws.audioscrobbler.com/2.0/'
LIMIT = 200

def get_scrobble_page(page_number, api_key, user, limit):
    params = {
        'method': 'user.getrecenttracks',
        'user': user,
        'api_key': api_key,
        'format': 'json',
        'limit': limit,
        'page': page_number,
        'extended': 1
    }
    try:
        response = requests.get(ROOT_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Request failed for page {page_number}: {e}")
        return None

def fetch_all_scrobbles():
    print(f"Starting download")

    first_page_data = get_scrobble_page(1, API_KEY, LASTFM_USERNAME, LIMIT)
    if not first_page_data or 'error' in first_page_data:
        error_msg = first_page_data.get('message', 'Unknown API error') if first_page_data else 'No response data.'
        print(f"[FATAL] Could not retrieve first page. Check API Key and Username.")
        print(f"API Response Error: {error_msg}")
        return

    try:
        attrs =  first_page_data['recenttracks']['@attr']
        total_pages = int(attrs['totalPages'])
        total_tracks = int(attrs['total'])

        print(f"Total Scrobbles: {total_tracks:,}")
        print(f"Total Pages: {total_pages:,}")

        all_scrobbles = []

        first_page_tracks = first_page_data['recenttracks'].get('track', [])
        processed_tracks = [t for t in first_page_tracks if t.get('date')]
        all_scrobbles.extend(processed_tracks)

        for page in tqdm(range(2, total_pages + 1), desc="Fetching Pages", unit="page", initial=1, total=total_pages):

            time.sleep(0.3)

            page_data = get_scrobble_page(page, API_KEY, LASTFM_USERNAME, LIMIT)

            if page_data and 'recenttracks' in page_data:
                tracks = page_data['recenttracks'].get('track', [])

                if not tracks:
                    break

                all_scrobbles.extend([t for t in tracks if t.get('date')])


            if len(all_scrobbles) >= total_tracks:
                break

    except (KeyError, ValueError) as e:
            print(f"\n[ERROR] failed to parse API response structure: {e}")
            return

    print(f"\nFinished fetching {len(all_scrobbles)} scrobbles")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_scrobbles, f, ensure_ascii=False, indent=4)
        print(f"Successfully wrote to {OUTPUT_FILE}")
    except IOError as e:
        print(f"[ERROR] could not write to file {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    fetch_all_scrobbles()