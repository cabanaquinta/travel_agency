import re
from datetime import datetime
from pathlib import Path
from typing import Union

import pandas as pd
import scrapy
from prefect_gcp import GcpCredentials
from prefect_gcp.cloud_storage import GcsBucket
from scrapy.crawler import CrawlerProcess
from unidecode import unidecode

from prefect import task


PARQUET_PATH = Path('./travel_data.parquet')
DESTINATIONS = {}

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


def extract_price(description: str) -> Union[int, None]:
    """ Get the price from the dirty string description """
    prices = description.split('=')[1]
    prices = prices.split('/')
    price = _first_or_second_index(prices).replace(' ', '')
    price = re.sub('[A-Za-z]|\(|\)', '', price).strip()
    price = price.split('.')[0] if '.' in price else price
    price = None if price == '' else int(price)
    return price


def extract_locations(description: str, start_end: str) -> str:
    destinations = description.split('=')[0]
    destination = ''
    if start_end == 'start':
        destination = destinations.split('-')[0].strip().replace('*', '')
    else:
        destination = destinations.split('-')[1].strip()
    return destination


def extract_dates(link: str, start_end: str) -> Union[str, None]:
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
        ROWS = response.xpath(
            "//table/tr[3]/td[2]/div/table[3]//td/table/tr[2]/td[2]//table//td/font//p[contains(., '=')]"
        )
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
        lambda row:  extract_locations(row, 'start'))
    df['end'] = df['description'].apply(
        lambda row: extract_locations(row, 'end'))
    df['date_from'] = df['link'].apply(lambda row: extract_dates(row, 'start'))
    df['date_to'] = df['link'].apply(lambda row: extract_dates(row, 'end'))
    df['collected_date'] = datetime.now()
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
def upload_to_bq(path: Path, method: str = 'append') -> None:
    """ Read files from Bucket and paste them to BigQuery """
    df = pd.read_parquet(path)
    gcp_credentials = GcpCredentials.load('my-gcp')
    df.to_gbq(
        destination_table='warehouse.master',
        project_id='amazing-thought-394210',
        credentials=gcp_credentials.get_credentials_from_service_account(),
        chunksize=10000,
        if_exists=method
    )
    return
