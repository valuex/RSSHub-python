import re
import asyncio
import arrow
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
from bs4 import BeautifulSoup


async def get_hotspot_posts():
    """使用 Playwright 获取热点动态"""
    async with async_playwright() as p:
        # Use async context manager for browser to ensure it handles cleanup
        async with await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        ) as browser:
            page = await browser.new_page()
            
            # 设置反检测 (Manual Stealth)
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })

            # Block unnecessary resources
            await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,css}", lambda route: route.abort())
            
            try:
                await page.goto("https://xueqiu.com/?category=hotspot", wait_until='domcontentloaded')
                await page.wait_for_selector('.timeline__item', timeout=15000)
                
                # 模拟滚动加载
                for _ in range(2):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                all_posts = []
                
                timeline_items = soup.find_all('article', class_='timeline__item')
                for item in timeline_items[:20]:  # Limit to top 20 posts
                    # Extract title/content
                    content_element = item.select_one('.timeline__item__content .content--description > div')
                    content_text = content_element.get_text(strip=True, separator='\n') if content_element else "N/A"
                    
                    # Extract timestamp
                    time_element = item.find('a', class_='date-and-source')
                    timestamp = time_element.get_text(strip=True) if time_element else "N/A"
                    
                    # Extract link
                    link = "https://xueqiu.com" + time_element['href'] if time_element and time_element.has_attr('href') else "https://xueqiu.com/?category=hotspot"
                    
                    # Extract author
                    author_element = item.select_one('.timeline__item__header .user__name')
                    author = author_element.get_text(strip=True) if author_element else "雪球用户"
                    
                    all_posts.append({
                        'content': content_text,
                        'timestamp': timestamp,
                        'link': link,
                        'author': author
                    })
                
                return all_posts
                
            except Exception as e:
                # Browser will close automatically due to context manager
                print(f"Error fetching Xueqiu hotspot: {e}")
                return []


def parse_post(post):
    """解析单条动态数据"""
    item = {}
    text = re.sub('<[^<]+?>', '', post.get('content', '雪球热点'))
    item['title'] = text[:100] + '...' if len(text) > 100 else text
    item['description'] = text
    item['link'] = post.get('link', 'https://xueqiu.com/?category=hotspot')
    item['pubDate'] = arrow.now().isoformat()
    item['author'] = post.get('author', '雪球用户')
    return item


def ctx():
    """主函数"""
    if not HAS_PLAYWRIGHT:
        return {
            'title': '雪球热点动态 (Not supported on Vercel)',
            'link': 'https://xueqiu.com/?category=hotspot',
            'description': 'Playwright is not available in this environment. Please use the self-hosted version for this feed.',
            'author': 'hillerliao',
            'items': [{
                'title': 'Playwright not supported on Vercel',
                'description': 'This feed requires Playwright, which is not supported on Vercel. Please use the self-hosted scraper image.',
                'link': 'https://xueqiu.com/?category=hotspot'
            }]
        }

    posts = asyncio.run(get_hotspot_posts())
    items = [parse_post(post) for post in posts]
    return {
        'title': '雪球热点动态',
        'link': 'https://xueqiu.com/?category=hotspot',
        'description': '雪球热点话题和热门动态',
        'author': 'hillerliao',
        'items': items 
    }
