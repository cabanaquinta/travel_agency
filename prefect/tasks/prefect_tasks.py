import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Optional

import pandas as pd
import scrapy
from prefect_gcp import GcpCredentials
from prefect_gcp.cloud_storage import GcsBucket
from scrapy.crawler import CrawlerProcess
from selenium import webdriver
from selenium.webdriver.common.by import By
from unidecode import unidecode

from prefect import task

PARQUET_PATH = Path('./travel_data.parquet')
DESTINATIONS = {}
CZECH_TO_ENGLISH = {
    'leden': 'January',
    'únor': 'February',
    'březen': 'March',
    'duben': 'April',
    'květen': 'May',
    'červen': 'June',
    'červenec': 'July',
    'srpen': 'August',
    'září': 'September',
    'říjen': 'October',
    'listopad': 'November',
    'prosinec': 'December'
}


# Crawler
def _first_or_second_index(prices: list) -> str:
    """ if the price is in euro and czk, we always want the czk """
    if len(prices) == 1:
        return prices[0]
    elif len(prices) == 2:
        return prices[1]
    else:
        return prices[0]


def clean_description(description: str) -> str:
    description = (
        unidecode(description)
        .strip()
    )
    return description


def extract_price(description: str = '1=2') -> Optional[int]:
    """ Get the price from the dirty string description """
    prices_list = description.split('=')[1]
    prices = prices_list.split('/')
    price = _first_or_second_index(prices).replace(' ', '')
    price = re.sub('[A-Za-z]|\(|\)', '', price).strip()  # noqa: W605
    final_price = price.split('.')[0] if '.' in price else price
    final_price = None if final_price == '' else float(final_price)  # type: ignore
    return price  # type: ignore


def extract_locations(description: str, start_end: str) -> str:
    destinations = description.split('=')[0]
    destination = ''
    if start_end == 'start':
        destination = destinations.split('-')[0].strip().replace('*', '')
    else:
        destination = destinations.split('-')[1].strip()
    return destination


def extract_dates(link: str, start_end: str) -> Optional[datetime]:
    """ To Extract the dates from the links that have them """
    date_regex = r'(\d{4}-\d{2}-\d{2})'
    date_format = '%Y-%m-%d'
    dates = re.findall(date_regex, link)
    if any(dates):
        if start_end == 'start':
            return datetime.strptime(dates[0], date_format)
        else:
            return datetime.strptime(dates[1], date_format)
    else:
        return None


class Travelspider(scrapy.Spider):
    name = 'travel_agency'

    def start_requests(self):
        URL = 'http://www.akcniletenky.com/'
        yield scrapy.Request(url=URL, callback=self.parse)

    def parse(self, response):
        LINKS = []
        TEXTS = []
        # noflake8
        PATH = "//table/tr[3]/td[2]/div/table[3]//td/table/tr[2]/td[2]//table//td/font//p[contains(., '=')]"  # noqa: E501
        ROWS = response.xpath(PATH)
        for row in ROWS:
            text = (
                row.xpath('string()').get()
                .replace('\r', '')
                .replace('\t', '')
                .strip()
            )
            text = text.split('\n')
            text = [clean_description(des) for des in text]

            link = row.xpath('.//@href').getall()
            if len(text) == len(link):
                LINKS.extend(link)
                TEXTS.extend(text)

        DESTINATIONS['-'] = list(zip(LINKS, TEXTS))


def crawl(spider) -> None:
    """ Start the Spider crawling"""
    crawler = CrawlerProcess()
    crawler.start()
    crawler.crawl(spider)
    crawler.start(stop_after_crawl=True, install_signal_handlers=False)


# Web to Bucket
@task(retries=3)
def fetch() -> dict:
    """ Fetch the data from the URL """
    crawl(Travelspider)
    return DESTINATIONS


@task()
def clean_data(destinations: dict) -> pd.DataFrame:
    """ Clean the data and return the DF """
    df = pd.DataFrame(DESTINATIONS.get('-'), columns=['link', 'description'])
    df['price'] = df['description'].apply(extract_price)
    df['currency'] = 'CZK'
    df['start'] = df['description'].apply(
        lambda row: extract_locations(row, 'start'))
    df['end'] = df['description'].apply(
        lambda row: extract_locations(row, 'end'))
    df['date_from'] = df['link'].apply(lambda row: extract_dates(row, 'start'))
    df['date_to'] = df['link'].apply(lambda row: extract_dates(row, 'end'))
    df['collected_date'] = datetime.utcnow() + timedelta(hours=2)
    return df


@task()
def save_parquet_file(df: pd.DataFrame, path: Path) -> None:
    """ Save pd.DataFrame to parquet"""
    df.to_parquet(path, compression='gzip')
    return


@task()
def upload_to_gcs(path: Path) -> None:
    """ Just upload the files to the GCS Bucket """
    bucket = GcsBucket.load('bucket')
    bucket.upload_from_path(path)
    return


# Bucket to BigQuery
@task(retries=3)
def upload_to_bq(path: Path, method: Literal['fail', 'replace', 'append'] = 'append') -> None:
    """ Read files from Bucket and paste them to BigQuery """
    bucket = GcsBucket.load('bucket')
    download_file_path = bucket.download_object_to_path(path, path)
    df = pd.read_parquet(download_file_path)
    df['price'] = pd.to_numeric(df['price'], downcast='float')
    gcp_credentials = GcpCredentials.load('my-gcp')
    df.to_gbq(
        destination_table='warehouse.master',
        project_id='amazing-thought-394210',
        credentials=gcp_credentials.get_credentials_from_service_account(),
        chunksize=10000,
        if_exists=method
    )
    return


def selenium_scraping(url: str) -> dict:
    PARSE_DATES = {}
    DRIVER = webdriver.Chrome(
        executable_path='/Users/alejandro.perez/Downloads/chromedriver-mac-x64/chromedriver')  # type: ignore
    DRIVER.get(url)
    try:
        # Check if the cookie acceptance element is present
        cookie_accept_button = DRIVER.find_element(
            By.XPATH, "//*[@id='ngAppContainer']/div[4]/div/div[3]/button[3]"
        )
        # Click the cookie acceptance button
        cookie_accept_button.click()

    except Exception as e:
        print('No cookie acceptance element found:', e)
    try:
        # Find the element containing the title
        title_element = DRIVER.find_elements(By.XPATH, "//*[contains(@class,'month-label')]//span")
        # Extract the text from the element
        months_years = [(title_element[i].text, title_element[i+1].text) for i in range(0, len(title_element), 2)]
        number_of_dates = len(months_years)
        dates_english = [(CZECH_TO_ENGLISH[combination[0].lower()], combination[1]) for combination in months_years]
        dates_parsed = [(datetime.strptime(f'01 {combination[0]} {combination[1]}', '%d %B %Y')) for combination in dates_english]
        PARSE_DATES = {
            'number_of_dates': number_of_dates,
            'options': dates_parsed
        }

    except Exception as e:
        print('Error:', e)
    DRIVER.quit()
    return PARSE_DATES


@task(retries=3)
def read_bigquery_table() -> pd.DataFrame:
    gcp_credentials = GcpCredentials.load('my-gcp')
    # with BigQueryWarehouse(gcp_credentials=gcp_credentials) as warehouse:
    QUERY = (
        """
        SELECT
            link
        FROM `amazing-thought-394210.warehouse.master`
        WHERE
            collected_date >= '2023-09-10'
            AND link LIKE '%pelikan%'
        ORDER BY collected_date DESC
        """
    )
    df = pd.read_gbq(
        query=QUERY,
        project_id='amazing-thought-394210',
        credentials=gcp_credentials.get_credentials_from_service_account()
    )
    df.drop_duplicates(inplace=True)
    return df


@task(retries=3)
def enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    df['enriched_data_pelikan'] = df['link'].apply(selenium_scraping)
    return df
