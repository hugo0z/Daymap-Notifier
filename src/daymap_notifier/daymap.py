import asyncio
import json
import re
from pathlib import Path

import httpx
import requests
import settings
from bs4 import BeautifulSoup
from playwright.async_api import TimeoutError, async_playwright

BASE_DIR = Path(__file__).resolve().parents[2]
AUTH_FILE = BASE_DIR / ".playwright" / ".auth" / "user.json"
AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
DAYMAP_URL = "https://kedron.eq.daymap.net/"


async def login(email: str, password: str, username: str):
    """Automaticly goes through the login process for daymap using playwright in a headless browser then saving session cookies for later use.

    Args:
        email (str): The email address for the user's account.
        password (str): The password for the user's account.
        username (str): The username for the user's account.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(
            DAYMAP_URL,
            wait_until="domcontentloaded",
        )

        await page.fill('input[type="email"]', email)
        await page.click('input[type="submit"]')

        try:
            await page.wait_for_url(
                "https://fed.education.qld.gov.au/**", timeout=15000
            )
        except TimeoutError:
            raise ValueError("Failed to login. Email most likely invalid.")

        await page.fill('input[id="username"]', username)
        await page.fill('input[id="password"]', password)
        await page.click('input[id="sso-cou"]')
        await page.click('input[id="sso-signin"]')

        try:
            await page.wait_for_url(
                "https://login.microsoftonline.com/login.srf", timeout=15000
            )
        except TimeoutError:
            raise ValueError("Failed to login. Email or password most likely invalid.")

        await page.click('input[id="idSIButton9"]')

        await page.wait_for_url(
            f"{DAYMAP_URL}daymap/timetable/timetable.aspx",
            timeout=15000,
        )

        await context.storage_state(path=AUTH_FILE)

        settings.update_config("username", username)

        await browser.close()


async def get_timetable(week_start):
    """Automaticly gets timetable from daymap using stored session cookies and formats it neatly.

    Args:
        week_start (str): The start date of the week for which to retrieve the timetable.

    Returns:
        list[dict]: Formatted timetable data containing day, period, subject, room, teacher, and attendance information.
    """

    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        storage = json.load(f)

    cookies = {c["name"]: c["value"] for c in storage["cookies"]}

    async with httpx.AsyncClient(cookies=cookies) as client:
        r = await client.post(
            "https://kedron.eq.daymap.net/daymap/timetable/timetable.aspx/GetTimetable",
            headers={
                "content-type": "application/json; charset=UTF-8",
                "x-requested-with": "XMLHttpRequest",
                "referer": "https://kedron.eq.daymap.net/daymap/timetable/timetable.aspx",
            },
            json={"weekStart": week_start, "id": None},
        )

    r.raise_for_status()
    html = r.json()["d"]

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="tblTt")
    rows = table.find_all("tr")

    days = [c.get_text(" ", strip=True) for c in rows[0].find_all(["th", "td"])[1:]]

    timetable = []

    for row in rows[1:]:
        cells = row.find_all("td", recursive=False)
        if not cells:
            continue

        period = cells[0].get_text(strip=True)

        for day, cell in zip(days, cells[1:]):
            tt_cell = cell.find("div", class_="ttCell")
            if not tt_cell:
                continue

            subject_el = tt_cell.find("div", class_="ttSubject")
            room_el = tt_cell.find("div", class_="ttRoom")
            alert_el = tt_cell.find("div", class_="ttAlert")

            subject = subject_el.get_text(strip=True) if subject_el else None

            room, teacher = None, None
            if room_el:
                parts = [
                    p.strip()
                    for p in re.split(r"[\r\n]+", room_el.get_text("\n", strip=True))
                    if p.strip()
                ]
                if len(parts) > 0:
                    room = parts[0]
                if len(parts) > 1:
                    teacher = parts[1]

            attendance = None
            if alert_el:
                img = alert_el.find("img")
                if img:
                    attendance = img.get("title")

            timetable.append(
                {
                    "day": day,
                    "period": period,
                    "subject": subject,
                    "room": room,
                    "teacher": teacher,
                    "attendance": attendance,
                }
            )

    return timetable


async def get_period_info(week: str, day: str, period: str):
    timetable = await get_timetable(week)

    for i in timetable:
        if i["day"] == day and i["period"] == period:
            return {"subject": i["subject"], "room": i["room"], "teacher": i["teacher"]}

    return None
