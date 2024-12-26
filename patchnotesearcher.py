import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Back, Style
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

init()

def namechange(search_keyword):
    # ヴォイド勢の名前を変換
    if search_keyword == "レクサイ":
        return "レク＝サイ"
    if search_keyword == "カイサ":
        return "カイ＝サ"
    if search_keyword == "カジックス":
        return "カ＝ジックス"    
    if search_keyword == "コグマウ":
        return "コグ＝マウ" 
    if search_keyword == "チョガス":
        return "チョ＝ガス"
    if search_keyword == "ベルヴェス":
        return "ベル＝ヴェス"
    if search_keyword == "ヴェルコズ":
        return "ヴェル＝コズ" 

    # 間違えやすい名前を変換
    if search_keyword == "ベルコズ":
        return "ヴェル＝コズ"
    if search_keyword == "マスターイー":
        return "マスター・イー"
    return search_keyword

# シーズンとキーワードの入力を求める
try:
    season = input("シーズンの数字を入力してください（例: 14）: ").strip()
    search_keyword = input("検索キーワードを入力してください: ").strip()
    search_keyword = namechange(search_keyword)
except Exception as e:
    print(f"入力エラー: {e}")
    exit(1)

# URLを生成
base_url = "https://www.leagueoflegends.com/ja-jp/news/game-updates/"
urls = [f"{base_url}patch-{season}-{i:02d}-notes/" for i in range(1, 25)]

# 検索結果を保持するリスト
results = []

def process_url(url):
    try:
        # URL から HTML を取得
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
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
    patch_number = url.split("/")[-2]

    # h3 と h4 タグを検索
    found_entries = []
    for tag in soup.find_all(['h3', 'h4']):
        if search_keyword in tag.text:
            entry = {"patch_number": patch_number, "patchdate": patchdate, "header": tag.text.strip(), "url": url}
            if tag.name == 'h3':
                entry['details'] = []
                for sibling in tag.find_next_siblings():
                    if sibling.name == 'h4':
                        subheader = sibling.text.strip()
                        items = []

                        next_tag = sibling.find_next_sibling()
                        if next_tag and next_tag.name == 'ul':
                            items.extend([li.get_text(separator=" ").strip() for li in next_tag.find_all('li')])
                        while next_tag and next_tag.name in ['li', 'p']:
                            if next_tag.name == 'li':
                                items.append(next_tag.get_text(separator=" ").strip())
                            elif next_tag.name == 'p':
                                items.append(next_tag.text.strip())
                            next_tag = next_tag.find_next_sibling()

                        entry['details'].append({
                            "subheader": subheader,
                            "items": items
                        })
                    elif sibling.name == 'h3':
                        break
            elif tag.name == 'h4':
                subheader = tag.text.strip()
                items = []

                next_tag = tag.find_next_sibling()
                if next_tag and next_tag.name == 'ul':
                    items.extend([li.get_text(separator=" ").strip() for li in next_tag.find_all('li')])
                while next_tag and next_tag.name in ['li', 'p']:
                    if next_tag.name == 'li':
                        items.append(next_tag.get_text(separator=" ").strip())
                    elif next_tag.name == 'p':
                        items.append(next_tag.text.strip())
                    next_tag = next_tag.find_next_sibling()

                entry['details'] = [{
                    "subheader": subheader,
                    "items": items
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