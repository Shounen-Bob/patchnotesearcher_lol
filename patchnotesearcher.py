import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Back, Style
from tqdm import tqdm
from urllib.parse import urlparse
import sys


init()

# patchnote.txt ファイルから URL を読み込む
try:
    with open('patchnote.txt', 'r') as file:
        urls = file.readlines()
except FileNotFoundError:
    print("エラー：patchnote.txtが見つかりません。")
    print("起動前にpatchnote.txtにパッチノートのURLを一行ずつ記載し、同ディレクトリに格納してください。")
    input()
    sys.exit(1)  # 処理を終了させる

# ユーザーから検索キーワードを入力してもらう
search_keyword = input('検索するキーワードを入力してください: ')

# ヴォイド勢の名前を変換
if search_keyword == "レクサイ":
    search_keyword = "レク＝サイ"
if search_keyword == "カイサ":
    search_keyword = "カイ＝サ"
if search_keyword == "カジックス":
    search_keyword = "カ＝ジックス"    
if search_keyword == "コグマウ":
    search_keyword = "コグ＝マウ" 
if search_keyword == "チョガス":
    search_keyword = "チョ＝ガス"
if search_keyword == "ベルヴェス":
    search_keyword = "ベル＝ヴェス"
if search_keyword == "ヴェルコズ":
    search_keyword = "ヴェル＝コズ" 

# 間違えやすい名前を変換
if search_keyword == "ベルコズ":
    search_keyword = "ヴェル＝コズ"
if search_keyword == "マスターイー":
    search_keyword = "マスター・イー"
    

# 各 URL に対して処理を行う
tqdm.write(f'{search_keyword}をパッチノートから検索中')
progress_bar = tqdm(total=len(urls), desc='進捗', leave=False)# 進捗バーの設定 Falseにしているのに残り続けている気がする
for url in urls:
    url = url.strip()  # 余分な空白や改行を削除
    try:
        # URL から HTML を取得
        response = requests.get(url)
        response.raise_for_status()  # ステータスコードが 200 以外の場合は例外を発生させる
        html_content = response.text
    except requests.RequestException as e:
        progress_bar.update(1)  # 進捗バーを更新
        continue  # 次の URL へ処理を移行

    # BeautifulSoup を使って HTML を解析
    soup = BeautifulSoup(html_content, 'html.parser')

    # h3 と h4 タグを検索
    parsed_url = urlparse(url)
    last_path = parsed_url.path.strip('/').split('/')[-1]
    tqdm.write(last_path)
    for tag in soup.find_all(['h3', 'h4']):
        if search_keyword in tag.text:
            # タグのテキストを表示
            tqdm.write(Back.RED +tag.text.strip()+ Back.RESET)
            if tag.name == 'h3':
                # h3 タグの次の h4 タグまでの範囲を検索
                for sibling in tag.find_next_siblings():
                    if sibling.name == 'h4':
                        tqdm.write(Back.BLUE +'    ' + sibling.text.strip()+ Back.RESET)
                        ul_tag = sibling.find_next_sibling('ul')
                        if ul_tag:
                            for li in ul_tag.find_all('li'):
                                tqdm.write(Fore.GREEN +'        ' + li.text+ Fore.RESET)
                    elif sibling.name == 'h3':
                        break  # 次の h3 タグが見つかったら終了
            elif tag.name == 'h4':
                # h4 タグの直後の ul タグを取得
                ul_tag = tag.find_next_sibling('ul')
                if ul_tag:
                    for li in ul_tag.find_all('li'):
                        tqdm.write('    ' + li.text)
    else:
        tqdm.write('（他）変更なし')
    progress_bar.update(1)  # 進捗バーを更新
    tqdm.write('---')  # URL ごとに区切り線を表示
    

input()