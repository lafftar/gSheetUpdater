import sys
from datetime import datetime
from json import dumps
from typing import NamedTuple

from utils.custom_logger import Log
from utils.root import get_project_root

FIRST_PRINT = False
RANK = {
    'Refund Issued': 6,
    'Delivered': 5,
    'Verified & Shipped': 4,
    'Arrived At StockX': 3,
    'Shipped To StockX': 2,
    'Order Confirmed': 1,
}
log = Log('[TOOLS]')


def strip_each(lines): return (line.strip() for line in lines.split(','))


def add_date_of_purchase(similar_rows: list, dop: dict):
    """
    dop[row.order_num] = row.dop
    Finds the line with `Order Confirmed` as status, makes that that row.dop the dop of all.
    If it can't find `Order Confirmed`, uses the oldest email.

    similar_rows: subset of rows from (`orders.csv` + live grab) that have the same order number
    dop: date_of_purchase dict
    """
    if len(similar_rows) == 1:  # if there's only one row, assume this is the first email
        dop[similar_rows[0].order_num] = similar_rows[0].status_update_date
        return

    order_confirmed_row: list[OrderStatusRow] = list(filter(lambda row: row.status == 'Order Confirmed', similar_rows))
    if order_confirmed_row:
        dop[order_confirmed_row[0].order_num] = order_confirmed_row[0].status_update_date
        return

    # `Order Confirmed` not found, find the oldest email, use that as the dop
    oldest_date = None
    dt_fmt = '%a %d %b %Y - %I:%M:%S %p'
    for row in similar_rows:
        if not oldest_date:
            oldest_date = datetime.strptime(row.status_update_date, dt_fmt)
            continue
        row_date = datetime.strptime(row.status_update_date, dt_fmt)
        if row_date <= oldest_date:
            continue
        oldest_date = row_date

    # turn oldest date back into a string, then add it to dop
    oldest_date = oldest_date.strftime(dt_fmt)
    dop[similar_rows[0].order_num] = oldest_date


def clean_order_num(similar_rows, all_orders):
    """
    deletes from src directly, makes sure only the highest row is in the final list.
    """
    highest_row = None
    for row in similar_rows:
        if not highest_row:
            highest_row = row
            continue
        # `=`: unlikely, just deletes a duplicate. `<`: deletes the current row if it's of lower status.
        if RANK[row.status] <= RANK[highest_row.status]:
            all_orders.remove(row)
            continue
        if RANK[row.status] > RANK[highest_row.status]:
            all_orders.remove(highest_row)
            highest_row = row
            continue


def return_orders() -> list:
    dop = {}
    checked = {}

    with open(f'{get_project_root()}/program_data/orders.csv') as file:
        src = [OrderStatusRow(*strip_each(line)) for line in file.readlines()[1:]
               if len(list(strip_each(line))) == 8]

    # remove by rank
    cleaned = {}  # all the order nums we've seen, speeds up iteration to On, where n is the num of order nums
    for row in src.copy():
        checked[f'{row.order_num}-{row.status}'] = 1
        if row.status == 'Order Confirmed':
            dop[row.order_num] = row.status_update_date
        if cleaned.get(row.order_num, None):
            continue
        # filter returns a generator, then we turn it to a list, runs a fx on every line in an iterable
        # this also includes the row we're iterating over from src
        similar_rows = list(filter(lambda line: row.order_num in line, src.copy()))

        add_date_of_purchase(similar_rows, dop)

        # clean the order num
        if len(similar_rows) > 1:
            clean_order_num(similar_rows, src)

        # add the order num to `cleaned`
        cleaned[row.order_num] = 1

    out = []
    # set status update date for all orders
    for line in src:
        out.append(
            [
                line.item,
                line.sku,
                line.size,
                line.order_num,
                dop.get(line.order_num),
                line.purchase_price,
                line.status,
                line.status_update_date,
            ]
        )
    # write checked to file
    with open(f'{get_project_root()}/program_data/checked.txt', 'w') as file:
        file.write('\n'.join(checked))

    return out


class OrderStatusRow(NamedTuple):
    item: str
    sku: str
    size: str
    order_num: str
    date_of_purchase: str
    purchase_price: str
    status: str
    status_update_date: str


if __name__ == "__main__":
    return_orders()