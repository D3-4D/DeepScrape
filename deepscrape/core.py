from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from os import devnull
from time import sleep

opt = Options()

opt.page_load_strategy = "eager"
opt.add_argument('--ignore-certificate-errors')
opt.add_argument('headless')
opt.add_argument("--log-level=3")

opt.add_experimental_option("prefs", {
    "profile.block_third_party_cookies": True,
    "enable_do_not_track": True
})

opt.add_argument("--incognito")
opt.add_argument("--disable-dev-shm-usage")
opt.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install(), log_output=devnull), options=opt)
del opt

Containers = {}

class Container:
    def __init__(self, ID, Cached=False, SegmentedRes=False, Debug=False, InternalInstruct=""):
        self.__LastM = 1
        self.EndStream = "EOF" 
        self.Instruct = "Append EOF at the end of your response."+InternalInstruct
        self.Cached = Cached
        self.SegmentedRes = SegmentedRes
        self.Debug = Debug

        driver.execute_script("window.open('https://deepai.org/chat', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        self.Tab = driver.current_window_handle
        self.ID = ID or self.Tab
        
        if Debug:
            print(f"Container '{self.ID}' was created.")
        
        Containers[self.ID] = dict(Cached=Cached,SegmentedRes=SegmentedRes,Debug=Debug) if Debug else True

    def __del(self):
        Containers.pop(self.ID)

        self.__Switch()
        driver.close()

        if self.Debug:
            print(f"Container '{self.ID}' was removed.")

    def __Switch(self):
        if driver.current_window_handle != self.Tab: #!
            driver.switch_to.window(self.Tab)
            if self.Debug:
                print(f"Switching to tab {self.Tab}.")

    def EraseHistory(self):
        self.__Switch()
        driver.refresh()
        if self.Cached:
            self.__LastM = 1

    def Request(self, Request):
        self.__Switch()
        Request = f"{self.Instruct}{Request}".replace("\n", "").replace("\n", ";")

        if self.Debug:
            print("Processing request.")

        inp = driver.find_element(By.ID, "persistentChatbox")
        
        #appear not to be working
        #driver.execute_script("""var elm = arguments[0], txt = arguments[1];
        #elm.value += txt\\n;
        #elm.dispatchEvent(new Event('change'));""", inp, Request)
        
        inp.send_keys(f"{Request}\n")
        response = Wait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='outputBox']"))
        )
        
        while len(response) < self.__LastM:
            response = Wait(driver, 1.5).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='outputBox']"))
            )
        
        response = response[-1]
        sleep(.2)
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", response)
        if self.Debug:
            print("Scroll applied.")
        response = response.find_element(By.XPATH, ".//div[@class='markdownContainer']")
        c = 0
        buffer = ""
        while not "EOF" in response.text:
            sleep(.05)
            if self.SegmentedRes:
                buffer = ""
                lastc = c
                for _ in range(3):
                    sleep(.01)
                    if len(response.text) > c:
                        if not "EOF" in response.text[c:]:
                            lenc = len(response.text)
                            buffer += response.text[c:lenc]
                            c = lenc
                        else:
                            buffer = ""
                            c = lastc
                            break
                if buffer != "":
                    yield buffer
        yield response.text[c:-3]
        if self.Cached:
            self.__LastM += 1
        else:
            self.EraseHistory()
        yield self.EndStream
