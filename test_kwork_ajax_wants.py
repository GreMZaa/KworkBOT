import asyncio
import aiohttp
import json
import config


async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-encoding; charset=UTF-8"
    }
    if config.KWORK_COOKIES:
        headers["Cookie"] = config.KWORK_COOKIES

    async with aiohttp.ClientSession() as session:
        endpoints = [
            ("POST", "https://kwork.ru/projects", {"c": "11"}),
            ("POST", "https://kwork.ru/index_wants_ajax.php", {"c": "11"}),
            ("POST", "https://kwork.ru/projects?action=get_wants", {}),
            ("GET", "https://kwork.ru/projects?c=11&ajax=1", {}),
            ("POST", "https://kwork.ru/projects?c=11", {"ajax": "1", "page": "1"}),
        ]

        for method, url, data in endpoints:
            print(f"\n{method} {url} data={data} ...")
            try:
                if method == "POST":
                    async with session.post(url, headers=headers, data=data) as resp:
                        print("Status:", resp.status)
                        text = await resp.text()
                        print("Response snippet:", text[:300])
                else:
                    async with session.get(url, headers=headers) as resp:
                        print("Status:", resp.status)
                        text = await resp.text()
                        print("Response snippet:", text[:300])
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
