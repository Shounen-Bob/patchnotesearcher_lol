
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