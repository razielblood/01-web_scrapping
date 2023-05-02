"""Module that have all the necesary classes and methods to web scrap some popular colombian grocery stores
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

from web_scrapper import Product


class NoMoreProductsError(Exception):
    """Exception that rises where no more products are identified in a given page
    """

@dataclass(slots=True)
class Store:
    """Dataclass that defines a store that can be scrapped
    """

    store_id: int
    name: str
    base_url: str

@dataclass(slots=True)
class Product:
    """Dataclass that represents a product identified when a store is being scrapped
    """

    url: str
    brand: str
    name: str
    price: str
    query_date: datetime
    seller: Store

class WebScrapper(ABC):
    """Abstract class that defines what a valid web scrapper for a colombian grocery store should implement
    """

    store: Store

    @abstractmethod
    def scrap_site(self) -> list[Product]:
        """Base method that should be invoked to scrap a site

        Returns:
            list[Product]: List of identified products in the site 
        """

    @abstractmethod
    def scrap_page(self, page: int, browser: WebDriver) -> list[Product]:
        """Method that scrap a single page of a site based on a page number

        Args:
            page (int): Number of the page to scrap
            browser (WebDriver): Browser to use to scrap the page

        Raises:
            NoMoreProductsError: Raised when no product was identified in the given page

        Returns:
            list[Product]: List of identified products in the current page
        """

class ExitoScrapper(WebScrapper):
    """Definition of the web scrapper for the exito store
    """

    def __init__(self) -> None:
        self.store = Store(1, 'Exito','https://www.exito.com/mercado/?page={page_number}')

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
        browser.get(self.store.base_url.format(page_number=page))
        time.sleep(8)
        try:
            close_modal = WebDriverWait(browser, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'exito-geolocation-3-x-cursorPointer')))
            if close_modal:
                close_modal.click()
        except Exception as ex:
            raise NoMoreProductsError(ex)
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
                                             product_identified_name, product_identified_price, datetime.now(), self.store))
        return scrapped_products

@dataclass
class ProductDAO(ABC):
    """Class that defines what a valid DAO should implement to store the information of a scrapped product
    """

    PRODUCTS_TABLE_NAME: str = 'products'

    def __init__(self) -> None:
        if not self.check_database():
            self.initialize_database()
    
    @abstractmethod
    def check_database(self) -> bool:
        """Check if the database is initialized correctly. That is, the database and the needed tables exists

        Returns:
            bool: Boolean representing if the database is valid
        """
    
    @abstractmethod
    def initialize_database(self) -> None:
        """Method that creates the necesary tables for the scrapper to store the results
        """

    @abstractmethod
    def write_products(self, products: list[Product]) -> None:
        """Method that flushes the identified products to the database

        Args:
            products (list[Product]): List of Product objects to be stores
        """

@dataclass
class SQLiteProductDAO(ProductDAO):
    """Class that implements the required methods to store the scrapping result into a SQLite DB
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

    def initialize_database(self) -> None:
        with sqlite3.connect(self.DB_FILE_NAME) as connection:
            connection.cursor().execute(
                f'CREATE TABLE {self.PRODUCTS_TABLE_NAME} (seller_id INT, url TEXT, brand TEXT, name TEXT, price TEXT, query_date TEXT)')

    def write_products(self, products: list[Product]) -> None:
        with sqlite3.connect(self.DB_FILE_NAME) as connection:
            connection.cursor().executemany(f'INSERT INTO {self.PRODUCTS_TABLE_NAME} (seller_id, url, brand, name, price, query_date) VALUES (?,?,?,?,?,?)',
                                            tuple(map(lambda pr: (pr.seller.store_id, pr.url, pr.brand, pr.name, pr.price, pr.query_date), products)))

@dataclass
class PostgreSQLProductDAO(ProductDAO):
    """Class that implements the required methods to store the scrapping result into a PostgreSQL Database
    """

    def check_database(self) -> bool:
        return super().check_database()

    def initialize_database(self) -> None:
        return super().initialize_database()

    def write_products(self, products: list[Product]) -> None:
        return super().write_products(products)

def main() -> None:
    """Main method that orchestrate an example flow to scrap web pages
    """

    logging.basicConfig(level=logging.INFO)

    scrapper: WebScrapper = ExitoScrapper()
    products: list[Product] = scrapper.scrap_site()

    products_dao: ProductDAO = SQLiteProductDAO()

    products_dao.write_products(products)

    logging.info(
        f'Identified {len(products)} products in site "{scrapper.store.name}"')

if __name__ == '__main__':
    main()
