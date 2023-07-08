from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains

import os
import sys
import time
import json

import signal

class DelayedKeyboardInterrupt:

    def __enter__(self):
        self.signal_received = False
        self.old_handler = signal.signal(signal.SIGINT, self.handler)
                
    def handler(self, sig, frame):
        self.signal_received = (sig, frame)
        print('SIGINT received. Delaying KeyboardInterrupt.')

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)


class Scraper:

    def __init__(self) -> None:
        s = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()

        # options.add_argument(r"--user-data-dir=C:\Users\khana\AppData\Local\Google\Chrome\User Data\TempProfile")
        # options.add_argument(r"--profile-directory=TempProfile")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")

        self.driver = webdriver.Chrome(service=s, options=options)
        self.driver.get("https://freesearchigrservice.maharashtra.gov.in/")
        # self.driver.get("https://ip.oxylabs.io/")
        self.wait = WebDriverWait(self.driver, 20)

        self.download_tries = 0
        self.page_tries = 0

    def getElement(self,by = By.XPATH, selector = "") -> WebElement | None:
        """ Default selector is XPATH,
        use keyword argument 'selector' to pass values.
        """
        element = None
        try:
            element = self.wait.until(EC.presence_of_element_located( (by, selector) ))
        except Exception as e:
            print(e)
            print("Couldn't find Selector: " + selector)
        finally:
            return element

    def getElements(self,by = By.XPATH, selector = "") -> WebElement | None:
        """ Default selector is XPATH,
        use keyword argument 'selector' to pass values.
        """
        element = None
        try:
            element = self.wait.until(EC.presence_of_all_elements_located( (by, selector) ))
        except Exception as e:
            print(e)
            print("Couldn't find Selector: " + selector)
        finally:
            return element
    
    def waitForever(self):
        print('Stopped...')
        while True:
            time.sleep(60)

    def loading(self):
        loader = self.getElement(selector='//div[contains(@id,"UpdateProgress")]')
        counter = 0
        while loader:
            if loader.get_attribute('aria-hidden') == 'true': return False
            print('Loading...',end='\r')
            counter += 1
            if counter > 10:
                return True
            time.sleep(12)
            loader = self.getElement(selector='//div[contains(@id,"UpdateProgress")]')
        return False

    def reload(self,*args):
        year, district, tahsil, village, number = args
        print('Reloading')
        time.sleep(4)
        self.scrape(year, district, tahsil, village, number)

    def downloadHTML(self,docno):
        print('Downloading HTML, tries',self.download_tries)
        with open(f"eSearch-Forms-Pune/{docno}.html", "w", encoding='utf-8') as f:
            f.write(self.driver.page_source)

    def scrape(self,*args):
        self.driver.refresh()
        time.sleep(8)
        year, district, tahsil, village, number = args
        if "Service Unavailable" in self.driver.page_source:
            return self.reload(year, district, tahsil, village, number)
        try:
            print('Selecting Maharstra',flush=True)
            self.getElement(selector='//input[@name="btnOtherdistrictSearch"]').click()
        except Exception as e:
            print('Error in selecting Rest of Maharashtra')
            return None
        
        form = self.getElement(selector='//div[@id="otherdistrictpropsearchPanel"]')
        if not form:
            print('Input panel not loaded')
            return self.reload(year, district, tahsil, village, number)
        
        print('Selecting Year:',year,flush=True)
        year_option = self.getElement(selector=f'//option[@value="{year}"]')
        self.driver.execute_script('arguments[0].setAttribute("selected", "selected")', year_option)

        print('Selecting District:',district,flush=True) 
        dropdown = self.getElement(selector='//select[@id="ddlDistrict1"]')
        dropdown.click()
        time.sleep(8)
        for i in dropdown.find_elements(By.TAG_NAME, 'option'):
            if district == i.text.strip():
                i.click()
                time.sleep(2)
                if self.loading(): return self.reload(year, district, tahsil, village, number)
                break
        
        time.sleep(4)
        print('Selecting Tahsil:',tahsil,flush=True)
        dropdown = self.getElement(selector='//select[@id="ddltahsil"]')
        dropdown.click()
        time.sleep(8)
        for i in dropdown.find_elements(By.TAG_NAME, 'option'):
            if tahsil == i.text.strip():
                i.click()
                time.sleep(2)
                if self.loading(): return self.reload(year, district, tahsil, village, number)
                break

        time.sleep(4)
        print('Selecting Village:',village,flush=True)
        dropdown = self.getElement(selector='//select[@id="ddlvillage"]')
        dropdown.click()
        time.sleep(8)
        for i in dropdown.find_elements(By.TAG_NAME, 'option'):
            if village == i.text.strip():
                i.click()
                time.sleep(2)
                if self.loading(): return self.reload(year, district, tahsil, village, number)
                break
        
        time.sleep(4)
        print('Selecting Property:',number,flush=True)
        p = self.getElement(selector='//input[@id="txtAttributeValue1"]')
        p.send_keys(number)
        time.sleep(4)

        print('Entering captcha',flush=True)
        capcha = self.getElement(selector='//input[contains(@id,"txtCaptcha")]').get_attribute('value')
        captch_input = self.getElement(selector='//input[contains(@id,"txtImg")]')
        self.driver.execute_script(f'arguments[0].setAttribute("value", "{capcha}")', captch_input)
        time.sleep(4)

        print('Searching',flush=True)
        search = self.getElement(selector='//input[@id="btnSearch_RestMaha"]').click()
        time.sleep(4)
        if self.loading(): return self.reload(year, district, tahsil, village, number)
        time.sleep(4)
        
        result_table = self.getElement(selector='//table[@id="RegistrationGrid"]')
        if not result_table:
            print('No results')
            return {'message':'No results'}
        
        rows = result_table.find_elements(By.XPATH,'.//tr[contains(@style,"background-color")]')
        total_page = 1
        if rows[-1].get_attribute('align') == 'left':
            total_page = len(rows[-1].find_elements(By.XPATH,'.//td')) - 1
        
        all_results = []
        print('Total Page:',total_page,flush=True)
        for page in range(total_page):
            result_table = self.getElement(selector='//table[@id="RegistrationGrid"]')
            rows = result_table.find_elements(By.XPATH,'.//tr[contains(@style,"background-color")]')

            if total_page-1 >= page >= 1:
                actionChains = ActionChains(self.driver)
                npage = rows[-1].find_elements(By.XPATH,'.//td')[page+1]
                print('clicking next page',npage.text,flush=True)
                cur_detail = next_detail = rows[1].text
                self.page_tries = 0
                while cur_detail == next_detail:
                    self.page_tries += 1
                    if self.page_tries >= 15:
                        return all_results
                    print('Checking Next Page',flush=True)
                    actionChains.double_click(npage).perform()
                    time.sleep(20)
                    result_table = self.getElement(selector='//table[@id="RegistrationGrid"]')
                    rows = result_table.find_elements(By.XPATH,'.//tr[contains(@style,"background-color")]')
                    next_detail = rows[1].text
            else:
                print('first page')

            total_rows = len(rows) - 1
            row_index = 1
            while row_index <= total_rows:
                result_table = self.getElement(selector='//table[@id="RegistrationGrid"]')
                temp_row = result_table.find_elements(By.XPATH,'.//tr[contains(@style,"background-color")]')[row_index]

                col = temp_row.find_elements(By.XPATH,'.//td')
                last_col =  len(col) - 1
                res_list = []
                for index, data in enumerate(col):
                    if index != last_col:
                        res_list.append(data.text)
                        continue
                    
                    docno: str = res_list[0]+'/'+year
                    try:
                        link = data.find_element(By.XPATH,'.//input').click()
                    except:
                        row_index += 1
                        continue
                    time.sleep(6)
                    if len(self.driver.window_handles) >= 1:
                        self.driver.switch_to.window(self.driver.window_handles[1])
                    else:
                        continue
                    if docno in self.driver.page_source:
                        print('Saving Page Source,',self.download_tries,flush=True)
                        docno = self.driver.page_source
                        all_results.append({
                            'DocNo': res_list[0],
                            'DName': res_list[1],
                            'RDate': res_list[2],
                            'SROName': res_list[3],
                            'Seller Name': res_list[4],
                            'Purchaser Name': res_list[5],
                            'Property Description': res_list[6],
                            'SROCode': res_list[7],
                            'Status': res_list[8],
                            'Index': docno
                        })
                        row_index += 1
                        self.download_tries = 0
                    else:
                        self.download_tries += 1
                        if self.download_tries >= 15:
                            self.download_tries = 0
                            return all_results
                    time.sleep(6)
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])

        self.driver.refresh()
        return all_results

    def scrapeInputs(self):
        self.driver.refresh()
        time.sleep(2)
        if "Service Unavailable" in self.driver.page_source:
            return self.scrapeInputs()
        try:
            print('Selecting Maharstra')
            self.getElement(selector='//input[@name="btnOtherdistrictSearch"]').click()
        except Exception as e:
            print('Error in selecting Rest of Maharashtra')
            return {'message':'Error in selecting Rest of Maharashtra'}

        form = self.getElement(selector='//div[@id="otherdistrictpropsearchPanel"]')
        if not form:
            print('Input panel not loaded')
            return self.scrapeInputs()
        
        inputs: dict[str,dict[str,list]] = {}

        dd = self.getElement(selector='//select[@id="ddlDistrict1"]')
        time.sleep(5)
        for i in range(1,len(dd.find_elements(By.TAG_NAME, 'option'))):
            dd = self.getElement(selector='//select[@id="ddlDistrict1"]')
            dd.click()
            time.sleep(5)
            district = dd.find_elements(By.TAG_NAME, 'option')[i]
            if district.text != 'पुणे': continue
            print('Selecting District:',district.text)
            if self.loading(): return self.scrapeInputs()

            d = district.text
            inputs[d] = {}

            district.click()
            if self.loading(): return self.scrapeInputs()
            time.sleep(5)
            
            td = self.getElement(selector='//select[@id="ddltahsil"]')
            for j in range(1,len(td.find_elements(By.TAG_NAME, 'option'))):

                td = self.getElement(selector='//select[@id="ddltahsil"]')
                td.click()
                time.sleep(5)
                tahsil = td.find_elements(By.TAG_NAME, 'option')[j]
                print('Selecting Tahsil:',tahsil.text)
                
                if self.loading(): return self.scrapeInputs()
                t = tahsil.text
                inputs[d][t] = []

                tahsil.click()
                if self.loading(): return self.scrapeInputs()
                time.sleep(5)
                
                vd = self.getElement(selector='//select[@id="ddlvillage"]')
                for village in vd.find_elements(By.TAG_NAME, 'option')[1:]:
                    # print('Selecting Village:',village.text)
                    inputs[d][t].append(village.text)
            break

        file = 'maha_eSearch'
        with open(f"{file}_Inputs.json", "w", encoding='utf-8') as jsonFile:
            json.dump(inputs, jsonFile, indent=4, ensure_ascii=False)


def updateJSON(file: str, newdata: list):
    if os.path.exists(f"{file}.json"):
        if os.stat(f"{file}.json").st_size == 0: open(f"{file}.json", "w", encoding='utf-8').write('[]')
        with open(f"{file}.json", "r", encoding='utf-8') as jsonFile:
            data: list = json.load(jsonFile)
        data.extend(newdata)
    else:
        data = newdata

    with open(f"{file}.json", "w", encoding='utf-8') as jsonFile:
        json.dump(data, jsonFile, indent=2, ensure_ascii=False)

bot = Scraper()


file = "30May"
with open(f"{file}.json", "r", encoding='utf-8') as jsonFile:
    data: dict[str,dict[str,list[str]]] = json.load(jsonFile)



count = 0
query = {}
query['Year'] = '2021'
query['district'] = 'पुणे'
for tahsil, villages in data['पुणे'].items():
#   if tahsil != 'जुन्नर': continue
    query['tahsil'] = tahsil
    for village in villages:
        query['Village'] = village
        for i in range(10):
            query['Property_number'] = i

            json_list = []

            skip = False
            if os.path.exists(f"{file}_results.json"):
                with open(f"{file}_results.json", "r", encoding='utf-8') as jsonFile:
                 data = jsonFile.read()
                 old_data=None
                 if flag == False:
                    old_data: list = json.load(jsonFile)
                r: dict[str, dict]
                if old_data!=None:
                 for r in old_data:
                    c = 0
                    for k,v in set(r['input'].items()) & set(query.items()): c+= 1
                    if c == 5:
                        skip = True
                        count += 1
                        print('already scraped',count,end='\r',flush=True)
                        break
            
            if skip: continue

            print('Scraping')
            try:
                result = bot.scrape(query['Year'].strip(),query['district'].strip(),
                            query['tahsil'].strip(),query['Village'].strip(),
                            query['Property_number'])
                print('Sleep... 10 min',flush=True)
                count += 1
                print('Scraped',count,flush=True)
                time.sleep(60)
            except Exception as e:
                print(e)
                result = None
                # exc_type, exc_obj, exc_tb = sys.exc_info()
                # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                # print(exc_type, fname, exc_tb.tb_lineno)

            if result:
                json_list.append({
                    'input': query,
                    'results': result
                })
                print('Saving to File')

                with DelayedKeyboardInterrupt():
                    updateJSON(f"{file}_results",json_list)
