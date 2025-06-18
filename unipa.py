import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import subprocess
import os

################################
# 基本的なブラウザ操作
################################

def setup_driver():
    """
    Chromeドライバーを設定して返す
    Linux環境での安定性を向上させるためのオプションを追加
    """
    chrome_options = Options()
    
    # Linux環境での安定性向上オプション
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # 画像読み込みを無効化して高速化
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    # ユーザーエージェントを設定
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # ウィンドウサイズを設定
    chrome_options.add_argument("--window-size=1920,1080")
    
    # メモリ使用量を制限
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--max_old_space_size=4096")
    
    try:
        # ChromeDriverのパスを自動検出
        chromedriver_path = None
        
        # 方法1: PATHから検索
        try:
            result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
            if result.returncode == 0:
                chromedriver_path = result.stdout.strip()
                print(f"ChromeDriverをPATHから発見: {chromedriver_path}")
        except:
            pass
        
        # 方法2: 一般的な場所を確認
        if chromedriver_path is None:
            common_paths = [
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver',
                '/snap/bin/chromedriver',
                './chromedriver'
            ]
            for path in common_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    print(f"ChromeDriverを発見: {chromedriver_path}")
                    break
        
        # 方法3: ChromeDriverをダウンロード
        if chromedriver_path is None:
            print("ChromeDriverが見つかりません。自動ダウンロードを試行します...")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                chromedriver_path = ChromeDriverManager().install()
                print(f"ChromeDriverをダウンロード: {chromedriver_path}")
            except ImportError:
                print("webdriver-managerがインストールされていません。")
                print("以下のコマンドでインストールしてください:")
                print("pip install webdriver-manager")
                raise Exception("ChromeDriverが見つからず、自動ダウンロードもできません")
        
        # Serviceオブジェクトを作成
        service = Service(executable_path=chromedriver_path)
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.maximize_window()
        
        # ページ読み込みタイムアウトを設定
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        print("Chromeドライバーの初期化が完了しました")
        return driver
        
    except Exception as e:
        print(f"Chromeドライバーの初期化に失敗: {e}")
        print("ヘッドレスモードで再試行します...")
        
        # ヘッドレスモードで再試行
        chrome_options.add_argument("--headless")
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            print("ヘッドレスモードでChromeドライバーの初期化が完了しました")
            return driver
        except Exception as e2:
            print(f"ヘッドレスモードでも初期化に失敗: {e2}")
            print("\nChromeDriverのインストール方法:")
            print("1. ChromeDriverをダウンロード: https://chromedriver.chromium.org/")
            print("2. ダウンロードしたファイルを解凍")
            print("3. chromedriverを/usr/local/bin/に移動: sudo mv chromedriver /usr/local/bin/")
            print("4. 実行権限を付与: sudo chmod +x /usr/local/bin/chromedriver")
            raise e2

def open_syllabus_site(driver, url):
    driver.get(url)

def select_all_gakki(driver):
    """
    「開講年度学期」を「すべて対象」に変更
    """
    print("開講年度学期の選択を開始します...")
    
    # ページが完全に読み込まれるまで待機
    time.sleep(3)
    
    wait = WebDriverWait(driver, 20)  # タイムアウトを20秒に延長
    
    try:
        # まず、ページが完全に読み込まれているか確認
        print("ページの読み込み状況を確認中...")
        
        # 複数の方法で要素を検索
        label = None
        
        # 方法1: IDで検索
        try:
            label = wait.until(EC.element_to_be_clickable((By.ID, "funcForm:kaikoGakki_label")))
            print("IDで要素を発見しました")
        except:
            print("IDでの要素検索に失敗、他の方法を試行中...")
        
        # 方法2: ラベルテキストで検索
        if label is None:
            try:
                label = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//label[contains(text(), '開講年度学期') or contains(text(), '年度学期')]")
                ))
                print("ラベルテキストで要素を発見しました")
            except:
                print("ラベルテキストでの要素検索に失敗...")
        
        # 方法3: より広範囲のXPathで検索
        if label is None:
            try:
                label = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[contains(@class, 'ui-selectonemenu')]//label")
                ))
                print("XPathで要素を発見しました")
            except:
                print("XPathでの要素検索に失敗...")
        
        # 方法4: CSSセレクタで検索
        if label is None:
            try:
                label = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "label.ui-selectonemenu-label")
                ))
                print("CSSセレクタで要素を発見しました")
            except:
                print("CSSセレクタでの要素検索に失敗...")
        
        if label is None:
            raise Exception("開講年度学期の選択要素が見つかりません")
        
        # 要素が見えるようにスクロール
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
        time.sleep(2)
        
        # クリック
        print("開講年度学期の選択ボックスをクリック中...")
        label.click()
        time.sleep(2)
        
        # 「すべて対象」オプションを選択
        print("「すべて対象」オプションを検索中...")
        
        all_option = None
        
        # 方法1: 元のXPath
        try:
            all_option = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//li[@class='ui-selectonemenu-item ui-selectonemenu-list-item ui-corner-all' and @data-label='すべて対象']")
            ))
            print("元のXPathで「すべて対象」オプションを発見しました")
        except:
            print("元のXPathでの検索に失敗、他の方法を試行中...")
        
        # 方法2: テキストで検索
        if all_option is None:
            try:
                all_option = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//li[contains(text(), 'すべて対象')]")
                ))
                print("テキストで「すべて対象」オプションを発見しました")
            except:
                print("テキストでの検索に失敗...")
        
        # 方法3: より広範囲の検索
        if all_option is None:
            try:
                all_option = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//li[contains(@class, 'ui-selectonemenu-item') and contains(text(), 'すべて')]")
                ))
                print("広範囲検索で「すべて対象」オプションを発見しました")
            except:
                print("広範囲検索に失敗...")
        
        if all_option is None:
            raise Exception("「すべて対象」オプションが見つかりません")
        
        # オプションが見えるようにスクロール
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", all_option)
        time.sleep(1)
        
        # クリック
        print("「すべて対象」を選択中...")
        all_option.click()
        time.sleep(2)
        
        print("開講年度学期の選択が完了しました")
        
    except Exception as e:
        print(f"開講年度学期の選択中にエラーが発生: {e}")
        print("現在のページのHTMLを確認中...")
        
        # デバッグ用：現在のページのHTMLを出力
        try:
            page_source = driver.page_source
            print("ページのHTML（最初の1000文字）:")
            print(page_source[:1000])
        except:
            print("HTMLの取得に失敗しました")
        
        # 代替手段：手動で要素を探す
        print("代替手段として、手動で要素を探します...")
        try:
            # ページ内のすべてのラベル要素を確認
            labels = driver.find_elements(By.TAG_NAME, "label")
            print(f"ページ内のラベル要素数: {len(labels)}")
            for i, lbl in enumerate(labels[:5]):  # 最初の5個のみ表示
                print(f"  ラベル{i+1}: {lbl.text} (ID: {lbl.get_attribute('id')})")
            
            # セレクトメニュー要素を確認
            select_menus = driver.find_elements(By.CSS_SELECTOR, ".ui-selectonemenu")
            print(f"セレクトメニュー要素数: {len(select_menus)}")
            
            if select_menus:
                print("最初のセレクトメニューをクリックしてみます...")
                select_menus[0].click()
                time.sleep(2)
                
                # ドロップダウンのオプションを確認
                options = driver.find_elements(By.CSS_SELECTOR, ".ui-selectonemenu-item")
                print(f"ドロップダウンオプション数: {len(options)}")
                for opt in options:
                    print(f"  オプション: {opt.text}")
                    if "すべて" in opt.text:
                        print("「すべて」を含むオプションをクリックします...")
                        opt.click()
                        time.sleep(2)
                        break
        except Exception as debug_e:
            print(f"デバッグ処理中にエラー: {debug_e}")
        
        raise e

################################
# 曜日チェック ON/OFF
################################

def set_checkbox(driver, day_value, check=True):
    """
    曜日チェックボックスを ON / OFF する。
      - day_value: "1"(月), "2"(火), ... "7"(日)
      - check: True ならチェック, False なら解除
    """
    try:
        # オーバーレイが消えるのを待つ
        wait = WebDriverWait(driver, 10)
        wait.until(EC.invisibility_of_element_located((By.ID, "j_idt39_blocker")))
        
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
    except Exception as e:
        print(f"チェックボックスの操作中にエラーが発生: {e}")
        # エラーが発生した場合、少し待ってから再試行
        time.sleep(2)
        try:
            checkbox_div.click()
        except:
            print("再試行も失敗しました")

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
        time.sleep(4)
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
        link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, link_xpath))
        )
        print(f"\n    詳細情報を取得中: {link.text} (ページ {current_page}, インデックス {actual_index})")

        # クリック前に要素が表示されていることを確認
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
        time.sleep(1)

        link.click()
        time.sleep(2)

        # ダイアログの要素を取得
        dialog = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#pkx02301\\:dialog"))
        )
        
        # ダイアログが完全に表示されるまで待機
        time.sleep(1)

        # ダイアログ内のコンテンツ要素を取得
        content = dialog.find_element(By.CSS_SELECTOR, ".ui-dialog-content")
        
        # スクロールしながら情報を取得
        details = {}
        last_height = driver.execute_script("return arguments[0].scrollHeight", content)
        scroll_count = 0
        
        # 基本情報の取得
        basic_info_xpath = "//div[@id='pkx02301:ch:table']//div[contains(@class, 'rowStyle')]"
        basic_info_rows = content.find_elements(By.XPATH, basic_info_xpath)
        
        for row in basic_info_rows:
            try:
                header = row.find_element(By.XPATH, ".//div[contains(@class, 'ui-widget-header')]").text.strip()
                value_elem = row.find_element(By.XPATH, ".//div[contains(@class, 'fr-box fr-view')]")
                
                # DPの場合はテーブル形式を保持
                if header == "DP":
                    value = value_elem.get_attribute('innerHTML')
                else:
                    value = value_elem.text.strip()
                
                if header and value:
                    details[header] = value
                    print(f"      {header}を取得")
            except:
                continue

        # 授業内容（全16回）
        class_contents = []
        prep_contents = []
        
        print("\n    授業内容の取得を開始...")
        # 授業内容の取得
        for i in range(16):
            try:
                content_xpath = f"//div[contains(@class, 'rowStyle')]//label[contains(text(), '第{i+1}回')]/ancestor::div[contains(@class, 'rowStyle')]//div[contains(@class, 'fr-box fr-view')]"
                print(f"      第{i+1}回のXPath: {content_xpath}")
                content_elem = content.find_element(By.XPATH, content_xpath)
                if content_elem:
                    content_text = content_elem.text.strip()
                    class_contents.append(f"第{i+1}回: {content_text}")
                    print(f"      第{i+1}回の内容: {content_text}")
            except NoSuchElementException:
                print(f"      第{i+1}回の内容が見つかりません")
                continue

        print("\n    準備学習の取得を開始...")
        # 準備学習の取得
        for i in range(16):
            try:
                prep_xpath = f"//div[contains(@class, 'rowStyle')]//label[contains(text(), '第{i+1}回')]/ancestor::div[contains(@class, 'rowStyle')]//div[contains(@class, 'fr-box fr-view')]"
                print(f"      準備学習_第{i+1}回のXPath: {prep_xpath}")
                prep_elem = content.find_element(By.XPATH, prep_xpath)
                if prep_elem:
                    prep_text = prep_elem.text.strip()
                    prep_contents.append(f"第{i+1}回: {prep_text}")
                    print(f"      準備学習_第{i+1}回の内容: {prep_text}")
            except NoSuchElementException:
                print(f"      準備学習_第{i+1}回の内容が見つかりません")
                continue

        # 授業内容と準備学習を個別のフィールドとして保存
        if class_contents:
            details['授業内容（全16回）'] = '\n'.join(class_contents)
            for i, content in enumerate(class_contents, 1):
                details[f'第{i}回'] = content.split(': ', 1)[1] if ': ' in content else content
            print("\n      授業内容の取得完了")

        if prep_contents:
            details['準備学習（全16回）'] = '\n'.join(prep_contents)
            for i, content in enumerate(prep_contents, 1):
                details[f'準備学習_第{i}回'] = content.split(': ', 1)[1] if ': ' in content else content
            print("      準備学習の取得完了")

        # スクロール
        driver.execute_script("arguments[0].scrollTop += 500", content)
        time.sleep(1)
        scroll_count += 1

        # 新しい高さを取得
        new_height = driver.execute_script("return arguments[0].scrollHeight", content)
        
        # スクロールが終端に達したら終了
        if new_height == last_height:
            print(f"      スクロール完了（{scroll_count}回）")
        
        # ダイアログを閉じる
        close_button = dialog.find_element(By.CSS_SELECTOR, ".ui-dialog-titlebar-close")
        close_button.click()
        time.sleep(1)
        print("      詳細情報の取得完了")

        return details

    except Exception as e:
        print(f"    シラバス詳細の取得中にエラーが発生: {e}")
        # エラーが発生した場合でも、ダイアログを閉じることを試みる
        try:
            close_button = driver.find_element(By.CSS_SELECTOR, ".ui-dialog-titlebar-close")
            close_button.click()
            time.sleep(1)
        except:
            pass
        return {}

################################
# CSV出力
################################

def save_to_csv(data, filename):
    """
    データをCSVファイルに保存する
    """
    if not data:
        print(f"保存するデータがありません: {filename}")
        return

    # 希望するフィールド順序を定義
    desired_fields = [
        "授業コード", "科目ナンバリング", "科目名", "科目名（英語）", "同時開講科目",
        "科目授業種別", "授業名", "担当教員名", "対象学部学科", "対象学年",
        "単位数", "開講学期", "曜日時限", "教室", "授業実施形態",
        "他学科履修可否", "DP", "講義目的", "達成目標", "成績評価",
        "試験実施", "授業内容（全16回）",
        "第1回", "第2回", "第3回", "第4回", "第5回",
        "第6回", "第7回", "第8回", "第9回", "第10回",
        "第11回", "第12回", "第13回", "第14回", "第15回", "第16回",
        "準備学習（全16回）",
        "準備学習_第1回", "準備学習_第2回", "準備学習_第3回", "準備学習_第4回", "準備学習_第5回",
        "準備学習_第6回", "準備学習_第7回", "準備学習_第8回", "準備学習_第9回", "準備学習_第10回",
        "準備学習_第11回", "準備学習_第12回", "準備学習_第13回", "準備学習_第14回", "準備学習_第15回", "準備学習_第16回",
        "教科書販売", "教科書", "参考書", "関連科目", "キーワード",
        "授業の運営方針", "アクティブラーニングを促すための手法", "アクティブラーニング",
        "課題に対するフィードバック", "合理的配慮が必要な学生への対応",
        "実務経験のある教員", "その他（注意・備考）", "連絡先"
    ]

    # 基本情報のフィールド（既存のデータに含まれる可能性のあるフィールド）
    basic_fields = ["開講区分", "担当教員", "授業科目", "曜日", "開講年度学期", "row_index"]

    # 全てのデータから一意のフィールド名を収集
    all_fields = set()
    for row in data:
        all_fields.update(row.keys())

    # 希望するフィールド順序を維持しつつ、存在するフィールドのみを含める
    fieldnames = [f for f in desired_fields if f in all_fields]
    
    # 基本情報のフィールドを追加（存在する場合）
    fieldnames.extend([f for f in basic_fields if f in all_fields])
    
    # その他のフィールドを追加（存在する場合）
    remaining_fields = sorted(list(all_fields - set(fieldnames)))
    fieldnames.extend(remaining_fields)

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                # 存在しないフィールドには空文字を設定
                row_data = {field: row.get(field, '') for field in fieldnames}
                writer.writerow(row_data)
        print(f"データを保存しました: {filename}")
    except Exception as e:
        print(f"CSVファイルの保存中にエラーが発生: {e}")
        # エラーの詳細を表示
        print("フィールド名:", fieldnames)
        print("データのキー:", list(data[0].keys()) if data else "データなし")

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
            all_results.extend(page_data)  # 修正: インデントを修正し、page_dataを一度だけ追加

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
    print("テスト完了: syllabus_results_monday_test.csv に保存しました")

def main():
    try:
        print("=== シラバススクレイピング開始 ===")
        print("Linux環境での実行を検出しました。安定性向上オプションを適用中...")
        
        # 1. 基本情報の取得
        print("基本情報の取得を開始します...")
        basic_data = scrape_basic_info_for_all_days()
        
        # 2. 詳細情報の取得
        print("詳細情報の取得を開始します...")
        scrape_detailed_info_for_all_days(basic_data)
        
        print("=== スクレイピング完了 ===")
        
    except KeyboardInterrupt:
        print("\nユーザーによって中断されました。")
        print("ブラウザを終了中...")
        try:
            # グローバル変数でdriverを管理していないため、ここでは終了処理のみ
            pass
        except:
            pass
        print("プログラムを終了します。")
        
    except Exception as e:
        print(f"\n予期しないエラーが発生しました: {e}")
        print("エラーの詳細:")
        import traceback
        traceback.print_exc()
        
        print("\nトラブルシューティングのヒント:")
        print("1. Chromeブラウザがインストールされているか確認してください")
        print("2. ChromeDriverがPATHに含まれているか確認してください")
        print("3. インターネット接続を確認してください")
        print("4. 必要に応じて、ChromeDriverを手動でダウンロードしてください")
        
        try:
            # ブラウザを終了
            pass
        except:
            pass

if __name__ == "__main__":
    main()
