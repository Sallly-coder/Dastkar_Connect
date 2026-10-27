# Lab 10: Selenium tests for Dastkar_Connect login.
# Start the app first, then run: python -m pytest tests\test_login_selenium.py -v
from dotenv import load_dotenv
load_dotenv()  # This loads variables from your .env file into os.environ

import os
# ... rest of your test imports and code
from selenium.common.exceptions import TimeoutException
import re
import time
import urllib.request
from urllib.parse import urlparse

import pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()                                   # reads SEED_PASSWORD from .env

BASE = "http://127.0.0.1:5000"
BUYER_PW = "buyer123"
LIAISON_PW = "liaison123"
ARTISAN_PW = "artisan123"
PASSWORD = BUYER_PW        # used by the tests that log in as the buyer
BUYER = "buyer@test.com"
LIAISON = "liaison@test.com"
ARTISAN = "rani@test.com"
ERROR_TEXT = "Invalid email or password"


@pytest.fixture(scope="session", autouse=True)
def server_is_running():
    try:
        urllib.request.urlopen(BASE + "/login", timeout=3)
    except Exception:
        pytest.exit("The app is not running. In another Command Prompt run: "
                    "flask --app app run", returncode=1)


@pytest.fixture(scope="session")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    if os.environ.get("HEADLESS"):              # set HEADLESS=1 to hide the browser window
        options.add_argument("--headless=new")
    d = webdriver.Chrome(options=options)
    yield d
    d.quit()


@pytest.fixture
def browser(driver, request):
    driver.get(BASE + "/login")
    driver.delete_all_cookies()                 # every test starts logged out
    driver.get(BASE + "/login")
    yield driver
    # evidence for the lab report: a screenshot of the final state of every test
    os.makedirs("screenshots", exist_ok=True)
    name = re.sub(r"[^A-Za-z0-9_-]", "_", request.node.name)
    driver.save_screenshot(f"screenshots/{name}.png")


def path(driver):
    return urlparse(driver.current_url).path


def wait(driver, condition):
    return WebDriverWait(driver, 5).until(condition)


def login(driver, email, password):
    driver.get(BASE + "/login")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "form button, form input[type='submit']").click()


def test_tc01_valid_login(browser):
    login(browser, BUYER, PASSWORD)
    wait(browser, lambda d: path(d) == "/buyer")
    cookie = browser.get_cookie("token")
    assert cookie is not None and cookie["httpOnly"]


@pytest.mark.parametrize("email, password, page", [
    (BUYER, BUYER_PW, "/buyer"),
    (LIAISON, LIAISON_PW, "/liaison"),
    (ARTISAN, ARTISAN_PW, "/artisan")],
    ids=["buyer", "liaison", "artisan"])
def test_tc02_each_role_lands_on_its_own_page(browser, email, password, page):
    login(browser, email, password)
    try:
        wait(browser, lambda d: path(d) == page)
    except TimeoutException:
        body = browser.find_element(By.TAG_NAME, "body").text[:300]
        pytest.fail(f"Expected {page} but URL is {browser.current_url}\nPage text: {body!r}")


def test_tc03_wrong_password(browser):
    login(browser, BUYER, "wrong-password-123")
    wait(browser, lambda d: ERROR_TEXT in d.page_source)
    assert path(browser) == "/login"
    assert browser.get_cookie("token") is None


def test_tc04_unregistered_email(browser):
    login(browser, "nobody@example.com", PASSWORD)
    wait(browser, lambda d: ERROR_TEXT in d.page_source)
    assert path(browser) == "/login"
    assert browser.get_cookie("token") is None


def test_tc05_empty_email(browser):
    login(browser, "", PASSWORD)
    time.sleep(1)                               # give the browser or server time to react
    assert path(browser) == "/login"
    assert browser.get_cookie("token") is None


def test_tc06_empty_password(browser):
    login(browser, BUYER, "")
    time.sleep(1)
    assert path(browser) == "/login"
    assert browser.get_cookie("token") is None


def test_tc07_protected_page_needs_login(browser):
    browser.get(BASE + "/buyer")
    assert path(browser) == "/login"


def test_tc08_buyer_cannot_open_liaison_page(browser):
    login(browser, BUYER, PASSWORD)
    wait(browser, lambda d: path(d) == "/buyer")
    browser.get(BASE + "/liaison")
    assert "Forbidden" in browser.page_source


def test_tc09_logout_ends_the_session(browser):
    login(browser, BUYER, PASSWORD)
    wait(browser, lambda d: path(d) == "/buyer")
    buttons = browser.find_elements(By.CSS_SELECTOR, "form[action$='/logout'] button")
    if not buttons:
        pytest.skip("No Log out button on the page (check base.html)")
    buttons[0].click()
    wait(browser, lambda d: path(d) == "/login")
    browser.get(BASE + "/buyer")
    assert path(browser) == "/login"


def test_tc10_tampered_token_is_rejected(browser):
    browser.add_cookie({"name": "token", "value": "garbage", "path": "/"})
    browser.get(BASE + "/buyer")
    assert path(browser) == "/login"
