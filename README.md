# Grocery Shopping Web Scrapper

Web Scrapper for some popular colombian grocery stores.

# Requirements

Depends on:

- Python>=3.7
- Selenium>=4.9

# Usage

To use this web scrapper you need:

1.  Install python requirements

        pip install -r requirements.txt

2.  run the scrapper

        python3 web_scrapper.py

At this point, the scrapper will be running and a Chrome web browser will open. Don't touch it while the program is running, it will close when the scrapping is done.

When the process is finished, it will flush the scrapped results to the configured database (SQLite by default) to a table named "products".

# Entity-Relation Diagram

```mermaid
---
title: Entiry-Relation Diagram
---

erDiagram

    STORE one to many PRODUCT: sells

    PRODUCT{
        int seller FK
        string url
        string brand
        string name
        string price
        string query_date
    }
    
    STORE{
        int store_id PK
        string name
        string base_url
    }
```

# Class Diagram

```mermaid
---
title: Web Scrapper Class Diagram
---

classDiagram

    class WebScrapper {
        +base_url: str
        +site_name: str
        +scrap_site() Product[]
        +scrap_page(page) Product[]
    }

    <<interface>> WebScrapper

    class ExitoScrapper
    class JumboScrapper

    class Product{
        <<entity>>
        +site: str
        +url: str
        +brand: str
        +name: str
        +price: str
        +query_date: datetime
    }
    class IProductDAO{
        <<interface>>
        -PRODUCTS_TABLE_NAME str
        +write_products(products: Product[])
        +check_database() bool
        +initialize_database() bool
    }


    class SQLiteProductDAO {
        -DB_FILE_NAME: str = 'web_scrapper.db'

    }
    class PostgreSQLProductDAO

    class NoMoreProductsError{
        <<Exception>>
        +NoMoreProductsError()
    }

    NoMoreProductsError --> WebScrapper

    WebScrapper <|-- ExitoScrapper
    WebScrapper <|-- JumboScrapper

    WebScrapper --> Product : produces
    IProductDAO --> Product : uses

    IProductDAO <|-- SQLiteProductDAO
    IProductDAO <|-- PostgreSQLProductDAO

```
