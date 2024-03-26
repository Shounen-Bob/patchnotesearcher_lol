import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Back, Style
from tqdm import tqdm
from urllib.parse import urlparse
import sys
from namechange import namechange

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

# namechange.pyで必要に応じてワードを変換する
search_keyword = namechange(search_keyword)

# 各 URL に対して処理を行う
tqdm.write(f'{search_keyword}をパッチノートから検索中')
progress_bar = tqdm(total=len(urls), desc='進捗', leave=False)# 進捗バーの設定 Falseにしているのに残り続けている気がする
for url in urls:
    url = url.strip()  # 余分な空白や改行を削除
    try:
        # URL から HTML を取得
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()  # ステータスコードが 200 以外の場合は例外を発生させる

        html_content = response.text

    except requests.RequestException as e:
        remaining_progress = len(urls) - progress_bar.n  # 残りの進捗量
        progress_bar.update(remaining_progress)  # 進捗バーを100%に更新
        break

    # BeautifulSoup を使って HTML を解析
    soup = BeautifulSoup(html_content, 'html.parser')

    # <time datetime=で始まるタグを探し出す
    time_tags = soup.find_all('time', attrs={'datetime': True})
    # datetime属性の値を取得してpatchdateに格納
    for tag in time_tags:
        patchdatefull = tag['datetime']
    # datetimeの文字列の左１０ケタを取り出す
    patchdate = patchdatefull[:10]
    # h3 と h4 タグを検索
    parsed_url = urlparse(url)
    last_path = parsed_url.path.strip('/').split('/')[-1]
    tqdm.write(last_path)
    tqdm.write(f"{Fore.BLUE}適用日時:{patchdate}{Fore.RESET}")
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
    
tqdm.write('GG!パッチノートからの抽出が終わりました！') 
input()