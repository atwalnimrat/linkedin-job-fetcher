from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time


def login_to_linkedin(email, password):
    # Initialize the Chrome driver
    driver = webdriver.Chrome()
    driver.get('https://www.linkedin.com/login')

    # Enter email and password to login
    email_input = driver.find_element(By.ID, 'username')
    email_input.send_keys(email)

    password_input = driver.find_element(By.ID, 'password')
    password_input.send_keys(password)

    password_input.send_keys(Keys.RETURN)

    # Wait for the login process to complete
    time.sleep(3)

    return driver

def fetch_jobs(driver, location, keywords):
    # Navigate to the jobs page
    driver.get('https://www.linkedin.com/jobs')

    # Wait for the page to load
    time.sleep(3)

    # Enter the location and keywords
    keywords_input = driver.find_element(By.XPATH, '//input[@aria-label="Search by title, skill, or company"]')
    keywords_input.send_keys(keywords)
    
    location_input = driver.find_element(By.XPATH, '//input[@aria-label="City, state, or zip code"]')
    location_input.send_keys(location)

    

    keywords_input.send_keys(Keys.RETURN)

    # Wait for the search results to load
    time.sleep(3)

    # Get the job entries
    job_entries = driver.find_elements(By.CLASS_NAME, 'scaffold-layout__list-container')
    for x in job_entries:
        job_entries_list = driver.find_elements(By.TAG_NAME, 'li')
    job_titles = driver.find_elements(By.CLASS_NAME, 'artdeco-entity-lockup__title')
    company_names = driver.find_elements(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle')
    job_locations = driver.find_elements(By.CLASS_NAME, 'artdeco-entity-lockup__caption')
    i = 0
    for job_entry in job_entries_list:
        print(i+1)
        try:
            print(f"Job Title: {job_titles[i].text}\nCompany: {company_names[i].text}\nLocation: {job_locations[i].text}\n")
        except:
            print("There are no more entries on this page... program terminated")
            break
        i += 1
        print()

def main():
    print("Login details\n")
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    print("\nSearch details\n")
    location = input("Enter location: ")
    keywords = input("Enter job: ")

    driver = login_to_linkedin(email, password)
    fetch_jobs(driver, location, keywords)

    # Close the browser
    driver.quit()

if __name__ == "__main__":
    main()
