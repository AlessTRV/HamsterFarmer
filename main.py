import os

import aiohttp
import asyncio
import logging
import coloredlogs
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone, timedelta
from typing import NoReturn, Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

TOKEN: str = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
coloredlogs.install(
    level='DEBUG',
    logger=logger,
    fmt='%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s',
    level_styles=dict(
        debug={"color": "green", "bright": True},
        info={"color": "white", "bright": True},
        warning={"color": "yellow", "bright": True},
        error={"color": "red", "bright": True},
    ),
    field_styles=dict(
        asctime={"color": "blue", "bright": True},
        message={"color": "white", "bright": True},
        name={"color": "white"},
        levelname={"color": "white"},
    ),
    milliseconds=True
)

HEADERS = {
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'it-IT,it;q=0.5',
    'Authorization': f'Bearer {TOKEN}',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Host': 'api.hamsterkombat.io',
    'Origin': 'https://hamsterkombat.io',
    'Referer': 'https://hamsterkombat.io/',
    'Sec-Ch-Ua': '"Brave";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Gpc': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
}

API_URLS = {
    'tap': 'https://api.hamsterkombat.io/clicker/tap',
    'boosts': 'https://api.hamsterkombat.io/clicker/boosts-for-buy',
    'buy-boosts': 'https://api.hamsterkombat.io/clicker/buy-boost',
    'daily-cipher': 'https://api.hamsterkombat.io/clicker/claim-daily-cipher',
    'sync': 'https://api.hamsterkombat.io/clicker/sync'
}

cipher: str = "WEB3"


async def fetch_post(url: str, data: Optional[Dict] = None) -> Optional[Dict]:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=HEADERS) as response:
            if response.status == 200:
                return await response.json()
            logger.error(f"Failed request to {url}. Status code: {response.status}, Response: {await response.json()}")
            return None


async def do_taps(count: int, available_taps: int) -> NoReturn:
    data = {
        "count": count,
        "availableTaps": available_taps,
        "timestamp": int(datetime.now(timezone.utc).timestamp())
    }
    result = await fetch_post(API_URLS['tap'], data)
    if result:
        clicker_user = result.get("clickerUser", {})
        logger.info(
            f"Tap request sent successfully: Total coins: {clicker_user.get('totalCoins')} | Balance coins: {clicker_user.get('balanceCoins')} | Available taps: {clicker_user.get('availableTaps')} | Max taps: {clicker_user.get('maxTaps')}")


async def get_boosts() -> Optional[List[Dict]]:
    result = await fetch_post(API_URLS['boosts'])
    if result:
        logger.info(f"Boosts request sent successfully: {len(result.get('boostsForBuy', []))} boosts available.")
        return result.get("boostsForBuy")
    return None


async def buy_boost(boost_id: int) -> NoReturn:
    data = {
        "boostId": boost_id,
        "timestamp": int(datetime.now(timezone.utc).timestamp())
    }
    result = await fetch_post(API_URLS['buy-boosts'], data)
    if result:
        logger.info(f"Boost {boost_id} bought successfully: {result}")


async def claim_daily_cipher() -> NoReturn:
    data = {"cipher": cipher}
    result = await fetch_post(API_URLS['daily-cipher'], data)
    if result:
        logger.info(f"Daily cipher claimed successfully: {result}")


async def sync() -> Optional[Dict[str, Any]]:
    result = await fetch_post(API_URLS['sync'])
    if result:
        clicker_user = result.get("clickerUser", {})
        logger.info(
            f"Sync request sent successfully: Total coins: {clicker_user.get('totalCoins')} | Balance coins: {clicker_user.get('balanceCoins')} | Available taps: {clicker_user.get('availableTaps')} | Max taps: {clicker_user.get('maxTaps')}")
        return result
    return None


async def claim_boosts() -> bool:
    boosts = await get_boosts()
    if not boosts:
        logger.warning("No boosts available to claim.")
        return False

    for boost in boosts:
        if boost.get("cooldownSeconds", 0) > 0 or boost.get("price", 0) > 0:
            logger.debug(
                f"Skipping boost {boost.get('id')} with cooldown {boost.get('cooldownSeconds')} and price {boost.get('price')}.")
            continue

        await buy_boost(boost.get("id"))
        await asyncio.sleep(1)
        return True
    return False


async def execute_taps() -> NoReturn:
    sync_data = await sync()
    if sync_data:
        clicker_user = sync_data.get('clickerUser', {})
        taps_to_do = int(clicker_user.get('availableTaps', 0) / clicker_user.get('earnPerTap', 1))
        logger.info(f"Calculated taps to do: {taps_to_do}")
        await do_taps(taps_to_do, clicker_user.get('availableTaps', 0))
        await asyncio.sleep(1)
        if await claim_boosts():
            logger.info("Boost claimed, recalculating taps.")
            await execute_taps()


async def schedule_next_sync() -> NoReturn:
    sync_data = await sync()
    if sync_data:
        clicker_user = sync_data.get('clickerUser', {})
        seconds_to_full = (clicker_user.get('maxTaps', 0) - clicker_user.get('availableTaps', 0)) / 3
        logger.info(f"Scheduling next sync in {seconds_to_full} seconds.")

        boosts = await get_boosts()
        boost_full_available_taps = next(
            (boost for boost in boosts if boost.get("id") == "BoostFullAvailableTaps"), None)

        if boost_full_available_taps:
            cooldown_seconds = boost_full_available_taps.get("cooldownSeconds", 0)
            if cooldown_seconds < seconds_to_full * 0.75:
                adjusted_seconds = cooldown_seconds
                logger.info(f"Scheduling next sync in {adjusted_seconds} seconds due to BoostFullAvailableTaps.")
                scheduler.add_job(execute_taps_and_schedule, 'date',
                                  run_date=datetime.now() + timedelta(seconds=adjusted_seconds))
            else:
                logger.info("BoostFullAvailableTaps cooldown is too high, skipping adjustment.")
                scheduler.add_job(execute_taps_and_schedule, 'date',
                                  run_date=datetime.now() + timedelta(seconds=seconds_to_full))
        else:
            logger.info("No BoostFullAvailableTaps found, skipping adjustment.")
            scheduler.add_job(execute_taps_and_schedule, 'date',
                              run_date=datetime.now() + timedelta(seconds=seconds_to_full))


async def execute_taps_and_schedule() -> NoReturn:
    await execute_taps()
    await schedule_next_sync()


if __name__ == '__main__':
    scheduler = AsyncIOScheduler()
    scheduler.start()

    loop = asyncio.get_event_loop()
    scheduler.add_job(execute_taps_and_schedule, 'date', run_date=datetime.now())

    try:
        loop.run_forever()
        logger.info("Event loop started.")
    except (KeyboardInterrupt, SystemExit):
        loop.close()
        scheduler.shutdown()
        logger.info("Event loop stopped.")
    else:
        logger.error("Event loop stopped unexpectedly.")
