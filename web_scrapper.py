"""_summary_
"""
import logging
import pathlib
import sqlite3
import time

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver


class NoMoreProductsError(Exception):
    """_summary_
    """

@dataclass(slots=True)
class Product:
    """_summary_
    """

    url: str
    brand: str
    name: str
    price: str
    query_date: datetime

class WebScrapper(ABC):
    """_summary_
    """

    base_url: str
    site_name: str

    @abstractmethod
    def scrap_site(self) -> list[Product]:
        """_summary_

        Returns:
            list[Product]: _description_
        """

    @abstractmethod
    def scrap_page(self, page: int, browser: WebDriver) -> list[Product]:
        """_summary_

        Args:
            page (int): _description_
            browser (WebDriver): _description_

        Raises:
            NoMoreProductsError: _description_
            NoMoreProductsError: _description_

        Returns:
            list[Product]: _description_
        """

class ExitoScrapper(WebScrapper):
    """_summary_
    """

    def __init__(self) -> None:
        self.url = 'https://www.exito.com/mercado/?page={page_number}'
        self.site_name = 'Exito'

    def scrap_site(self) -> list[Product]:
        scrapped_products: list[Product] = list()
        page = 0
        with webdriver.Chrome() as browser:
            while True:
                try:
                    page += 1
                    scrapped_products.extend(self.scrap_page(page, browser))
                except NoMoreProductsError:
                    break
        return scrapped_products

    def scrap_page(self, page: int, browser: WebDriver) -> list[Product]:
        scrapped_products: list[Product] = list()
        browser.get(self.url.format(page_number=page))
        time.sleep(8)
        try:
            close_modal = WebDriverWait(browser, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'exito-geolocation-3-x-cursorPointer')))
            if close_modal:
                close_modal.click()
        except:
            raise NoMoreProductsError()
        for scroll_counter in range(8):
            time.sleep(2)
            browser.execute_script(
                f"window.scrollTo(0, {1080*(scroll_counter+1)});")
        logging.info(f'Se carga la pagina con titulo "{browser.title}"')
        identified_products = browser.find_elements(
            By.CLASS_NAME, 'vtex-product-summary-2-x-container')
        logging.info(f'Se encuentran {len(identified_products)} productos')

        if not len(identified_products):
            raise NoMoreProductsError()

        for item in identified_products:

            product_identified_brand = item.find_element(
                By.CLASS_NAME, 'vtex-product-summary-2-x-productBrandName').text
            product_identified_name = item.find_element(
                By.CLASS_NAME, 'vtex-store-components-3-x-productBrand').text
            price_div = item.find_element(
                By.CLASS_NAME, 'exito-vtex-components-4-x-selling-price'
            )
            product_identified_price = price_div.find_element(
                By.CLASS_NAME, 'exito-vtex-components-4-x-currencyContainer').text
            product_identified_url = item.find_element(
                By.TAG_NAME, 'a').get_attribute('href')
            scrapped_products.append(Product(product_identified_url, product_identified_brand,
                                             product_identified_name, product_identified_price, datetime.now()))
        return scrapped_products

@dataclass
class IProductDAO(ABC):
    """_summary_
    """

    PRODUCTS_TABLE_NAME: str = 'products'

    def __init__(self):
        if not self.check_database():
            self.initialize_database()
    
    @abstractmethod
    def check_database(self) -> bool:
        """_summary_

        Returns:
            bool: _description_
        """
    
    @abstractmethod
    def initialize_database(self):
        """_summary_
        """

    @abstractmethod
    def write_products(self, products: list[Product]):
        """_summary_
        """

@dataclass
class SQLiteProductDAO(IProductDAO):
    """_summary_
    """

    DB_FILE_NAME: str = 'web_scrapper.db'

    def check_database(self) -> bool:
        # Check if SQLite DB file exists
        if not pathlib.Path(f'./{self.DB_FILE_NAME}').is_file():
            logging.info(f'./{self.DB_FILE_NAME} no existe')
            return False
        # Check if table PRODUCTS_TABLE_NAME exists
        with sqlite3.connect(self.DB_FILE_NAME) as connection:
            res = connection.cursor().execute(
                f'SELECT name FROM sqlite_master WHERE type="table" AND name="{self.PRODUCTS_TABLE_NAME}"')
            if not len(res.fetchall()):
                logging.info(f'tabla {self.PRODUCTS_TABLE_NAME} no existe')
                return False
        return True

    def initialize_database(self):
        with sqlite3.connect(self.DB_FILE_NAME) as connection:
            connection.cursor().execute(
                f'CREATE TABLE {self.PRODUCTS_TABLE_NAME} (url TEXT, brand TEXT, name TEXT, price TEXT, query_date TEXT)')

    def write_products(self, products: list[Product]):
        """_summary_

        Args:
            products (list[Product]): _description_

        Returns:
            bool: _description_
        """

        with sqlite3.connect(self.DB_FILE_NAME) as connection:
            connection.cursor().executemany(f'INSERT INTO {self.PRODUCTS_TABLE_NAME} (url, brand, name, price, query_date) VALUES (?,?,?,?,?)',
                                            tuple(map(lambda pr: (pr.url, pr.brand, pr.name, pr.price, pr.query_date), products)))

@dataclass
class PostgreSQLProductDAO(IProductDAO):
    """_summary_
    """

    def write_products(self, products: list[Product]):
        """_summary_

        Args:
            products (list[Product]): _description_

        Returns:
            bool: _description_
        """

def main():
    """_summary_
    """

    logging.basicConfig(level=logging.INFO)

    scrapper: WebScrapper = ExitoScrapper()
    products: list[Product] = scrapper.scrap_site()

    products_dao: IProductDAO = SQLiteProductDAO()

    products_dao.write_products(products)

    logging.info(
        f'Identified {len(products)} products in site "{scrapper.site_name}"')

if __name__ == '__main__':
    main()
