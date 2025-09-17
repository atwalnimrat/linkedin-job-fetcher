from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
import time


def login_to_linkedin(email, password, driver=None, headless=False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
    # optional: avoid detection nudges
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options) if driver is None else driver
    driver.maximize_window()
    driver.get("https://www.linkedin.com/login")

    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.ID, "username")))
    driver.find_element(By.ID, "username").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password + Keys.RETURN)

    # wait for post-login redirect (presence of profile nav or jobs link)
    try:
        wait.until(
            EC.presence_of_element_located((By.ID, "global-nav-search"))
        )
    except TimeoutException:
        # fallback: presence of avatar or nav
        time.sleep(2)
    return driver


def wait_for_job_cards_stable(driver, timeout=10, poll_interval=0.5, stable_for=1.0):
    """
    Wait until the number of job-card-container elements is stable for `stable_for` seconds.
    Returns the list (snapshot) of elements when stable or whatever was last found on timeout.
    """
    end_time = time.time() + timeout
    last_count = -1
    stable_start = None
    last_cards = []
    while time.time() < end_time:
        cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, .jobs-search-results__list-item")
        count = len(cards)
        if count == last_count:
            if stable_start is None:
                stable_start = time.time()
            elif time.time() - stable_start >= stable_for:
                return cards  # stable snapshot
        else:
            last_count = count
            stable_start = None
        last_cards = cards
        time.sleep(poll_interval)
    return last_cards  # timeout -> return last seen


def fetch_jobs(driver, location, keywords, max_jobs=50, auto_scroll=True):
    driver.get("https://www.linkedin.com/jobs")
    wait = WebDriverWait(driver, 15)

    # Try layouts in order: A -> B -> C
    used_layout = None
    try:
        # Layout A (two inputs)
        keywords_input = wait.until(
            EC.presence_of_element_located((By.XPATH, '//input[contains(@aria-label,"Search jobs") or contains(@placeholder,"Search jobs")]'))
        )
        location_input = driver.find_element(By.XPATH, '//input[contains(@aria-label,"Search location") or contains(@placeholder,"Search location")]')

        keywords_input.clear()
        keywords_input.send_keys(keywords)
        location_input.clear()
        location_input.send_keys(location)
        location_input.send_keys(Keys.RETURN)
        used_layout = "A"
    except Exception:
        try:
            # Layout B (single search bar)
            keywords_input = wait.until(
                EC.presence_of_element_located((By.XPATH, '//input[contains(@aria-label,"Search by title") or contains(@aria-label,"Search by title, skill, or company")]'))
            )
            keywords_input.clear()
            search_query = f"{keywords} {location}".strip()
            keywords_input.send_keys(search_query)
            keywords_input.send_keys(Keys.RETURN)
            used_layout = "B"
        except Exception:
            # Layout C: click a "Search jobs" button / icon to open search control
            try:
                search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label,"Search jobs") or contains(text(),"Search jobs")]')))
                search_button.click()
                # then wait for an input to appear
                keywords_input = wait.until(
                    EC.presence_of_element_located((By.XPATH, '//input[contains(@aria-label,"Search by") or contains(@placeholder,"Search jobs")]'))
                )
                keywords_input.clear()
                keywords_input.send_keys(f"{keywords} {location}".strip())
                keywords_input.send_keys(Keys.RETURN)
                used_layout = "C"
            except Exception as e:
                print("[ERROR] Could not find any job search input on the page.", e)
                return []

    # allow results to load a little
    time.sleep(1)

    # optional auto-scrolling to load more results
    if auto_scroll:
        # attempt to scroll until enough jobs are loaded or no more loading
        last_count = 0
        retries = 0
        while True:
            cards = wait_for_job_cards_stable(driver, timeout=5)
            if len(cards) >= max_jobs:
                break
            # scroll to bottom of results area
            try:
                # try to scroll the results list container if present
                results_container = driver.find_element(By.CSS_SELECTOR, ".jobs-search-results-list, .jobs-search-results")
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", results_container)
            except Exception:
                # fallback: page-level scroll
                driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(1)
            cards_after = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, .jobs-search-results__list-item")
            if len(cards_after) == last_count:
                retries += 1
            else:
                retries = 0
                last_count = len(cards_after)
            if retries >= 3:
                break
            if len(cards_after) >= max_jobs:
                break

    # get a stable snapshot of job cards
    job_cards = wait_for_job_cards_stable(driver, timeout=8)
    if not job_cards:
        print("[INFO] No job cards found.")
        return []

    results = []
    limit = min(len(job_cards), max_jobs)
    print(f"[INFO] Using Layout {used_layout}. Found {len(job_cards)} job cards (scraping up to {limit}).\n")

    for idx in range(limit):
        # we will attempt to get a fresh reference if stale
        tries = 0
        while tries < 2:
            try:
                card = job_cards[idx]
                # sometimes the snapshot element is stale if page re-rendered - get fresh by index
                try:
                    # defensive: attempt to read title/company/location from the card
                    # title
                    title = "N/A"
                    company = "N/A"
                    loc = "N/A"

                    # multi-selector for title
                    title_selectors = [
                        ".job-card-list__title",
                        ".job-card-container__link",
                        ".job-card-listing__title",
                        "a.job-card-list__title",
                        "a[href*='/jobs/view']"
                    ]
                    for sel in title_selectors:
                        try:
                            el = card.find_element(By.CSS_SELECTOR, sel)
                            text = el.text.strip()
                            if text:
                                title = text
                                break
                        except Exception:
                            continue

                    # company
                    company_selectors = [
                        ".job-card-container__company-name",
                        ".job-card-container__primary-description",
                        ".job-card-list__company-name",
                        ".job-card__company-name"
                    ]
                    for sel in company_selectors:
                        try:
                            el = card.find_element(By.CSS_SELECTOR, sel)
                            text = el.text.strip()
                            if text:
                                company = text
                                break
                        except Exception:
                            continue

                    # location
                    location_selectors = [
                        ".job-card-container__metadata-item",
                        ".job-card-list__location",
                        ".job-card__location",
                        ".job-card-container__location"
                    ]
                    for sel in location_selectors:
                        try:
                            el = card.find_element(By.CSS_SELECTOR, sel)
                            text = el.text.strip()
                            if text:
                                loc = text
                                break
                        except Exception:
                            continue

                    # Immediately create a plain dict (no element refs kept)
                    results.append({"title": title, "company": company, "location": loc})
                    print(f"{idx+1}. {title}\n   {company}\n   {loc}\n")
                    break  # success -> break retry loop

                except StaleElementReferenceException:
                    # refresh snapshot and retry once
                    job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, .jobs-search-results__list-item")
                    tries += 1
                    time.sleep(0.25)
                    continue

            except IndexError:
                # out of range because DOM changed and list shorter; refresh snapshot and try again
                job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, .jobs-search-results__list-item")
                if idx >= len(job_cards):
                    # nothing more to scrape
                    break
                tries += 1
        else:
            print(f"{idx+1}. Skipped due to repeated stale/index issues")

    return results


def main():
    print("Login details\n")
    email = input("Enter your email: ").strip()
    password = input("Enter your password: ").strip()
    print("\nSearch details\n")
    location = input("Enter location: ").strip()
    keywords = input("Enter job: ").strip()

    driver = login_to_linkedin(email, password)
    jobs = fetch_jobs(driver, location, keywords, max_jobs=50, auto_scroll=True)

    print(f"\nScraped {len(jobs)} job(s).")
    driver.quit()


if __name__ == "__main__":
    main()
