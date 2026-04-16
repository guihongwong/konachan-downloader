import os
import requests
from lxml import etree
from time import sleep

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
}

BASE_URL = "https://konachan.net/post?page={page}&tags={keyword}"


def fetch_html(url, retry=3):
    """获取 HTML（bytes），自动重试"""
    for i in range(retry):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            return resp.content  # ★ 返回 bytes，避免 lxml 报错
        except Exception as e:
            print(f"[WARN] fetch failed ({i+1}/{retry}): {e}")
            sleep(1)
    return None


def parse_image_urls(html_bytes):
    """解析页面中的图片 URL"""
    parser = etree.HTMLParser(recover=True)  # ★ 自动修复坏标签
    tree = etree.HTML(html_bytes, parser=parser)

    # Konachan 缩略图结构：<a class="directlink largeimg" href="...">
    urls = tree.xpath('//a[@class="directlink largeimg"]/@href')
    return urls


def download_image(url, save_dir):
    """下载单张图片"""
    filename = url.split("/")[-1]
    path = os.path.join(save_dir, filename)

    if os.path.exists(path):
        print(f"skip exists: {filename}")
        return

    try:
        img = requests.get(url, headers=HEADERS, timeout=10).content
        with open(path, "wb") as f:
            f.write(img)
        print(f"downloaded: {filename}")
    except Exception as e:
        print(f"[ERROR] download failed {url}: {e}")


def get_pages(from_page, to_page, to_dir, keyword):
    os.makedirs(to_dir, exist_ok=True)

    for page in range(from_page, to_page + 1):
        url = BASE_URL.format(page=page, keyword=keyword)
        print(f"view page: {page} {url}")

        html = fetch_html(url)
        if not html:
            print(f"[ERROR] skip page {page}, fetch failed")
            continue

        img_urls = parse_image_urls(html)
        print(f"image count of this page: {len(img_urls)}")

        for img in img_urls:
            download_image(img, to_dir)

        sleep(0.5)  # 防止访问过快被封


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--from_page", type=int, default=1)
    parser.add_argument("--to_page", type=int, default=5)
    parser.add_argument("--keyword", type=str, default="kirisame_marisa")
    parser.add_argument("--to_dir", type=str, default="downloads")
    args = parser.parse_args()

    get_pages(args.from_page, args.to_page, args.to_dir, args.keyword)


if __name__ == "__main__":
    main()
