from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

_CACHE = {}

def _cache_key(page_url, extract):
    return (page_url,getattr(extract,"__name__","extract"))

def _get_cache(key, ttl_seconds):
    if ttl_seconds <= 0:
        return None
    cached = _CACHE.get(key)
    if not cached:
        return None
    timestamp, value = cached
    if time.time() - timestamp <= ttl_seconds:
        return value
    _CACHE.pop(key, None)
    return None


def _set_cache(key, value):
  _CACHE[key] = (time.time(), value)

def build_driver(download_dir=None):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )

    if download_dir:
        prefs = {
            "download.default_directory": str(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }

        options.add_experimental_option(
            "prefs",
            prefs
        )

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    if download_dir:
        driver.execute_cdp_cmd(
            "Page.setDownloadBehavior",
            {
                "behavior": "allow",
                "downloadPath": str(download_dir),
            },
        )

    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            },
        )
    except Exception:
        pass

    return driver

GET_FULL_DOM_JS = r"""
function getShadowDOMContent(element) {
    let chunks = [];
    if (!element) return "";
    if (element.shadowRoot) {
        chunks.push("<shadow-root-start>");
        chunks.push(element.shadowRoot.innerHTML);
        chunks.push("<shadow-root-end>");
        element.shadowRoot
            .querySelectorAll("*")
            .forEach(child => {
                chunks.push(
                    getShadowDOMContent(child)
                );
            });
    }
    return chunks.join("");
}

let chunks = [];

chunks.push(
    document.documentElement.outerHTML
);

document.querySelectorAll("*")
    .forEach(el => {
        if (el.shadowRoot) {
            chunks.push(
                getShadowDOMContent(el)
            );
        }
    });

return chunks.join("");
"""

def wait_for_dom_ready(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except TimeoutException:
        pass


def scraper(page_url, extract, max_wait=30, cache_ttl=60, retries=3, backoff=1.0):
    cache_key = _cache_key(page_url, extract)
    cached = _get_cache(cache_key, cache_ttl)
    if cached is not None:
        return cached

    last_error = None
    for attempt in range(retries):
        driver = build_driver()
        try:
            driver.get(page_url)
            wait_for_dom_ready(driver)
            time.sleep(2)
            start = time.time()
            last_height = driver.execute_script(
                "return document.documentElement.scrollHeight"
            )

            while True:
                driver.execute_script(
                    "window.scrollTo(0, document.documentElement.scrollHeight);"
                )
                time.sleep(2)
                new_height = driver.execute_script(
                    "return document.documentElement.scrollHeight"
                )
                if new_height == last_height:
                    break
                last_height = new_height
                if time.time() - start > max_wait:
                    break
            
            full_html = driver.execute_script(GET_FULL_DOM_JS)

            if not full_html:
                raise RuntimeError(
                    "Failed to retrieve page HTML."
                )
            
            soup = BeautifulSoup(full_html, "html.parser")

            for tag in soup(["script","style","noscript","svg"]):
                tag.decompose()
                
            data = extract(soup)
            _set_cache(cache_key, data)
            return data
        except Exception as exc:
            last_error = exc
            time.sleep(backoff * (2 ** attempt))
        finally:
            driver.quit()

    if last_error:
        raise last_error
    return None