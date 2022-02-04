import asyncio
from os import system
from time import sleep

import aiohttp
import requests
from discord import Colour

from email_handler import return_today_emails
from google_sheet_api import add_many_rows, create_base_sheet, add_color_rules, add_new_row, update_last_checked
from utils.custom_logger import Log
from utils.root import get_project_root
from utils.tools import OrderStatusRow, strip_each, return_orders, add_date_of_purchase
from utils.webhook import send_webhook

log = Log('[MONITOR]')


def first_load():
    out = return_orders()
    # write to sheet in batch
    create_base_sheet()
    add_many_rows(out)
    add_color_rules()


def monitor_new():
    # check for new items from today
    # check if they're in checked.txt
    # if they're not in checked.txt, call `add_one` and add to checked.txt, then reload checked.txt

    # load checked files
    with open(f'{get_project_root()}/program_data/checked.txt') as file:
        checked = file.read()

    with open(f'{get_project_root()}/program_data/orders.csv') as file:
        orders = [OrderStatusRow(*strip_each(line)) for line in file.readlines()[1:]
                  if len(list(strip_each(line))) == 8]

    # populate base dop
    dop = {}
    for row in orders:
        similar_rows = list(filter(lambda line: row.order_num in line, orders))
        add_date_of_purchase(similar_rows, dop)

    # grab today's emails
    todays_emails = return_today_emails()

    # check if it's in our checked file
    for row in todays_emails:
        if f'{row.order_num}-{row.status}' in checked:
            log.debug(f'{row.order_num}-{row.status} - In Checked - {row.status_update_date}')
            continue
        log.debug(f'{row.order_num}-{row.status} - New - {row.status_update_date}')
        orders.append(row)
        # use new row to calculate new dop
        similar_rows = list(filter(lambda line: row.order_num in line, orders))
        add_date_of_purchase(similar_rows, dop)

        # add the row
        row = OrderStatusRow(
            row.item,
            row.sku,
            row.size,
            row.order_num,
            dop.get(row.order_num),
            row.purchase_price,
            row.status,
            row.status_update_date,
        )
        add_new_row(row)

        # write to checked.txt
        with open(f'{get_project_root()}/program_data/checked.txt', 'a') as file:
            file.write(f'{row.order_num}-{row.status}\n')

        # write to orders.csv
        with open(f'{get_project_root()}/program_data/orders.csv', 'a') as file:
            file.write(f"{', '.join(row)}\n")
        sleep(5)  # try to avoid 429
    update_last_checked()
    log.debug('Check Complete')


async def run():
    system('cls')
    while True:
        try:
            log.info('Monitor Started')
            while True:
                monitor_new()
                mins = 1
                log.debug(f'Sleeping for {mins} minutes')
                sleep(mins * 60)
        except requests.exceptions.ConnectionError:
            log.error('Connection Error.')
            log.info('Restarting Monitor.')
            continue
        except Exception as err:
            log.exception('Major Error')
            async with aiohttp.ClientSession() as client:
                await send_webhook(
                        webhook_url='https://discord.com/api/webhooks/937925424183402546/'
                                    'ofefABvBFbTxPAMTjoZro6xybTiyzKFjW_Tn1AXAIlKVIQ6kL4BKVkdl50I95h-id9Z3',
                        _dict={'Error': f'{err}'},
                        webhook_client=client,
                        title='WiseGrails gSheetUpdater.',
                        title_link='https://google.com',
                        color=Colour.red()
                    )
            continue


if __name__ == "__main__":
    asyncio.run(run())
