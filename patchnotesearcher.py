import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Back, Style
from tqdm import tqdm
from urllib.parse import urlparse
import sys
from concurrent.futures import ThreadPoolExecutor
from namechange import namechange

init()

# patchnote.txt ファイルから URL を読み込む
try:
    with open('patchnote.txt', 'r') as file:
        urls = [url.strip() for url in file.readlines()]
except FileNotFoundError:
    print("エラー：patchnote.txtが見つかりません。")
    print("起動前にpatchnote.txtにパッチノートのURLを一行ずつ記載し、同ディレクトリに格納してください。")
    sys.exit(1)  # 処理を終了させる

# コマンドライン引数またはデフォルト値から検索キーワードを取得
if len(sys.argv) > 1:
    search_keyword = sys.argv[1]
else:
    try:
        search_keyword = input("検索キーワードを入力してください: ")
    except (EOFError, RuntimeError):
        search_keyword = "デフォルトキーワード"  # デフォルトの検索キーワードを設定

# namechange.pyで必要に応じてワードを変換する
search_keyword = namechange(search_keyword)

# 検索結果を保持するリスト
results = []

def process_url(url):
    try:
        # URL から HTML を取得
        response = requests.get(url, allow_redirects=True, timeout=10)
        if response.status_code == 404:
            return None  # 404エラーの場合はスキップ
        response.raise_for_status()  # ステータスコードが 200 以外の場合は例外を発生させる

        html_content = response.text
    except requests.RequestException:
        return None

    # BeautifulSoup を使って HTML を解析
    soup = BeautifulSoup(html_content, 'html.parser')

    # <time datetime=で始まるタグを探し出す
    time_tag = soup.find('time', attrs={'datetime': True})
    patchdate = time_tag['datetime'][:10] if time_tag else "不明"

    # パッチノート番号を取得
    parsed_url = urlparse(url)
    patch_number = parsed_url.path.strip('/').split('/')[-1]

    # h3 と h4 タグを検索
    found_entries = []
    for tag in soup.find_all(['h3', 'h4']):
        if search_keyword in tag.text:
            entry = {"patch_number": patch_number, "patchdate": patchdate, "header": tag.text.strip(), "url": url}
            if tag.name == 'h3':
                entry['details'] = []
                for sibling in tag.find_next_siblings():
                    if sibling.name == 'h4':
                        entry['details'].append({
                            "subheader": sibling.text.strip(),
                            "items": [li.text.strip() for li in sibling.find_next_sibling('ul').find_all('li')] if sibling.find_next_sibling('ul') else []
                        })
                    elif sibling.name == 'h3':
                        break
            elif tag.name == 'h4':
                entry['details'] = [{
                    "subheader": tag.text.strip(),
                    "items": [li.text.strip() for li in tag.find_next_sibling('ul').find_all('li')] if tag.find_next_sibling('ul') else []
                }]
            found_entries.append(entry)

    if found_entries:
        return {"patch_number": patch_number, "patchdate": patchdate, "entries": found_entries, "url": url}
    return None

# スレッドプールを使用してURLを並列処理
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(process_url, url) for url in urls]
    for future in tqdm(futures, desc="進捗", leave=False):
        result = future.result()
        if result:
            results.append(result)

# パッチノート番号でソートして結果を表示
results.sort(key=lambda x: x['patch_number'])

for result in results:
    tqdm.write(f"{Fore.BLUE}パッチノート番号: {result['patch_number']} - 適用日時: {result['patchdate']} - リンク: {result['url']}{Fore.RESET}")
    for entry in result['entries']:
        tqdm.write(f"{Back.RED}{entry['header']}{Back.RESET}")
        for detail in entry.get('details', []):
            tqdm.write(f"    {Back.BLUE}{detail['subheader']}{Back.RESET}")
            for item in detail.get('items', []):
                tqdm.write(f"        {Fore.GREEN}{item}{Fore.RESET}")
    tqdm.write("---")

tqdm.write('GG!パッチノートからの抽出が終わりました！')
