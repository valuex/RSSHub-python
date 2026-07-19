import requests
from rsshub.utils import DEFAULT_HEADERS
import arrow
import hashlib
import urllib.parse


def generate_sign(params):
    """Generate sign for CLS API using SHA1+MD5"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    query_string = urllib.parse.urlencode(sorted_params)
    sha1_hash = hashlib.sha1(query_string.encode('utf-8')).hexdigest()
    return hashlib.md5(sha1_hash.encode('utf-8')).hexdigest()


def parse(post):
    item = {}
    item['title'] = post['title'] if post['title'] != '' else post['content']
    item['description'] = post['content']
    item['link'] = post['shareurl']
    item['pubDate'] = arrow.get(int(post['ctime'])).isoformat()
    return item


def ctx():
    url = 'https://www.cls.cn/v1/roll/get_roll_list'
    params = {
        'app': 'CailianpressWeb',
        'category': '',
        'os': 'web',
        'rn': '50',
        'last_time': '0'
    }
    params['sign'] = generate_sign(params)
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.cls.cn/telegraph'
    })
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    try:
        data = res.json()
        posts = data['data']['roll_data']
    except (ValueError, KeyError) as e:
        print(f"Error decoding JSON: {e}")
        print(f"Response snippet: {res.text[:200]}")
        return {
            'title': f'电报 - 财联社',
            'link': f'https://www.cls.cn/telegraph',
            'description': f'财联社电报 (数据获取失败)',
            'author': 'hillerliao',
            'items': []
        }
    items = list(map(parse, posts))
    return {
        'title': f'电报 - 财联社',
        'link': f'https://www.cls.cn/telegraph',
        'description': f'财联社电报',
        'author': 'hillerliao',
        'items': items
    }
