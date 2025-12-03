#analyze json for top music results

import pandas as pd
import json
from datetime import datetime, timedelta
import os

LASTFM_USERNAME = "USERNAME"
INPUT_FILE = f"{LASTFM_USERNAME}_plays.json"


def analyze_plays():

    print(f"Loading data from {INPUT_FILE}...")

    if not os.path.exists(INPUT_FILE):
        print(f"\n[ERROR] Input file not found: {INPUT_FILE}")
        print("Please ensure the fetcher script has been ran and the file exists")
        return

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        df = pd.DataFrame(data)

        print(f"Total songs ever scrobbled (All Time): {len(df):,}")

    except Exception as e:
        print(f"\n[ERROR] Failed to read or parse JSON file: {e}")
        return

    print("Preprocessing data...")

    df['timestamp'] = df['date'].apply(lambda x: int(x['uts']))
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')

    one_year_ago = datetime.now() - timedelta(days=365)

    df_filtered = df[df['datetime'] >= one_year_ago]

    print(f"Total listens in the last year: {len(df_filtered):,}")
    print(f"Analyzing data from {one_year_ago.strftime('%Y-%m-%d')} to today.")

    if df_filtered.empty:
        print("\nNo songs found in the last year. try again?")


    def calculate_top_stats(dataframe, column_key, title):

        if column_key == 'artist':
            series = dataframe[column_key].apply(
                lambda x: x.get('name') if isinstance(x, dict) else None
            ).dropna()
        elif column_key == 'album':
            series = dataframe[column_key].apply(
                lambda x: x.get('#text') if isinstance(x, dict) else None
            ).dropna()
        else:
            series = dataframe[column_key]

        top_stats = series.value_counts().head(10)

        total_plays = len(dataframe)

        print(f"\n--- Top 10 {title} (Last Year) ---")

        if top_stats.empty:
            print(f"No top {title} found, likely due to data format issues or missing records.")
            return

        for rank, (name, count) in enumerate(top_stats.items(), 1):

            output_string = f"{rank:2}. {name:<40} ({count:,} plays)"

            if column_key == 'artist' and total_plays > 0:
                percentage = (count / total_plays) * 100
                output_string += f" [{percentage:.2f}%]"

            print(output_string)

    def find_new_artists(df_full, df_recent, cutoff_date):
        df_history = df_full[df_full['datetime'] < cutoff_date]

        extract_artist_name = lambda x: x.get('name') if isinstance(x, dict) else None

        history_artists = set(df_history['artist'].apply(extract_artist_name).dropna().unique())
        recent_artists = set(df_recent['artist'].apply(extract_artist_name).dropna().unique())


        #print(f"\nDEBUG: Historical unique artists (pre-{cutoff_date.strftime('%Y-%m-%d')}): {len(history_artists):,}")
        #print(f"DEBUG: Recent unique artists (post-{cutoff_date.strftime('%Y-%m-%d')}): {len(recent_artists):,}")

        new_artists = recent_artists - history_artists

        print("\n--- New Artists Discovered this Year ---")
        if not new_artists:
            print("No new artists found. predictable!")
        else:
            top_new = list(new_artists)[:5]
            print(f"Total new artists found: {len(new_artists):,}")
            print("\nHere are a few artists you found this year:")
            for rank, artist in enumerate(top_new, 1):
                first_scrobble_date = df_recent[df_recent['artist'].apply(extract_artist_name) == artist][
                    'datetime'].min()
                date_str = first_scrobble_date.strftime('%Y-%m-%d')

                play_count = df_recent[df_recent['artist'].apply(extract_artist_name) == artist].shape[0]

                print(f"{rank}. {artist:<40} (First play: {date_str}, {play_count:,} plays)")

    def calculate_top_artist_all_time(dataframe):

        extract_artist_name = lambda x: x.get('name') if isinstance(x, dict) else None

        series = dataframe['artist'].apply(extract_artist_name).dropna()

        top_stats = series.value_counts().head(10)
        total_scrobbles_all_time = len(dataframe)

        print("\n--- Top 10 Artists (All Time) ---")

        if top_stats.empty:
            print("No top artists found in the complete data.")
            return

        for rank, (name, count) in enumerate(top_stats.items(), 1):
            output_string = f"{rank:2}. {name:<40} ({count:,} plays)"

            if total_scrobbles_all_time > 0:
                percentage = (count / total_scrobbles_all_time) * 100
                output_string += f" [{percentage:.2f}% of all plays]"

            print(output_string)

    # --- Execute Analysis ---

    # 1. Top Artists
    calculate_top_stats(df_filtered, 'artist', 'Artists')

    # 2. Top Tracks (Songs)
    calculate_top_stats(df_filtered, 'name', 'Tracks (Songs)')

    # 3. Top Albums
    calculate_top_stats(df_filtered, 'album', 'Albums')

    # 4. New Artist Discovery
    find_new_artists(df, df_filtered, one_year_ago)

    calculate_top_artist_all_time(df)


if __name__ == "__main__":
    analyze_plays()