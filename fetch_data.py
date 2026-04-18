import requests
import time
import os

# Constants
API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', 'c565137f0689452ca211e2ae468c8693')
BASE_URL = 'https://api.football-data.org/v4/'
CACHE_TIME = 300  # Cache duration in seconds (5 minutes)

# Cache storage
cache = {}


def fetch_data(endpoint):
    """Fetch data from the Football-Data.org API and handle errors."""
    url = f"{BASE_URL}{endpoint}"
    headers = {'X-Auth-Token': API_KEY}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

    return None


def get_fixtures():
    """Get upcoming Premier League fixtures."""
    if 'fixtures' in cache and time.time() - cache['fixtures']['time'] < CACHE_TIME:
        print("[CACHED] Returning cached fixtures data")
        return cache['fixtures']['data']

    print("Fetching upcoming fixtures from API...")
    fixtures = fetch_data('competitions/PL/matches?status=SCHEDULED')
    if fixtures:
        cache['fixtures'] = {'data': fixtures, 'time': time.time()}
    return fixtures


def get_results():
    """Get completed match results."""
    if 'results' in cache and time.time() - cache['results']['time'] < CACHE_TIME:
        print("[CACHED] Returning cached results data")
        return cache['results']['data']

    print("Fetching completed matches from API...")
    results = fetch_data('competitions/PL/matches?status=FINISHED')
    if results:
        cache['results'] = {'data': results, 'time': time.time()}
    return results


def get_standings():
    """Get current league standings."""
    if 'standings' in cache and time.time() - cache['standings']['time'] < CACHE_TIME:
        print("[CACHED] Returning cached standings data")
        return cache['standings']['data']

    print("Fetching league standings from API...")
    standings = fetch_data('competitions/PL/standings')
    if standings:
        cache['standings'] = {'data': standings, 'time': time.time()}
    return standings


def get_scores():
    """Get live scores for ongoing matches."""
    if 'scores' in cache and time.time() - cache['scores']['time'] < CACHE_TIME:
        print("[CACHED] Returning cached live scores data")
        return cache['scores']['data']

    print("Fetching live matches from API...")
    scores = fetch_data('competitions/PL/matches?status=LIVE')
    if scores:
        cache['scores'] = {'data': scores, 'time': time.time()}
    return scores


def group_fixtures_by_gameweek(fixtures_data):
    """Group fixtures by matchday (gameweek). Returns an ordered dict where keys are like 'Gameweek X' or 'Date YYYY-MM-DD'."""
    if not fixtures_data or 'matches' not in fixtures_data:
        return {}

    from collections import defaultdict
    import datetime

    groups = defaultdict(list)
    for match in fixtures_data['matches']:
        key = match.get('matchday')
        if key is None:
            # fallback: group by calendar date (YYYY-MM-DD)
            utc = match.get('utcDate')
            try:
                dt = datetime.datetime.fromisoformat(utc.replace('Z', '+00:00'))
                key = f"Date {dt.date().isoformat()}"
            except Exception:
                key = "Unspecified"
        else:
            key = f"Gameweek {key}"
        groups[key].append(match)

    # Sort group keys: numeric gameweeks first, then dates, then others
    def sort_key(k):
        if k.startswith("Gameweek "):
            try:
                return (0, int(k.split()[1]))
            except Exception:
                return (0, 9999)
        if k.startswith("Date "):
            return (1, k[5:])
        return (2, k)

    ordered = dict(sorted(groups.items(), key=lambda kv: sort_key(kv[0])))

    # Sort matches within each group chronologically
    for k in ordered:
        ordered[k].sort(key=lambda m: m.get('utcDate') or '')

    return ordered


def print_fixtures(fixtures_data, show_gameweeks=True, max_gameweeks=None):
    """Format and print upcoming fixtures.

    If show_gameweeks is True (default), fixtures are grouped by matchday (gameweek).
    max_gameweeks can be set to limit how many gameweeks to display.
    """
    if not fixtures_data or 'matches' not in fixtures_data:
        print("No fixtures data available")
        return

    print("\n" + "=" * 80)
    print("UPCOMING PREMIER LEAGUE FIXTURES")
    print("=" * 80)

    if show_gameweeks:
        import datetime
        grouped = group_fixtures_by_gameweek(fixtures_data)
        if not grouped:
            print("No fixtures to display")
            return

        gw_keys = list(grouped.keys())
        if max_gameweeks is not None:
            gw_keys = gw_keys[:max_gameweeks]

        for gw in gw_keys:
            print("\n" + "-" * 40)
            print(gw)
            print("-" * 40)
            for match in grouped[gw]:
                utc = match.get('utcDate')
                try:
                    dt = datetime.datetime.fromisoformat(utc.replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d %H:%M UTC')
                except Exception:
                    date_str = utc or 'Unknown time'
                print(f"{date_str}: {match['homeTeam']['name']} vs {match['awayTeam']['name']}")
    else:
        # legacy behavior: flat list
        for match in fixtures_data['matches'][:100]:  # Show up to 100 matches
            print(f"{match['utcDate']}: {match['homeTeam']['name']} vs {match['awayTeam']['name']}")


def group_results_by_gameweek(results_data):
    """Group results by matchday (gameweek).

    This is an alias to the fixtures grouping function because the data shape is the same.
    """
    return group_fixtures_by_gameweek(results_data)


def print_results(results_data, show_gameweeks=True, max_gameweeks=None):
    """Format and print match results.

    If show_gameweeks is True (default), results are grouped by matchday (gameweek).
    max_gameweeks can be set to limit how many gameweeks to display.
    """
    if not results_data or 'matches' not in results_data:
        print("No results data available")
        return

    print("\n" + "=" * 80)
    print("RECENT RESULTS")
    print("=" * 80)

    if show_gameweeks:
        import datetime
        grouped = group_results_by_gameweek(results_data)
        if not grouped:
            print("No results to display")
            return

        gw_keys = list(grouped.keys())
        if max_gameweeks is not None:
            gw_keys = gw_keys[:max_gameweeks]

        for gw in gw_keys:
            print("\n" + "-" * 40)
            print(gw)
            print("-" * 40)
            for match in grouped[gw]:
                utc = match.get('utcDate')
                try:
                    dt = datetime.datetime.fromisoformat(utc.replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d %H:%M UTC')
                except Exception:
                    date_str = utc or 'Unknown time'

                home = match['homeTeam']['name']
                away = match['awayTeam']['name']
                score = match.get('score', {})
                ft = score.get('fullTime', {}) if isinstance(score, dict) else {}
                home_score = ft.get('home') if isinstance(ft, dict) else None
                away_score = ft.get('away') if isinstance(ft, dict) else None
                home_score = '-' if home_score is None else home_score
                away_score = '-' if away_score is None else away_score

                print(f"{date_str}: {home} {home_score} - {away_score} {away}")
    else:
        # legacy behavior: flat list showing up to 10 recent results
        for match in results_data['matches'][:10]:
            utc = match.get('utcDate')
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            score = match.get('score', {})
            ft = score.get('fullTime', {}) if isinstance(score, dict) else {}
            home_score = ft.get('home') if isinstance(ft, dict) else None
            away_score = ft.get('away') if isinstance(ft, dict) else None
            home_score = '-' if home_score is None else home_score
            away_score = '-' if away_score is None else away_score
            print(f"{utc}: {home} {home_score} - {away_score} {away}")


def print_standings(standings_data):
    """Format and print league standings."""
    if not standings_data or 'standings' not in standings_data:
        print("No standings data available")
        return

    print("\n" + "=" * 80)
    print("LEAGUE STANDINGS")
    print("=" * 80)
    table = standings_data['standings'][0]['table']
    print(f"{'Pos':<4} {'Team':<25} {'P':<3} {'W':<3} {'D':<3} {'L':<3} {'GF':<3} {'GA':<3} {'GD':<4} {'Pts':<3}")
    print("-" * 80)
    for team in table[:10]:  # Show top 10
        print(
            f"{team['position']:<4} {team['team']['name']:<25} {team['playedGames']:<3} {team['won']:<3} {team['draw']:<3} {team['lost']:<3} {team['goalsFor']:<3} {team['goalsAgainst']:<3} {team['goalDifference']:<4} {team['points']:<3}")


def print_scores(scores_data):
    """Format and print live scores."""
    if not scores_data or 'matches' not in scores_data:
        print("No live matches currently")
        return

    print("\n" + "=" * 80)
    print("LIVE MATCHES")
    print("=" * 80)
    for match in scores_data['matches']:
        print(
            f"{match['homeTeam']['name']} {match['score']['fullTime']['home']} - {match['score']['fullTime']['away']} {match['awayTeam']['name']} ({match['status']})")


# Example usage
if __name__ == "__main__":
    # Fetch data
    fixtures = get_fixtures()
    results = get_results()
    #standings = get_standings()
    #scores = get_scores()

    # Print formatted output
    print_fixtures(fixtures)
    print_results(results)
    #print_standings(standings)
    #print_scores(scores)
