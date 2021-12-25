from time import sleep
from os import system
import requests

from email_handler import return_today_emails
from google_sheet_api import add_many_rows, create_base_sheet, add_color_rule, add_new_row, update_last_checked
from utils.custom_logger import Log
from utils.root import get_project_root
from utils.tools import OrderStatusRow

log = Log('[MONITOR]')


def strip_each(lines): return (line.strip() for line in lines.split(','))


def first_load():
    dop = {}
    checked = []

    with open(f'{get_project_root()}/program_data/orders.csv') as file:
        src = [OrderStatusRow(*strip_each(line)) for line in file.readlines()[1:]]

    # populate dop
    for line in src:
        if line.status == 'Order Confirmed':
            dop[line.order_num] = line.status_update_date

    out = []
    # set status update date for all orders
    for line in src:
        checked.append(f'{line.order_num}-{line.status}')
        out.append(
            [
                line.item,
                line.sku,
                line.size,
                line.order_num,
                dop.get(line.order_num) or 'Not Found',
                line.purchase_price,
                line.status,
                line.status_update_date,
            ]
        )

    # write checked to file
    with open(f'{get_project_root()}/program_data/checked.txt', 'w') as file:
        file.write('\n'.join(checked))

    # write to sheet in batch
    create_base_sheet()
    add_many_rows(out)
    add_color_rule()


def monitor_new():
    # check for new items from today
    # check if they're in checked.txt
    # if they're not in checked.txt, call `add_one` and add to checked.txt, then reload checked.txt

    # load checked files
    with open(f'{get_project_root()}/program_data/checked.txt') as file:
        checked = file.read()

    # grab today's emails
    todays_emails = return_today_emails()

    # check if it's in our checked file
    for row in todays_emails:
        if f'{row.order_num}-{row.status}' in checked:
            continue

        # add the row
        add_new_row(row)

        # write to checked.txt
        with open(f'{get_project_root()}/program_data/checked.txt', 'a') as file:
            file.write(f'{row.order_num}-{row.status}\n')

        # write to orders.csv
        with open(f'{get_project_root()}/program_data/orders.csv', 'a') as file:
            file.write(f"{', '.join(row)}\n")
    update_last_checked()
    log.debug('Check Complete')


system('clear')
while True:
    try:
        log.info('Monitor Started')
        while True:
            monitor_new()
            log.debug('Sleeping for 5 minutes')
            sleep(360)
    except requests.exceptions.ConnectionError():
        log.error('Connection Error.')
        log.info('Restarting Monitor.')
        continue
    except Exception:
        log.exception('Major Error')
        break