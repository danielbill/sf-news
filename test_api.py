"""测试华尔街见闻API"""
import asyncio
import httpx
from datetime import datetime


async def test_wallstreetcn_live():
    """测试华尔街见闻快讯API"""
    url = "https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=30"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        print(f"Content-Length: {len(resp.content)}")

        data = resp.json()
        items = data.get("data", {}).get("items", [])

        print(f"\n=== 返回 {len(items)} 条 ===\n")

        today = datetime.now().date()
        today_count = 0

        for i, item in enumerate(items[:10]):
            title = item.get("title") or item.get("content_text") or item.get("content_short")
            uri = item.get("uri")
            display_time = item.get("display_time")

            # 调试 display_time 类型
            print(f"  display_time type={type(display_time)}, value={display_time}")

            # 转换时间
            if display_time:
                ts = datetime.fromtimestamp(display_time)
                is_today = ts.date() == today
                if is_today:
                    today_count += 1
                time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
                today_mark = " [TODAY]" if is_today else " [OLD]"
            else:
                time_str = "NO TIME"
                today_mark = ""

            print(f"[{i}] {time_str}{today_mark}")
            print(f"    title: {title[:60]}...")
            print(f"    uri: {uri}")
            print()

        print(f"=== 前10条中今天的有 {today_count} 条 ===")


async def test_wallstreetcn_news():
    """测试华尔街见闻资讯API"""
    url = "https://api-one.wallstcn.com/apiv1/content/information-flow?channel=global-channel&accept=article&limit=30"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")

        data = resp.json()
        items = data.get("data", {}).get("items", [])

        print(f"\n=== 资讯流返回 {len(items)} 条 ===\n")

        today = datetime.now().date()
        today_count = 0

        for i, item in enumerate(items[:10]):
            resource = item.get("resource", {})
            resource_type = item.get("resource_type")

            # 过滤广告和主题
            if resource_type in ("theme", "ad") or resource.get("type") == "live":
                continue

            title = resource.get("title") or resource.get("content_short")
            uri = resource.get("uri")
            display_time = resource.get("display_time")

            if display_time:
                ts = datetime.fromtimestamp(display_time)
                is_today = ts.date() == today
                if is_today:
                    today_count += 1
                time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
                today_mark = " [TODAY]" if is_today else " [OLD]"
            else:
                time_str = "NO TIME"
                today_mark = ""

            print(f"[{i}] {time_str}{today_mark} | type={resource_type}")
            print(f"    title: {title[:60]}...")
            print(f"    uri: {uri}")
            print()

        print(f"=== 今天的资讯有 {today_count} 条 ===")


if __name__ == "__main__":
    print("=" * 60)
    print("测试华尔街见闻快讯")
    print("=" * 60)
    asyncio.run(test_wallstreetcn_live())

    print("\n" + "=" * 60)
    print("测试华尔街见闻资讯")
    print("=" * 60)
    asyncio.run(test_wallstreetcn_news())
