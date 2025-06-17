import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
    input_xpath = f"//input[@name='funcForm:yobiList' and @value='{day_value}']"
    checkbox_input = driver.find_element(By.XPATH, input_xpath)
    
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

def get_total_pages(driver):
    """
    総ページ数を取得
    """
    try:
        # ページネーション要素を取得
        pagination = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "funcForm:table_paginator_bottom"))
        )
        
        # すべてのページ番号を取得
        page_numbers = pagination.find_elements(By.CSS_SELECTOR, "span.ui-paginator-page")
        
        if not page_numbers:
            print("  ページ番号が見つかりません。1ページのみと判断します。")
            return 1
            
        # 最大ページ番号を取得
        max_page = max([int(page.text.strip()) for page in page_numbers if page.text.strip().isdigit()])
        print(f"  検出された最大ページ数: {max_page}")
        
        # 念のため、最後のページに移動して確認
        last_page = page_numbers[-1]
        driver.execute_script("arguments[0].scrollIntoView(true);", last_page)
        time.sleep(2)
        last_page.click()
        time.sleep(3)
        
        # 最後のページの要素数を確認
        rows = driver.find_elements(By.CSS_SELECTOR, "#funcForm\\:table_data tr")
        if len(rows) > 0:
            print(f"  最終ページの確認完了: {max_page}ページ目に{len(rows)}件のデータがあります")
        else:
            print("  警告: 最終ページにデータが見つかりません")
            
        # 1ページ目に戻る
        first_page = pagination.find_element(By.CSS_SELECTOR, "span.ui-paginator-page")
        driver.execute_script("arguments[0].scrollIntoView(true);", first_page)
        time.sleep(2)
        first_page.click()
        time.sleep(3)
        
        # ページネーションのテキストからもページ数を確認
        try:
            paginator_text = driver.find_element(By.CSS_SELECTOR, "#funcForm\\:table_paginator_bottom .ui-paginator-current").text
            start = paginator_text.find("(")
            end = paginator_text.find(")")
            if start != -1 and end != -1:
                page_info = paginator_text[start+1:end]
                _, total_str = page_info.split("/")
                text_total_pages = int(total_str.strip())
                print(f"  ページネーションテキストから取得した総ページ数: {text_total_pages}")
                
                # 両方の方法で取得したページ数を比較
                if text_total_pages > max_page:
                    print(f"  警告: ページネーションテキストの方が大きい値です。{text_total_pages}ページとして処理を続行します。")
                    max_page = text_total_pages
        except Exception as e:
            print(f"  ページネーションテキストの取得に失敗: {e}")
        
        return max_page
        
    except Exception as e:
        print(f"  ページ数取得エラー: {e}")
        return 1

def go_to_page(driver, page_num):
    """
    指定ページ番号をクリックして移動
    """
    wait = WebDriverWait(driver, 10)  # タイムアウトを10秒に短縮
    pagination = wait.until(EC.visibility_of_element_located((By.ID, "funcForm:table_paginator_bottom")))

    page_xpath = f".//span[contains(@class, 'ui-paginator-page') and normalize-space(text())='{page_num}']"
    page_span = pagination.find_element(By.XPATH, page_xpath)

    # ページャーが見えるようにスクロール
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", page_span)
    time.sleep(1)  # 待機時間を短縮

    # クリック
    page_span.click()
    time.sleep(2)  # 待機時間を短縮
    
    # テーブルが表示されるまで待機
    wait.until(EC.presence_of_element_located((By.ID, "funcForm:table_data")))
    time.sleep(1)  # 待機時間を短縮

    # ページ上部に移動
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)  # 待機時間を短縮

    # テーブルが完全に読み込まれるまで待機
    try:
        # テーブルの行要素が存在することを確認
        wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "#funcForm\\:table_data tr")) > 0)
        time.sleep(1)  # 待機時間を短縮
        
        # テーブルの内容が完全に読み込まれるまで待機
        wait.until(lambda driver: all(
            len(cell.text.strip()) > 0 
            for cell in driver.find_elements(By.CSS_SELECTOR, "#funcForm\\:table_data td")
        ))
        time.sleep(1)  # 待機時間を短縮
        
        print(f"    ページ {page_num} の読み込み完了")
    except Exception as e:
        print(f"    警告: ページ {page_num} の読み込み待機中にエラーが発生: {e}")
        print("    処理を続行します")

################################
# 基本情報の取得
################################

def scrape_basic_info(driver):
    """
    ページ内の結果テーブルの基本情報を取得
    """
    data_list = []
    try:
        print("  テーブルの基本情報を取得中...")
        scroll_to_bottom(driver, times=2)
        tbody = driver.find_element(By.ID, "funcForm:table_data")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        
        for i, row in enumerate(rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 6:
                continue
            yoyobi_jigen = cells[0].text.strip()
            jugyo_kamoku = cells[1].text.strip()
            tanto_kyoin  = cells[2].text.strip()
            kaiko_kubun  = cells[3].text.strip()
            nendo_gakki  = cells[4].text.strip()
            tanisu       = cells[5].text.strip()
            
            print(f"    授業 {i+1}: {jugyo_kamoku} ({tanto_kyoin})")
            
            row_data = {
                "曜日時限": yoyobi_jigen,
                "授業科目": jugyo_kamoku,
                "担当教員": tanto_kyoin,
                "開講区分": kaiko_kubun,
                "開講年度学期": nendo_gakki,
                "単位数": tanisu,
                "row_index": i  # 後で詳細情報を取得する際に使用
            }
            data_list.append(row_data)
            
    except Exception as e:
        print("  テーブル解析エラー:", e)
    return data_list

################################
# 詳細情報の取得
################################

def get_syllabus_details(driver, row_index, current_page):
    """
    授業名のリンクをクリックして詳細情報を取得する
    current_page: 現在のページ番号（1から始まる）
    """
    try:
        # ページ番号に基づいてIDのインデックスを計算
        base_index = (current_page - 1) * 100
        actual_index = base_index + row_index
        
        # 授業名のリンクをクリック
        link_xpath = f"//a[@id='funcForm:table:{actual_index}:jugyoKmkName']"
        link = WebDriverWait(driver, 10).until(  # タイムアウトを10秒に短縮
            EC.element_to_be_clickable((By.XPATH, link_xpath))
        )
        print(f"    詳細情報を取得中: {link.text} (ページ {current_page}, インデックス {actual_index})")
        
        # クリック前に要素が表示されていることを確認
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
        time.sleep(1)  # 待機時間を短縮
        
        link.click()
        time.sleep(2)  # 待機時間を短縮

        # ダイアログの要素を取得
        dialog = WebDriverWait(driver, 10).until(  # タイムアウトを10秒に短縮
            EC.presence_of_element_located((By.CSS_SELECTOR, "#pkx02301\\:dialog"))
        )
        
        # ダイアログが完全に表示されるまで待機
        time.sleep(1)  # 待機時間を短縮
        
        # ダイアログ内のコンテンツ要素を取得
        content = dialog.find_element(By.CSS_SELECTOR, ".ui-dialog-content")
        
        # スクロールしながら情報を取得
        details = {}
        last_height = driver.execute_script("return arguments[0].scrollHeight", content)
        scroll_count = 0
        
        # 一度に取得する情報のリスト
        info_to_get = [
            ("基本情報", ".//div[contains(@class, 'ui-g')]"),
            ("講義目的", ".//div[contains(text(), '講義目的')]/following-sibling::div//div[@class='fr-box fr-view']"),
            ("達成目標", ".//div[contains(text(), '達成目標')]/following-sibling::div//div[@class='fr-box fr-view']"),
            ("成績評価", ".//div[contains(text(), '成績評価')]/following-sibling::div//div[@class='fr-box fr-view']"),
            ("教科書", ".//div[contains(text(), '教科書')]/following-sibling::div//div[@class='fr-box fr-view']"),
            ("参考書", ".//div[contains(text(), '参考書')]/following-sibling::div//div[@class='fr-box fr-view']"),
            ("関連科目", ".//div[contains(text(), '関連科目')]/following-sibling::div//div[@class='fr-box fr-view']"),
            ("キーワード", ".//div[contains(text(), 'キーワード')]/following-sibling::div//div[@class='fr-box fr-view']"),
            ("授業の運営方針", ".//div[contains(text(), '授業の運営方針')]/following-sibling::div//div[@class='fr-box fr-view']"),
            ("連絡先", ".//div[contains(text(), '連絡先')]/following-sibling::div//div[@class='fr-box fr-view']")
        ]
        
        while True:
            # 現在表示されている情報を取得
            try:
                for label, xpath in info_to_get:
                    if label not in details:  # まだ取得していない情報のみ取得
                        try:
                            if label == "基本情報":
                                basic_info = content.find_elements(By.XPATH, xpath)
                                for info in basic_info:
                                    try:
                                        info_label = info.find_element(By.XPATH, ".//div[contains(@class, 'ui-g-2')]").text.strip()
                                        info_value = info.find_element(By.XPATH, ".//div[contains(@class, 'ui-g-10')]").text.strip()
                                        if info_label and info_value:
                                            details[info_label] = info_value
                                    except:
                                        continue
                            else:
                                elem = content.find_element(By.XPATH, xpath)
                                if elem:
                                    details[label] = elem.text.strip()
                                    print(f"      {label}を取得")
                        except NoSuchElementException:
                            continue

                # 授業内容（全16回）
                if '授業内容' not in details:
                    contents = []
                    for i in range(16):
                        try:
                            content_xpath = f".//div[contains(text(), '授業内容（全16回）')]/following-sibling::div[{i+1}]//div[@class='fr-box fr-view']"
                            content_elem = content.find_element(By.XPATH, content_xpath)
                            if content_elem:
                                contents.append(f"第{i+1}回: {content_elem.text.strip()}")
                        except NoSuchElementException:
                            continue
                    if contents:
                        details['授業内容'] = '\n'.join(contents)
                        print("      授業内容を取得")

                # 準備学習（全16回）
                if '準備学習' not in details:
                    preparations = []
                    for i in range(16):
                        try:
                            prep_xpath = f".//div[contains(text(), '準備学習（全16回）')]/following-sibling::div[{i+1}]//div[@class='fr-box fr-view']"
                            prep_elem = content.find_element(By.XPATH, prep_xpath)
                            if prep_elem:
                                preparations.append(f"第{i+1}回: {prep_elem.text.strip()}")
                        except NoSuchElementException:
                            continue
                    if preparations:
                        details['準備学習'] = '\n'.join(preparations)
                        print("      準備学習を取得")

            except NoSuchElementException:
                pass

            # スクロール
            driver.execute_script("arguments[0].scrollTop += 500", content)  # スクロール量を増やす
            time.sleep(1)  # 待機時間を短縮
            scroll_count += 1

            # 新しい高さを取得
            new_height = driver.execute_script("return arguments[0].scrollHeight", content)
            
            # スクロールが終端に達したら終了
            if new_height == last_height:
                print(f"      スクロール完了（{scroll_count}回）")
                break
            last_height = new_height

        # ダイアログを閉じる
        close_button = dialog.find_element(By.CSS_SELECTOR, ".ui-dialog-titlebar-close")
        close_button.click()
        time.sleep(1)  # 待機時間を短縮
        print("      詳細情報の取得完了")

        return details

    except Exception as e:
        print(f"    シラバス詳細の取得中にエラーが発生: {e}")
        # エラーが発生した場合でも、ダイアログを閉じることを試みる
        try:
            close_button = driver.find_element(By.CSS_SELECTOR, ".ui-dialog-titlebar-close")
            close_button.click()
            time.sleep(1)  # 待機時間を短縮
        except:
            pass
        return {}

################################
# CSV出力
################################

def save_to_csv(data, filename):
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
# メイン処理
################################

def scrape_basic_info_for_all_days():
    """
    全曜日の基本情報を取得
    """
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
        print(f"曜日 {dv} の基本情報を取得中...")
        # 1) dv の曜日だけ ON
        set_checkbox(driver, dv, check=True)
        
        # 2) 検索ボタン押下 → 結果1ページ目表示
        click_search(driver)

        # 3) ページをめくりながらデータを取得
        total_pages = get_total_pages(driver)
        print(f"総ページ数: {total_pages}")

        for page in range(1, total_pages + 1):
            print(f"ページ {page}/{total_pages} を処理中...")
            if page > 1:
                go_to_page(driver, page)
            
            page_data = scrape_basic_info(driver)
            # 各行に「検索曜日」を付加
            for row in page_data:
                row["曜日"] = dv  # "1"=月, "2"=火, ...
            all_results.extend(page_data)

        # 4) dv の曜日を OFF (次の曜日に行く前に外す)
        set_checkbox(driver, dv, check=False)

    # 全曜日ぶんが終了したら CSV 化
    save_to_csv(all_results, "syllabus_results_basic.csv")
    driver.quit()
    return all_results

def scrape_detailed_info_for_all_days(basic_data):
    """
    全曜日の詳細情報を取得
    """
    url = "https://mylog.pub.ous.ac.jp/uprx/up/pk/pky001/Pky00101.xhtml?guestlogin=Kmh006"
    driver = setup_driver()
    open_syllabus_site(driver, url)

    # 1) 「開講年度学期」を「すべて対象」に
    select_all_gakki(driver)

    # 曜日ごとに検索→詳細情報取得→曜日OFF
    day_values = ["1","2","3","4","5","6","7"]  # 月～日
    all_results = []

    # 念のため最初に全曜日OFFにしておく
    uncheck_all_days(driver)

    for dv in day_values:
        print(f"\n曜日 {dv} の詳細情報を取得中...")
        # 1) dv の曜日だけ ON
        set_checkbox(driver, dv, check=True)
        
        # 2) 検索ボタン押下 → 結果1ページ目表示
        click_search(driver)
        time.sleep(3)  # 検索結果の表示を待つ

        # 3) ページをめくりながらデータを取得
        total_pages = get_total_pages(driver)
        print(f"総ページ数: {total_pages}")

        for page in range(1, total_pages + 1):
            print(f"\nページ {page}/{total_pages} を処理中...")
            if page > 1:
                go_to_page(driver, page)
                time.sleep(3)  # ページ遷移後の待機時間を追加
            
            # 現在のページの行を取得
            tbody = driver.find_element(By.ID, "funcForm:table_data")
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            
            if not rows:
                print(f"  警告: ページ {page} にデータが見つかりません。再試行します。")
                # ページを再読み込み
                go_to_page(driver, page)
                time.sleep(3)
                tbody = driver.find_element(By.ID, "funcForm:table_data")
                rows = tbody.find_elements(By.TAG_NAME, "tr")
            
            print(f"  ページ {page} の行数: {len(rows)}")
            
            for i, row in enumerate(rows):
                # 基本情報を取得
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 6:
                    continue
                
                row_data = {
                    "曜日時限": cells[0].text.strip(),
                    "授業科目": cells[1].text.strip(),
                    "担当教員": cells[2].text.strip(),
                    "開講区分": cells[3].text.strip(),
                    "開講年度学期": cells[4].text.strip(),
                    "単位数": cells[5].text.strip(),
                    "曜日": dv
                }
                
                # 詳細情報を取得（ページ番号を渡す）
                details = get_syllabus_details(driver, i, page)
                row_data.update(details)
                
                all_results.append(row_data)

        # 4) dv の曜日を OFF (次の曜日に行く前に外す)
        set_checkbox(driver, dv, check=False)
        time.sleep(2)  # チェックボックス操作後の待機時間を追加

    # 全曜日ぶんが終了したら CSV 化
    save_to_csv(all_results, "syllabus_results_detailed.csv")
    driver.quit()

def main():
    # 1. 基本情報の取得
    print("基本情報の取得を開始します...")
    basic_data = scrape_basic_info_for_all_days()
    
    # 2. 詳細情報の取得
    print("詳細情報の取得を開始します...")
    scrape_detailed_info_for_all_days(basic_data)

if __name__ == "__main__":
    main()
