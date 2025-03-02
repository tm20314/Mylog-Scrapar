import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

################################
# 基本的なブラウザ操作
################################

def setup_driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    return driver

def open_syllabus_site(driver, url):
    driver.get(url)

def select_all_gakki(driver):
    """
    「開講年度学期」を「すべて対象」に変更
    """
    wait = WebDriverWait(driver, 10)
    
    label = wait.until(EC.element_to_be_clickable((By.ID, "funcForm:kaikoGakki_label")))
    label.click()
    time.sleep(1)
    
    all_option = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//li[@class='ui-selectonemenu-item ui-selectonemenu-list-item ui-corner-all' and @data-label='すべて対象']")
    ))
    all_option.click()
    time.sleep(1)

################################
# 曜日チェック ON/OFF
################################

def set_checkbox(driver, day_value, check=True):
    """
    曜日チェックボックスを ON / OFF する。
      - day_value: "1"(月), "2"(火), ... "7"(日)
      - check: True ならチェック, False なら解除
    """
    # 該当の <input> 要素を検索
    # 例: <input id="funcForm:yobiList:0" name="funcForm:yobiList" type="checkbox" value="1" ...>
    input_xpath = f"//input[@name='funcForm:yobiList' and @value='{day_value}']"
    checkbox_input = driver.find_element(By.XPATH, input_xpath)
    
    # 見た目上のクリック対象 (親の .ui-chkbox-box)
    checkbox_div = checkbox_input.find_element(
        By.XPATH,
        "./ancestor::div[@class='ui-chkbox ui-widget']/div[contains(@class, 'ui-chkbox-box')]"
    )
    
    is_checked = checkbox_input.is_selected()
    if check and not is_checked:
        checkbox_div.click()
    elif (not check) and is_checked:
        checkbox_div.click()
    
    time.sleep(1)

def uncheck_all_days(driver):
    """
    万一、前の曜日がチェックのまま残っていたら全OFFにしたい場合に使用。
    """
    for v in ["1","2","3","4","5","6","7"]:
        set_checkbox(driver, v, check=False)

################################
# 検索 + ページネーション処理
################################

def click_search(driver):
    """
    「検索」ボタンを押して、結果のテーブルが表示されるまで待機
    """
    search_button = driver.find_element(By.ID, "funcForm:search")
    search_button.click()
    
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "funcForm:table_data")))
    time.sleep(2)  # Ajax完了後の描画待ち

def scroll_to_bottom(driver, times=2):
    """下までスクロールして遅延読み込み対策"""
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

def scrape_result_table(driver):
    """
    ページ内の結果テーブル( funcForm:table_data )の行を取得して返す。
    """
    data_list = []
    try:
        scroll_to_bottom(driver, times=2)
        tbody = driver.find_element(By.ID, "funcForm:table_data")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 6:
                continue
            yoyobi_jigen = cells[0].text.strip()
            jugyo_kamoku = cells[1].text.strip()
            tanto_kyoin  = cells[2].text.strip()
            kaiko_kubun  = cells[3].text.strip()
            nendo_gakki  = cells[4].text.strip()
            tanisu       = cells[5].text.strip()
            
            data_list.append({
                "曜日時限": yoyobi_jigen,
                "授業科目": jugyo_kamoku,
                "担当教員": tanto_kyoin,
                "開講区分": kaiko_kubun,
                "開講年度学期": nendo_gakki,
                "単位数": tanisu
            })
    except Exception as e:
        print("テーブル解析エラー:", e)
    return data_list

def get_total_pages(driver):
    """
    ページャの「(1 / 4)」等を読み取り、総ページ数を返す。
    例: <span class="ui-paginator-current">366件 (1 / 4)</span>
    """
    paginator_text = driver.find_element(By.CSS_SELECTOR, "#funcForm\\:table_paginator_bottom .ui-paginator-current").text
    # 例: "366件 (1 / 4)"
    start = paginator_text.find("(")
    end   = paginator_text.find(")")
    if start == -1 or end == -1:
        return 1  # なければ1ページだけ
    page_info = paginator_text[start+1:end]  # "1 / 4"
    _, total_str = page_info.split("/")
    total_pages = int(total_str.strip())
    return total_pages

def go_to_page(driver, page_num):
    """
    指定ページ番号をクリックして移動
    """
    wait = WebDriverWait(driver, 10)
    pagination = wait.until(EC.visibility_of_element_located((By.ID, "funcForm:table_paginator_bottom")))

    # XPath 例: <span class="ui-paginator-page ui-state-default..." tabindex="0">2</span>
    # normalize-space で前後余白除去
    page_xpath = f".//span[contains(@class, 'ui-paginator-page') and normalize-space(text())='{page_num}']"
    page_span = pagination.find_element(By.XPATH, page_xpath)

    # 画面内にスクロール
    driver.execute_script("arguments[0].scrollIntoView(true);", page_span)
    time.sleep(1)

    # クリック
    page_span.click()
    
    wait.until(EC.presence_of_element_located((By.ID, "funcForm:table_data")))
    time.sleep(1)

def get_data_for_day(driver):
    """
    ページネーション付きのデータ取得:
      - 1ページ目は既に表示されている想定
      - 総ページ数を読み取り, 2～最終ページを順にクリックして取得
      - 全ページぶんの行を合体して返す
    """
    all_data = []
    
    # 1ページ目 (現状表示中)
    data_p1 = scrape_result_table(driver)
    all_data.extend(data_p1)
    
    # 残りページ
    total_pages = get_total_pages(driver)
    print("総ページ数:", total_pages)

    for p in range(2, total_pages + 1):
        go_to_page(driver, p)
        data_px = scrape_result_table(driver)
        all_data.extend(data_px)

    return all_data

################################
# CSV出力
################################

def save_to_csv(data, filename="syllabus_result.csv"):
    if not data:
        print("データがありません。")
        return
    headers = data[0].keys()
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"CSV保存完了: {filename}")

################################
# メイン
################################

def main():
    url = "https://mylog.pub.ous.ac.jp/uprx/up/pk/pky001/Pky00101.xhtml?guestlogin=Kmh006"
    driver = setup_driver()
    open_syllabus_site(driver, url)

    # 1) 「開講年度学期」を「すべて対象」に
    select_all_gakki(driver)

    # 曜日ごとに検索→ページネーション取得→曜日OFF
    day_values = ["1","2","3","4","5","6","7"]  # 月～日
    all_results = []

    # 念のため最初に全曜日OFFにしておく
    uncheck_all_days(driver)

    for dv in day_values:
        # 1) dv の曜日だけ ON
        set_checkbox(driver, dv, check=True)
        
        # 2) 検索ボタン押下 → 結果1ページ目表示
        click_search(driver)

        # 3) ページをめくりながらデータを取得
        day_data = get_data_for_day(driver)
        # 各行に「検索曜日」など付加したい場合は、下記のように:
        for row in day_data:
            row["曜日"] = dv  # "1"=月, "2"=火, ...

        all_results.extend(day_data)

        # 4) dv の曜日を OFF (次の曜日に行く前に外す)
        set_checkbox(driver, dv, check=False)

    # 全曜日ぶんが終了したら CSV 化
    save_to_csv(all_results, "syllabus_results_all_days.csv")

    driver.quit()

if __name__ == "__main__":
    main()
