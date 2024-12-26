import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter.ttk import Progressbar, Style
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

VERSION = "1.3.3"

namechange = lambda keyword: {
    "レクサイ": "レク＝サイ", "カイサ": "カイ＝サ", "カジックス": "カ＝ジックス", "コグマウ": "コグ＝マウ",
    "チョガス": "チョ＝ガス", "ベルヴェス": "ベル＝ヴェス", "ヴェルコズ": "ヴェル＝コズ",
    "ベルコズ": "ヴェル＝コズ", "マスターイー": "マスター・イー"
}.get(keyword, keyword)

def generate_urls(season):
    return [
        f"https://www.leagueoflegends.com/ja-jp/news/game-updates/patch-{season}-{i:02d}-notes/"
        for i in range(1, 25)
    ]

def process_url_champion(url, keyword):
    """
    【チャンピオン検索用ロジック】
    - h3 にキーワードが含まれていれば、次の h3 までの間にある h4->ul を収集
    """
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code != 200:
            return {"error": f"Status {response.status_code}", "url": url}

        soup = BeautifulSoup(response.text, 'html.parser')
        patchdate = soup.find('time', attrs={'datetime': True})
        patch_number = url.split("/")[-2]

        entries = []
        for h3tag in soup.find_all("h3"):
            if keyword not in h3tag.get_text():
                continue

            champion_name = h3tag.get_text(strip=True)
            champ_entry = {
                "header": champion_name,
                "details": []
            }

            sibling = h3tag.next_sibling
            while sibling:
                if sibling.name == "h3":
                    break

                if sibling.name == "h4":
                    subheader_text = sibling.get_text(strip=True)
                    ul_tag = sibling.find_next_sibling("ul")
                    if ul_tag:
                        items = [li.get_text(strip=True) for li in ul_tag.find_all("li")]
                    else:
                        items = []
                    if items:
                        champ_entry["details"].append({
                            "subheader": subheader_text,
                            "items": items
                        })
                sibling = sibling.next_sibling

            if champ_entry["details"]:
                entries.append(champ_entry)

        if entries:
            return {
                "patch_number": patch_number,
                "patchdate": patchdate["datetime"][:10] if patchdate else "不明",
                "entries": entries,
                "url": url
            }
        else:
            return {}
    except Exception as e:
        return {"error": str(e), "url": url}

def process_url_item(url, keyword):
    """
    【アイテム検索用ロジック】
    - h4 にキーワードが含まれていれば、その次の h3/h4 までの間で ul があればそれを取得
    """
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code != 200:
            return {"error": f"Status {response.status_code}", "url": url}

        soup = BeautifulSoup(response.text, 'html.parser')
        patchdate = soup.find('time', attrs={'datetime': True})
        patch_number = url.split("/")[-2]

        entries = []
        for h4tag in soup.find_all("h4"):
            if keyword not in h4tag.get_text():
                continue

            item_name = h4tag.get_text(strip=True)
            item_entry = {
                "header": item_name,
                "details": []
            }

            sibling = h4tag.next_sibling
            while sibling:
                if sibling.name in ["h3", "h4"]:
                    break

                if sibling.name == "ul":
                    items = [li.get_text(strip=True) for li in sibling.find_all("li")]
                    if items:
                        item_entry["details"].append({
                            "subheader": "",
                            "items": items
                        })
                sibling = sibling.next_sibling

            if item_entry["details"]:
                entries.append(item_entry)

        if entries:
            return {
                "patch_number": patch_number,
                "patchdate": patchdate["datetime"][:10] if patchdate else "不明",
                "entries": entries,
                "url": url
            }
        else:
            return {}
    except Exception as e:
        return {"error": str(e), "url": url}

def display_results(results):
    window = tk.Toplevel(root)
    window.title("検索結果")
    window.geometry("900x600")
    text_box = scrolledtext.ScrolledText(window, wrap="word", font=("Arial", 10),
                                         bg="black", fg="white")
    text_box.pack(fill=tk.BOTH, expand=True)

    text_box.tag_configure("error", foreground="red")
    text_box.tag_configure("champion", foreground="yellow")
    text_box.tag_configure("subheader", foreground="cyan")
    text_box.tag_configure("item", foreground="lightgreen")

    text_box.insert("end", "===== パッチノート検索結果 =====\n")
    if not results:
        text_box.insert("end", "ヒットするパッチノートは見つかりませんでした。\n", "error")

    for result in results:
        if "error" in result:
            continue

        text_box.insert(
            "end",
            f"パッチノート番号: {result['patch_number']} - 適用日時: {result['patchdate']} - リンク: {result['url']}\n"
        )
        for entry in result.get("entries", []):
            text_box.insert("end", f"  {entry['header']}\n", "champion")
            for detail in entry["details"]:
                if detail["subheader"]:
                    text_box.insert("end", f"    {detail['subheader']}\n", "subheader")
                for item in detail["items"]:
                    text_box.insert("end", f"      {item}\n", "item")
        text_box.insert("end", "--------------------------------\n", "champion")

    text_box.insert("end", "================================\n")
    text_box.see("end")

def run_scraper(event=None):
    # event=None は Enterキー押下バインド対応のため
    progress_bar["value"] = 0

    season = season_entry.get().strip()
    keyword = keyword_entry.get().strip()
    if not (season.isdigit()) or not keyword:
        return messagebox.showerror("エラー", "入力を確認してください。")

    progress_bar["maximum"] = 24
    results = []

    mode = search_mode.get()
    parse_func = process_url_champion if mode == "champion" else process_url_item

    with ThreadPoolExecutor(max_workers=10) as executor:
        for i, future in enumerate(executor.map(
            lambda url: parse_func(url, namechange(keyword)),
            generate_urls(season)
        )):
            if future:
                results.append(future)
            progress_bar["value"] = i + 1
            root.update_idletasks()

    valid_results = [r for r in results if "error" not in r]
    valid_results_sorted = sorted(valid_results, key=lambda x: x.get('patch_number', ''))

    display_results(valid_results_sorted)
    progress_bar["value"] = 0

#
# GUI 構築
#
root = tk.Tk()
root.title("パッチノート検索くん")

# ある程度余裕を持たせたサイズ
root.geometry("420x240")
root.configure(bg="#2E3B4E")

# ttkのStyleを定義
style = Style(root)
# テーマを"clam"に
style.theme_use("clam")

# "Horizontal.TProgressbar" (標準のスタイル名)をカスタマイズ
style.configure(
    "Horizontal.TProgressbar",
    troughcolor="#444444",  # 溝の色(背景)
    background="#FFD700"    # バーの色
)

frame = tk.Frame(root, padx=5, pady=5, bg="#2E3B4E")
frame.pack(fill=tk.BOTH, expand=True)

# 1行目: シーズン
season_label = tk.Label(frame, text="シーズン:", bg="#2E3B4E", fg="white", font=("Arial", 9))
season_label.grid(row=0, column=0, padx=3, pady=3, sticky="e")

season_entry = tk.Entry(frame, width=8, font=("Arial", 9))
season_entry.insert(0, "14")
season_entry.grid(row=0, column=1, padx=3, pady=3, sticky="w")

# 2行目: 検索キーワード
keyword_label = tk.Label(frame, text="検索キーワード:", bg="#2E3B4E", fg="white", font=("Arial", 9))
keyword_label.grid(row=1, column=0, padx=3, pady=3, sticky="e")

keyword_entry = tk.Entry(frame, width=20, font=("Arial", 9))
keyword_entry.grid(row=1, column=1, padx=3, pady=3, sticky="w")

# ラジオボタンは tk.Radiobutton を使う
search_mode = tk.StringVar(value="champion")
rb_champion = tk.Radiobutton(
    frame, text="チャンピオン", variable=search_mode,
    value="champion", bg="#2E3B4E", fg="white",
    selectcolor="#2E3B4E", activebackground="#2E3B4E"
)
rb_champion.grid(row=2, column=0, padx=5, sticky="e")

rb_item = tk.Radiobutton(
    frame, text="アイテム", variable=search_mode,
    value="item", bg="#2E3B4E", fg="white",
    selectcolor="#2E3B4E", activebackground="#2E3B4E"
)
rb_item.grid(row=2, column=1, padx=5, sticky="w")

# 3行目: 実行ボタン + ENTERキー案内
run_button = tk.Button(
    frame, text="Go", command=run_scraper,
    bg="#FFD700", fg="black", font=("Arial", 10, "bold"), width=5
)
run_button.grid(row=3, column=0, sticky="e", padx=3, pady=3)

enter_label = tk.Label(
    frame, text="(Enterキーでも検索可能)",
    bg="#2E3B4E", fg="white", font=("Arial", 9)
)
enter_label.grid(row=3, column=1, sticky="w", padx=3, pady=3)

# 4行目: 進捗バー
progress_bar = Progressbar(
    frame, orient="horizontal", length=300, mode="determinate",
    style="Horizontal.TProgressbar"
)
progress_bar.grid(row=4, column=0, columnspan=2, padx=5, pady=8)

# 下部にバージョン表示
tk.Label(
    root, text=f"version {VERSION} by 少年ボブ",
    font=("Arial", 9), bg="#2E3B4E", fg="white"
).pack(side=tk.BOTTOM, pady=5)

# イベントバインド: シーズンEntryにフォーカスが入ったらクリア
def clear_season(*_):
    season_entry.delete(0, tk.END)

season_entry.bind("<FocusIn>", clear_season)

# Enterキーで検索
root.bind("<Return>", run_scraper)

root.mainloop()
