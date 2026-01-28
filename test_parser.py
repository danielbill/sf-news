"""直接测试 parser 代码"""
import asyncio
import httpx
from datetime import datetime, date


async def test_parser():
    """测试 parser 逻辑"""
    url = "https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=30"

    # 创建一个没有 headers 的 client（像 parser 里那样）
    client = httpx.AsyncClient()

    resp = await client.get(url, timeout=30)
    data = resp.json()

    items = data.get("data", {}).get("items", [])

    print(f"返回 {len(items)} 条")

    articles = []
    for item in items:
        title = item.get("title") or item.get("content_text") or item.get("content_short")
        uri = item.get("uri")
        display_time = item.get("display_time")

        if not title or not uri:
            continue

        timestamp = datetime.now()
        if display_time:
            try:
                timestamp = datetime.fromtimestamp(int(display_time))
            except (ValueError, TypeError):
                pass

        # 打印前5条
        if len(articles) < 5:
            is_today = timestamp.date() == date.today()
            print(f"  title: {title[:40]}...")
            print(f"  timestamp: {timestamp}, is_today={is_today}")
            print()

        articles.append((title, uri, timestamp))

    print(f"共解析 {len(articles)} 条文章")

    await client.aclose()


if __name__ == "__main__":
    asyncio.run(test_parser())
