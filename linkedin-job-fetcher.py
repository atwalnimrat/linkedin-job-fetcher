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
        
    # Avoid detection nudges
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options) if driver is None else driver
    driver.maximize_window()
    driver.get("https://www.linkedin.com/login")

    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.ID, "username")))
    driver.find_element(By.ID, "username").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password + Keys.RETURN)

    # Wait for post-login redirect
    try:
        wait.until(
            EC.presence_of_element_located((By.ID, "global-nav-search"))
        )
    except TimeoutException:
        time.sleep(2)
    return driver


def wait_for_job_cards_stable(driver, timeout=10, poll_interval=0.5, stable_for=1.0):
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
                return cards            # stable snapshot
        else:
            last_count = count
            stable_start = None
        last_cards = cards
        time.sleep(poll_interval)
    return last_cards                   # timeout -> return last seen


def fetch_jobs(driver, location, keywords, max_jobs=50, auto_scroll=True):
    driver.get("https://www.linkedin.com/jobs")
    wait = WebDriverWait(driver, 15)
    used_layout = None

    try:
        # Layout A: two separate inputs
        keywords_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//input[contains(@aria-label,"Search jobs") or contains(@placeholder,"Search jobs")]')
            )
        )
        location_input = driver.find_element(
            By.XPATH,
            '//input[contains(@aria-label,"Search location") or contains(@placeholder,"Search location")]',
        )
        keywords_input.clear()
        keywords_input.send_keys(keywords)
        location_input.clear()
        location_input.send_keys(location)
        location_input.send_keys(Keys.RETURN)
        used_layout = "A"
    except Exception:
        try:
            # Layout B: single combined search bar
            keywords_input = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//input[contains(@aria-label,"Search by title") or contains(@placeholder,"Search jobs")]')
                )
            )
            search_query = f"{keywords} {location}".strip()
            keywords_input.clear()
            keywords_input.send_keys(search_query)
            keywords_input.send_keys(Keys.RETURN)
            used_layout = "B"
        except Exception:
            try:
                # Layout C: search button first
                search_button = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//button[contains(@aria-label,"Search jobs") or contains(text(),"Search jobs")]')
                    )
                )
                search_button.click()
                keywords_input = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//input[contains(@aria-label,"Search by") or contains(@placeholder,"Search jobs")]')
                    )
                )
                keywords_input.clear()
                keywords_input.send_keys(f"{keywords} {location}".strip())
                keywords_input.send_keys(Keys.RETURN)
                used_layout = "C"
            except Exception as e:
                print("[ERROR] Could not find any job search input.", e)
                return []

    print(f"[INFO] Using layout {used_layout} for search")
    time.sleep(2)

    # --- Auto scroll ---
    if auto_scroll:
        last_count, retries = 0, 0
        while True:
            cards = driver.find_elements(By.CSS_SELECTOR, "div.job-card-job-posting-card-wrapper")
            if len(cards) >= max_jobs:
                break
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(1)
            new_count = len(driver.find_elements(By.CSS_SELECTOR, "div.job-card-job-posting-card-wrapper"))
            if new_count == last_count:
                retries += 1
            else:
                retries, last_count = 0, new_count
            if retries >= 3 or new_count >= max_jobs:
                break

    # --- Job cards ---
    job_cards = driver.find_elements(By.CSS_SELECTOR, "div.job-card-job-posting-card-wrapper")
    if not job_cards:
        print("[INFO] No job cards found.")
        return []

    results = []
    limit = min(len(job_cards), max_jobs)
    print(f"[INFO] Found {len(job_cards)} job cards (scraping up to {limit}).\n")

    for idx, card in enumerate(job_cards[:limit], start=1):
        try:
            title = card.find_element(By.CSS_SELECTOR, ".job-card-job-posting-card-wrapper__title").text.strip()
        except:
            title = "N/A"

        try:
            company = card.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle").text.strip()
        except:
            company = "N/A"

        try:
            loc = card.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__caption").text.strip()
        except:
            loc = "N/A"

        results.append({"title": title, "company": company, "location": loc})
        print(f"{idx}. {title}\n   {company}\n   {loc}\n")

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
