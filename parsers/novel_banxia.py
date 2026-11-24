import sys
import os
import re
import time
from urllib.parse import urljoin

try:
    from crawl_utils import append_to_file, fetch_page, get_meta_info, get_output_path, save_to_file, Timer
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from crawl_utils import append_to_file, fetch_page, get_meta_info, get_output_path, save_to_file, Timer

CHAPTER_REQUEST_INTERVAL_SECONDS = 10

def extract_content(soup):
    """半夏小说特有的内容提取逻辑"""
    if not soup or not soup.body: return ""
    content_div = soup.body.find('div', id='nr1')
    simplified_content = False
    if content_div is None:
        content_div = soup.body.find('div', id='reader-body', class_='reader-body')
        simplified_content = content_div is not None
    if not content_div: return ""
    if simplified_content:
        # 先把所有 br 替换成换行
        for br in content_div.find_all("br"):
            br.replace_with("\n")
        # 取出全部文本
        raw_text = content_div.get_text(separator="", strip=False)
        paragraphs = [
            line.strip()
            for line in raw_text.split("\n")
        ]
        # 过滤空字符串，并且合并连续空行带来的空白
        # paragraphs = [p for p in paragraphs if p]
        # for idx, item in enumerate(paragraphs):
        #     print(idx, repr(item))
        content = "\r\n".join(paragraphs) if paragraphs else raw_text.strip()
    else:
        content = content_div.text
    content = content.replace('\n\n\n\n\n\n\n\n本站無彈出廣告，永久域名（ xbanxia.com ）\n', '\n\n')
    content = content.replace('\n\r\n','\n').replace('本站無彈出廣告', '').replace('半夏小說，快樂很多', '')
    return content

def extract_chapter_links(soup):
    """提取繁体站和简体站的章节链接。"""
    if not soup:
        return []

    legacy_links = soup.find_all('a', href=re.compile(r'/books/\d+/\d+\.html'))
    if legacy_links:
        return legacy_links

    simplified_links = soup.select('div.book-list a[href]')
    if simplified_links:
        return simplified_links

    return soup.select('a[href*="/chapter/"]')

def main():
    if len(sys.argv) < 2:
        print("使用方法: python3 -m parsers.novel_banxia [URL]")
        return

    timer = Timer()
    url = sys.argv[1]
    soup = fetch_page(url)
    if not soup:
        print(f"[错误] 无法获取小说主页: {url}")
        return

    meta = get_meta_info(soup)
    print(f"开始抓取: {meta['title']} - {meta['author']}")

    chapter_links = extract_chapter_links(soup)
    if not chapter_links:
        print(f"[错误] 未在小说主页找到章节链接，未生成文件: {url}")
        return

    output_path = get_output_path(meta['title'], meta['author'])
    page_text = {}
    first_saved_chapter = True
    total = len(chapter_links)
    for idx, link in enumerate(chapter_links):
        chapter_title = link.get_text(" ", strip=True) or f"第{idx+1}章"
        print(f"[{idx+1}/{total}] 正在抓取: {chapter_title} (已用时: {timer.format_time(timer.elapsed())})")
        
        chapter_url = urljoin(url, link['href'])
        chapter_soup = fetch_page(chapter_url)
        if chapter_soup:
            content = extract_content(chapter_soup)
            if content:
                chapter_text = f"\n{chapter_title}\n" + content
                page_text[idx] = chapter_text
                append_to_file(output_path, chapter_text, overwrite=first_saved_chapter)
                first_saved_chapter = False
                print(f"  [保存] 本章已写入: {output_path}")
            else:
                print(f"  [警告] 未找到章节正文: {chapter_url}")
        else:
            print(f"  [警告] 无法获取章节页面: {chapter_url}")
        
        if idx + 1 < total:
            print(f"  [限速] 等待 {CHAPTER_REQUEST_INTERVAL_SECONDS} 秒后继续...")
            time.sleep(CHAPTER_REQUEST_INTERVAL_SECONDS)

    save_to_file(meta['title'], meta['author'], page_text, timer=timer, save_path=output_path)

if __name__ == "__main__":
    main()
