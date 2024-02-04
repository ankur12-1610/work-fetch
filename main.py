import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
import pandas as pd
import random
import time
from pyvirtualdisplay import Display
display = Display(visible=0, size=(800, 800))
display.start()

def scrape_linkedin_jobs(job_title: str, location: str, pages: int = None) -> list:
    # Sets the pages to scrape if not provided
    pages = 3

    chromedriver_autoinstaller.install()  # Check if the current version of chromedriver exists
                                        # and if it doesn't exist, download it automatically,
                                        # then add chromedriver to path

    chrome_options = webdriver.ChromeOptions()
    # Add your options as needed
    options = [
    # Define window size here
    "--window-size=1200,1200",
        "--ignore-certificate-errors"

        #"--headless",
        #"--disable-gpu",
        #"--window-size=1920,1200",
        #"--ignore-certificate-errors",
        #"--disable-extensions",
        #"--no-sandbox",
        #"--disable-dev-shm-usage",
        #'--remote-debugging-port=9222'
    ]

    for option in options:
        chrome_options.add_argument(option)

    driver = webdriver.Chrome(options = chrome_options)

    # Navigate to the LinkedIn job search page with the given job title and location
    driver.get(
        f"https://www.linkedin.com/jobs/search/?f_E=1&origin=JOB_SEARCH_PAGE_JOB_FILTER&geoId=102713980&keywords={job_title}&location={location}&refresh=true&sortBy=DD"
    )

    # Scroll through the first 50 pages of search results on LinkedIn
    for i in range(pages):

        # Log the current page number
        logging.info(f"Scrolling to bottom of page {i+1}...")

        # Scroll to the bottom of the page using JavaScript
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        try:
            # Wait for the "Show more" button to be present on the page
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div[1]/div/main/section[2]/button")
                )
            )
            # Click on the "Show more" button
            element.click()

        # Handle any exception that may occur when locating or clicking on the button
        except Exception:
            # Log a message indicating that the button was not found and we're retrying
            logging.info("Show more button not found, retrying...")

        # Wait for a random amount of time before scrolling to the next page
        time.sleep(random.choice(list(range(3, 7))))

    # Scrape the job postings
    jobs = []
    soup = BeautifulSoup(driver.page_source, "html.parser")
    job_listings = soup.find_all(
        "div",
        class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
    )

    try:
        for job in job_listings:
            # Extract job details

            # job title
            job_title = job.find("h3", class_="base-search-card__title").text.strip()
            # job company
            job_company = job.find(
                "h4", class_="base-search-card__subtitle"
            ).text.strip()
            # job location
            job_location = job.find(
                "span", class_="job-search-card__location"
            ).text.strip()
            # job link
            apply_link = job.find("a", class_="base-card__full-link")["href"]
            #date posted
            date_posted = job.find("time")["datetime"]

            # Navigate to the job posting page and scrape the description
            driver.get(apply_link)

            # Sleeping randomly
            time.sleep(random.choice(list(range(5, 11))))

            # Add job details to the jobs list
            if job_title.find('intern') !=-1 or job_title.find('Intern') !=-1 or job_title.find('Apprentice')!=-1 or job_title.find('Trainee')!=-1:
                jobs.append(
                    {
                        "Company": job_company,
                        "Title": job_title,
                        "Location": job_location,
                        "Link": f"[Apply]({apply_link})",
                        "Date Posted": date_posted
                    }
                )

            # Logging scrapped job with company and location information
            logging.info(f'Scraped "{job_title}" at {job_company} in {job_location}...')

    # Catching any exception that occurs in the scrapping process
    except Exception as e:
        # Log an error message with the exception details
        logging.error(f"An error occurred while scraping jobs: {str(e)}")

        # Return the jobs list that has been collected so far
        # This ensures that even if the scraping process is interrupted due to an error, we still have some data
        return jobs

    # Close the Selenium web driver
    driver.quit()

    # Return the jobs list
    return jobs


def save_job_data(data: dict) -> None:
    """
    Save job data to a CSV file.

    Args:
        data: A dictionary containing job data.

    Returns:
        None
    """
    # sort jobs by latest date posted
    data = sorted(data, key=lambda x: x["Date Posted"], reverse=True)

    # Create a pandas DataFrame from the job data dictionary
    df = pd.DataFrame(data)

    #create a csv file
    # df.to_csv('jobs.csv', index=False)

    # update content in README.md between <!--START_SECTION:workfetch--> and <!--END_SECTION:workfetch-->
    readme = open('README.md', 'r')
    readme_content = readme.read()
    readme.close()

    start = readme_content.find('<!--START_SECTION:workfetch-->')
    end = readme_content.find('<!--END_SECTION:workfetch-->')

    new_readme_content = f"{readme_content[:start]}<!--START_SECTION:workfetch-->\n{df.to_markdown(index=False)}\n{readme_content[end:]}"

    readme = open('README.md', 'w')
    readme.write(new_readme_content)
    readme.close()

    # Log a message indicating how many jobs were successfully scraped and saved to the CSV file
    logging.info(f"Successfully scraped {len(data)} jobs and saved to README.md")

job_title = "Software Engineer"
location = "India"

jobs = scrape_linkedin_jobs(job_title, location)
save_job_data(jobs)
