import asyncio

import trafilatura


async def extract_url_content(url: str) -> str | None:
    # trafilatura는 동기 라이브러리이므로 이벤트 루프 블로킹을 피하려고 to_thread로 감싼다.
    html = await asyncio.to_thread(trafilatura.fetch_url, url)
    if html is None:
        return None
    return trafilatura.extract(html, output_format="markdown")
