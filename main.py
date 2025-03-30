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
opt.add_argument("--headless=new")
opt.add_argument('--ignore-certificate-errors')
opt.add_argument("--log-level=3")

opt.add_experimental_option("prefs", {
    "profile.block_third_party_cookies": True,
    "enable_do_not_track": True
})

opt.add_argument("--incognito")
opt.add_argument("--disable-dev-shm-usage")
opt.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install(), log_output=devnull), options=opt)

Containers = {}

class Container:
    def __init__(self, ID, Cached=False, SegmentedRes=False, Debug=False, InternalInstruct=""):
        self.__LastM = 1
        self.Instruct = "Make sure to respond solely with characters within the BMP range and carefully verify any emojis used. "+InternalInstruct
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

    def __del__(self):
        Containers.pop(self.ID)

        self.__Switch()
        driver.close()

        if self.Debug:
            print(f"Container '{self.ID}' was removed.")

    def __Switch(self):
        if driver.current_window_handle != self.Tab:
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
        Request = f"{self.Instruct}{Request}".replace("\n", "")

        if self.Debug:
            print("Processing request.")

        inp = Wait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "chatbox"))
        )
        leng = len(inp)
        inp = inp[-1]
        driver.execute_script("""var elm = arguments[0], txt = arguments[1];
        elm.value += txt;
        elm.dispatchEvent(new Event('change'));""", inp, Request)
        inp.send_keys("\n")
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
        while len(driver.find_elements(By.CLASS_NAME, "chatbox")) == leng:
            sleep(.05)
            if self.SegmentedRes and len(response.text) > c:
                yield response.text[c:]
                c = len(response.text)
        yield response.text[c:]
        if self.Cached:
            self.__LastM += 1
        else:
            self.EraseHistory()
        yield "EOF"

if __name__ == "__main__":
    inst = "Keep responses brief. Use a natural, conversational tone and keep the dialogue flowing. Respond with another trivial question."

    C1 = Container("EmmaAI", Cached=True, InternalInstruct=inst, SegmentedRes=True)
    C2 = Container("VictorAI", Cached=True, InternalInstruct=inst, SegmentedRes=False)

    Init = "How do bees fly?"

    print(f"Conversation began:\n\n *{Init}*\n\n")

    Switch = False

    L = Init
    try:
        while True:
            Switch = not Switch
            co = C1 if Switch else C2
            Strt = co.Request(L)
            L = ""
            print(f"[{co.ID}]: ",end="")
            for x in Strt:
                if x == "EOF":
                    break
                L += x
                print(x, end="")
            print()
    except (KeyboardInterrupt, TimeoutError, EC.NoSuchElementException) as e:
        driver.close()
        print(e)
        input("\nPress enter to exit.")
        raise SystemExit
