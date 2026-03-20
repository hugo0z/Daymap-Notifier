import asyncio
from datetime import datetime
from pathlib import Path
from string import Template

import daymap
import settings
from desktop_notifier import DesktopNotifier

BASE_DIR = Path(__file__).resolve().parents[2]
LOGO_PATH = BASE_DIR / "logo.png"


async def main():
    config = settings.load_config()
    timetable = config.get("timetable")
    notifier = DesktopNotifier()

    last_triggered = None

    if config["username"] == "":
        email = input("Email: ")
        password = input("Password: ")
        username = email.split("@")[0]

        await daymap.login(email, password, username)

        print("Logged in!")

    while True:
        now = datetime.now()

        current_day = now.strftime("%A")
        current_time = now.strftime("%H:%M")

        if current_day not in timetable:
            await asyncio.sleep(60)
            continue

        for period_name, period_time in timetable[current_day].items():
            if current_time == period_time:
                if last_triggered != (current_day, period_name):
                    notification_message = config.get("notification_message")
                    template = Template(notification_message)

                    period_info = await daymap.get_period_info(
                        now.strftime("%Y-%m-%d"),
                        f"{now.strftime('%a')} {now.day}/{now.month}",
                        period_name,
                    )

                    if period_info is None:
                        print(
                            f"Could not get period info for {current_day=} {period_name=}"
                        )
                        continue

                    new_message = template.safe_substitute(period_info)

                    print(new_message)

                    await notifier.send(
                        title="Next Class!",
                        message=new_message,
                        icon=LOGO_PATH,
                    )

                    last_triggered = (current_day, period_name)

        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
