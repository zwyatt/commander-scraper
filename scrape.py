# DECKS
# Commander 2015 and older?
# STORES
# hardcoded last page for gamebridge
# ALL-IN-ONE LISTINGS
# L.A. mood (no)
# derpycards (no)
# red dragon (no)
# ONLINE SHOPPING AVAILABLE SOON (TM)
# arkain hobbies and games
# HTML
# two columns
# filter/search/sort
# navigation arrows (up to top down to bottom)
# price history (lol)
# search singles? (lol)
# GITHUB
# branch deployment?

import csv
import json
import time
from operator import attrgetter

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from jinja2 import Environment, FileSystemLoader, select_autoescape

testing = []


class Deck:
    def __init__(self, name, alts, _set, set_alts, collector):
        self.name = name
        self.alts = alts
        self.set = _set
        self.set_alts = set_alts
        self.collector = collector
        self.store_decks = []
        self.stock = False

    def __str__(self):
        return f"{self.set} - {self.name}"


#
#
# Price and stock data for a deck from a specific store.
class Store_Deck:
    def __init__(self, store, link, price, stock):
        self.store = store
        self.link = link
        self.price = float(price)
        self.stock = stock

    def __lt__(self, other):
        return self.price < other.price


#
# Read data.json.
# Contains store and deck data.
def read_data():
    with open('data.json', 'r') as file:
        data = json.load(file)
    file.close()
    return data


#
#
# Create Deck objects out of the JSON deck data.
def make_decks(data):
    global testing
    decks = []
    for deck in data['decks']:
        alts = []
        set_alts = []
        if 'alts' in deck:
            for alt in deck['alts']:
                alts.append(str(alt))
        if 'set_alts' in deck:
            for set_alt in deck['set_alts']:
                set_alts.append(str(set_alt))

        collector = 'collector' in deck

        new_deck = Deck(deck['name'], alts, deck['set'], set_alts, collector)
        decks.append(new_deck)

    return decks


#
#
# Generate XPath for Selenium.
def format_xpath(tag, attr, _id):
    return f"//{tag}[contains(@{attr}, '{_id}')]"


#
#
# Retrieve and save HTML from the store product pages.
def fetch(store):
    # Click to go to next page.
    def click(i):
        # Zap a popup blocking the clickable.
        def zap():
            zap_xpath = format_xpath(store['html_zap_tag'], store['html_zap_attr'], store['html_zap'])
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, zap_xpath))
            )
            zaps = driver.find_elements(By.XPATH, zap_xpath)

            for zap in zaps:
                driver.execute_script("arguments[0].style.visibility='hidden'", zap)

        # First page?
        if i == 1:
            driver.get(store['page'])
        else:
            clickable_xpath = format_xpath(store['html_next_tag'], store['html_next_attr'], store['html_next'])
            clickable = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, clickable_xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView();", clickable)

            # Zap blockers.
            if 'html_zap' in store:
                zap()

            # Give time for the popups to disappear.
            time.sleep(1)
            clickable.click()

    # Keep scrolling until there are no new items.
    def scroll():
        driver.get(store['page'])
        elems = []
        xpath = format_xpath(store['html_items_tag'], store['html_items_attr'], store['html_items'])
        elem = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
        body = driver.find_element(By.TAG_NAME, "body")
        new_elems = driver.find_elements(By.XPATH, xpath)

        while len(elems) < len(new_elems):
            elems = new_elems
            for i in range(20):
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.5)
            new_elems = driver.find_elements(By.XPATH, xpath)

        return trim(driver.page_source, elem)

    # Trim everything before the first item.
    def trim(html, elem):
        trimmed = ""
        if store['html_items'] in html and elem:
            elem_html = elem.get_attribute('outerHTML')
            i = html.find(elem_html)
            trimmed = html[i:]

        return trimmed

    html = ""
    elem = ""
    driver = webdriver.Firefox()

    try:
        i = 1
        # No pages, just a loading scroll
        # clunky
        if 'scroll' in store:
            html = scroll()
        while elem is not None and 'scroll' not in store:
            # Do we have to click for next page?
            if 'html_next' in store:
                click(i)
            else:
                # Some pages/searches/etc have "page=" in the middle of the url
                if "page=" in store['page']:
                    next_page = store['page'].replace("page=", f"page={str(i)}")
                elif "pg=" in store['page']:
                    next_page = store['page'].replace("pg=", f"pg={str(i)}")
                driver.get(next_page)

            # Wait for up to 5 seconds until the element is present
            elem = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((
                    By.XPATH, format_xpath(store['html_items_tag'], store['html_items_attr'], store['html_items']))))
            print(elem)
            # Wait 5 seconds to be courteous.
            time.sleep(5)

            # Trim everything before the first item.
            html += trim(driver.page_source, elem)
            i += 1
            # Hardcoded last page for difficult sites.
            if 'last_page' in store:
                if i > int(store['last_page']):
                    break
    except TimeoutException:
        print("No more pages or no items found.")
    finally:
        driver.quit()

    with open(f"fetched\\{store['file']}", 'w', encoding='utf-8') as f:
        f.write(html)


def fetch_one(store):
    driver = webdriver.Firefox()
    print(store['file'])
    try:
        driver.get(f"{store['page']}1")
        elem = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, store['html_items']))
        )
        time.sleep(10)
        print(elem)

        with open(f"fetched\\{store['file']}", 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
    except TimeoutException:
        print("Element not found in fetch_one")
    finally:
        driver.quit()


# Read a store's fetched HTML.
def read_html(store):
    with open(f"fetched\\{store['file']}", 'r', encoding='utf-8') as f:
        return f.read()


not_found = []


#
#
# Extract product info from BeautifulSoup.
def extract(soup, store, decks):
    global not_found
    global testing

    # Generalized soup extraction.
    def soup_find(item, attr, _id, tag, value):
        soup_dict = {attr: _id}
        found = item.find(tag, soup_dict)
        return soup_value(found, value)

    # get('text') doesn't work so we improvise.
    def soup_value(elem, value):
        if elem:
            if elem.has_attr(value):
                return elem.get(value).strip()
            else:
                return elem.text.strip()
        # Elem not found, likely a sale price from JJs or a negative stock flag.
        else:
            return elem

    # Is the item a deck in our database?
    def in_decks(item, deck):
        global testing
        l_item = item.lower()
        l_deck_name = deck.name.lower()
        l_deck_set = deck.set.lower()
        set_found = False

        # Fail early
        if (
            deck.collector and "collector" not in l_item
            or not deck.collector and "collector" in l_item
            or "japanese" in l_item
            or "(fr)" in l_item
            or "french" in l_item
            or "prerelease" in l_item
        ):
            return False

        # Match set
        # set_alts to match mispellings and typos on website listings
        if deck.set_alts:
            for set_alt in deck.set_alts:
                if set_alt.lower() in l_item:
                    set_found = True
                    break

        if not set_found and l_deck_set not in l_item:
            return False

        # Match name
        # Alternate deck names to match different website listings
        if deck.alts:
            for alt in deck.alts:
                if alt.lower() in l_item:
                    return True

        return l_deck_name in l_item

    # Extract item
    # Returns a list of one item (name, link, price, stock)
    def extract_item(item):
        # Extract name.
        # Soup can't get text from anchor tags... weird. Use parent tag.
        name = soup_find(
            item,
            store['html_name_attr'],
            store['html_name'],
            store['html_name_tag'],
            store['html_name_value']
        )
        print(name)

        # Extract link.
        link = soup_find(
            item,
            store['html_link_attr'],
            store['html_link'],
            store['html_link_tag'],
            store['html_link_value']
        )

        # Extract price.
        text_price = soup_find(
            item,
            store['html_price_attr'],
            store['html_price'],
            store['html_price_tag'],
            store['html_price_value']
        )

        # Sale price? (JJs)
        if not text_price:
            text_price = soup_find(
                item,
                store['html_price_attr'],
                store['html_sale_price'],
                store['html_price_tag'],
                store['html_price_value']
            )

        # Extract stock.
        stock = soup_find(
            item,
            store['html_stock_attr'],
            store['html_stock'],
            store['html_stock_tag'],
            store['html_stock_value']
        )

        return [(name, link, text_price, stock)]

    # Extract all the sub-items for stores with combined listings
    # Returns a list of (name, link, price, stock)
    def extract_subitems(item):
        global testing
        _set = soup_find(
            item,
            store['html_set_attr'],
            store['html_set'],
            store['html_set_tag'],
            store['html_set_value']
        )
        print(_set)

        link = soup_find(
            item,
            store['html_link_attr'],
            store['html_link'],
            store['html_link_tag'],
            store['html_link_value']
        )
        print(link)

        # Parent element of the subitems
        parent_dict = {store['html_subitems_attr']: store['html_subitems']}
        parent = item.find(store['html_subitems_tag'], parent_dict)

        # The actual subitems
        subitems_dict = {store['html_subitem_attr']: store['html_subitem']}
        subitems = parent.find_all(store['html_subitem_tag'], subitems_dict)

        subitems_r = []

        for subitem in subitems:
            name = soup_value(subitem, store['html_name_value'])
            print(name)
            price = soup_value(subitem, store['html_price_value'])
            print(price)
            stock = soup_value(subitem, store['html_stock_value'])
            print(stock)
            subitems_r.append((f"{_set} - {name}", link, price, stock))

        return subitems_r

    # Extract all the items.
    items_dict = {store['html_items_attr']: store['html_items']}
    items = soup.find_all(store['html_items_tag'], items_dict)
    # Skip x items at the beginning if required based on the store.
    if 'skip' in store:
        items = items[int(store['skip']):]

    print(f"{len(items)} items found")

    for item in items:
        found = False
        if 'html_subitems' in store:
            subitems = extract_subitems(item)
        else:
            subitems = extract_item(item)

        # This is ugly, pretend it's not happening
        for subitem in subitems:
            name = subitem[0]
            link = subitem[1]
            text_price = subitem[2]
            stock = subitem[3]

            # Prefix with the store link if it's a local path.
            if "https" not in link:
                link = store['link'] + link
            print(link)

            # Clean up the price to remove CAD, dollar signs, etc.
            price = ""
            for char in text_price:
                if char.isnumeric() or char == ".":
                    price += char
            print(price)

            # Gamebridge has some items that are priced at $0. Also Chimera sometimes when out of stock
            if float(price) == 0:
                continue

            print(stock)
            # Imaginaire either has an Add to Cart button or it doesn't (or an Out of Stock span or it doesn't)
            if 'html_stock_flag' in store:
                stock = (
                    store['html_stock_flag'] == "in" and stock
                    or store['html_stock_flag'] == "out" and not stock)
            elif 'html_stock_numerical' in store:
                stock = int(stock) > 0
            else:
                stock = (
                    "in" in stock.lower()
                    or "add" in stock.lower()
                    or "true" in stock.lower()
                    or "new" in stock.lower())

            # Which deck is it?
            found = False
            for i in range(len(decks)):
                if in_decks(name, decks[i]):
                    decks[i].store_decks.append(Store_Deck(store, link, price, stock))
                    found = True
                    break

            if not found:
                print(f"{name} not found")
                not_found.append(name)

    return decks


# No longer used.
def write_csv(decks):
    with open('decks.csv', 'w') as csvfile:
        fieldnames = ['deck', 'store', 'price', 'stock']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        for deck in (deck for deck in decks if deck.store_decks):
            # sort store_decks by price and stock (price only atm)
            deck.store_decks.sort(key=attrgetter('price', 'stock'))
            writer.writeheader()
            for store_deck in deck.store_decks:
                writer.writerow({
                    'deck': f"{deck.set} - {deck.name}",
                    'store': store_deck.store['name'],
                    'price': store_deck.price,
                    'stock': store_deck.stock
                })
            writer.writerow({})

    print("csv file written")


#
#
# Write the extracted data to an HTML table.
def write_html(decks):
    env = Environment(
        loader=FileSystemLoader(''),
        autoescape=select_autoescape()
    )

    template = env.get_template('template.html.jinja')
    # Sort the decks by stock -> price.
    # Should I even include stock in the sort? ugh.
    for deck in decks:
        deck.store_decks.sort()
        # in_stock = []
        # out_stock = []
        # for store_deck in deck.store_decks:
        #     if store_deck.stock:
        #         in_stock.append(store_deck)
        #     else:
        #         out_stock.append(store_deck)
        # deck.store_decks = in_stock
        # deck.stock = len(in_stock) > 0

    with open('index.html', 'w') as f:
        f.write(template.render(decks=decks))


data = read_data()
decks = make_decks(data)
# for store in data['stores']:
#     fetch(store)
# fetch(data['stores'][18])
# fetch_one(data['stores'][4])
for store in data['stores']:
    html = read_html(store)
    soup = BeautifulSoup(html, 'html.parser')
    decks = extract(soup, store, decks)

print("not found:")
with open('not_found.txt', 'w') as f:
    for x in not_found:
        print(x)
        if (
            "booster" not in x.lower()
            and "japanese" not in x.lower()
            and "(fr)" not in x.lower()
            and "french" not in x.lower()
            and "starter" not in x.lower()
            and "playmat" not in x.lower()
            and "display" not in x.lower()
            and "bundle" not in x.lower()
            and "collection" not in x.lower()
            and "ultra pro" not in x.lower()
            and "brawl" not in x.lower()
            and "planechase" not in x.lower()
            and "archenemy" not in x.lower()
            and "pioneer" not in x.lower()
            and "prerelease" not in x.lower()
            and "secret lair" not in x.lower()
            and "challenger" not in x.lower()
            and "scene box" not in x.lower()
            and "beginner" not in x.lower()
            and "from the vault" not in x.lower()
            and "planeswalker deck" not in x.lower()
            and "deck box" not in x.lower()
            and "played" not in x.lower()
            and "mint" not in x.lower()
            and "default title" not in x.lower()
            and "guild" not in x.lower()
        ):
            f.write(f"{x}\n")

for x in testing:
    print(x)

write_html(decks)
# write_csv(decks)
