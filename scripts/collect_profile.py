"""Collect aggregate metrics only. Never persist repository names or credentials."""
import datetime as dt
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
QUERY = '''query($login:String!, $after:String) {
  user(login:$login) {
    contributionsCollection {
      totalCommitContributions totalIssueContributions totalPullRequestContributions
      totalPullRequestReviewContributions totalRepositoryContributions
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
    repositories(first:100,after:$after,ownerAffiliations:OWNER,isFork:false) {
      pageInfo { hasNextPage endCursor }
      nodes { isPrivate stargazerCount forkCount languages(first:100) { totalCount edges { size node { name color } } } }
    }
  }
}'''


def collect():
    token = os.environ.get('PROFILE_STATS_TOKEN', '').strip()
    if not token:
        raise ValueError('PROFILE_STATS_TOKEN is required; existing snapshot was preserved.')
    login = os.environ.get('PROFILE_LOGIN', 'Nostalgia546')
    languages, after, private = {}, None, False
    colors, totals, stars, forks = {}, {}, 0, 0
    calendar = None
    while True:
        request = urllib.request.Request(
            'https://api.github.com/graphql',
            data=json.dumps({'query': QUERY, 'variables': {'login': login, 'after': after}}).encode(),
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                     'User-Agent': 'profile-aggregate-metrics'},
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            result = json.load(response)
        if result.get('errors') or not result.get('data', {}).get('user'):
            raise ValueError('GitHub could not return the requested metrics; snapshot preserved.')
        user = result['data']['user']
        if calendar is None:
            calendar = user['contributionsCollection']['contributionCalendar']
            totals = {key: value for key, value in user['contributionsCollection'].items()
                      if key.startswith('total')}
        repos = user['repositories']
        for repo in repos['nodes']:
            private |= repo['isPrivate']
            stars += repo['stargazerCount']
            forks += repo['forkCount']
            if repo['languages']['totalCount'] > len(repo['languages']['edges']):
                raise ValueError('Language pagination is required; snapshot preserved.')
            for edge in repo['languages']['edges']:
                name = edge['node']['name']
                languages[name] = languages.get(name, 0) + edge['size']
                if name != 'C++':
                    colors[name] = edge['node']['color'] or '#777777'
        if not repos['pageInfo']['hasNextPage']:
            break
        after = repos['pageInfo']['endCursor']
    if not private:
        raise ValueError('No private repository was visible; check authorization. Snapshot preserved.')
    # This allowlist is the privacy boundary. No raw API response is written.
    safe = {
        'updated_at': dt.datetime.now(dt.timezone.utc).date().isoformat(),
        'total_contributions': calendar['totalContributions'],
        'days': [day for week in calendar['weeks'] for day in week['contributionDays']],
        'languages': dict(sorted(((name, size) for name, size in languages.items() if name != 'C++'),
                                 key=lambda item: item[1], reverse=True)),
        'excluded_languages': ['C++'],
        'language_colors': colors,
        'contribution_totals': totals,
        'stars': stars,
        'forks': forks,
        'scope': 'owned non-fork repositories visible to the authorized token',
        'includes_private': private,
    }
    folder = ROOT / 'data'
    folder.mkdir(exist_ok=True)
    temporary = folder / 'profile.json.tmp'
    temporary.write_text(json.dumps(safe, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(folder / 'profile.json')
    print('Aggregate contribution and language snapshot updated; no repository identities stored.')


if __name__ == '__main__':
    try:
        collect()
    except urllib.error.HTTPError as error:
        print(f'GitHub request failed (HTTP {error.code}); existing snapshot preserved.', file=sys.stderr)
        sys.exit(1)
    except (ValueError, urllib.error.URLError, TimeoutError, KeyError):
        print('Metrics refresh failed; verify token permissions and API availability. No response body logged.', file=sys.stderr)
        sys.exit(1)
