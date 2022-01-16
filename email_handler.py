from datetime import datetime, timedelta
from random import randint

import imap_tools
from imap_tools import MailBox, AND
from pytz import timezone
from regex import search

from utils.custom_logger import Log
from utils.root import get_project_root
from utils.tools import OrderStatusRow

log = Log('[GMAIL HANDLER]')


class count:
    emails_grabbed = 0


timezone = timezone("America/Toronto")


def login_to_mailbox(_user: str = 'Wisestockx@gmail.com', _passwd: str = 'rqfshscyeufhmeou', folder: str = 'Inbox'):
    mailbox = None
    try:
        mailbox = MailBox('imap.gmail.com').login(_user, _passwd, initial_folder=folder)
        log.info(f'Logged in to {_user} on folder {folder}.')
    except imap_tools.errors.MailboxFolderSelectError:
        log.warn(f'{folder} folder not found in {_user}')
    return mailbox


def grab_links_from_day(mail_box, out: list, _day: int = 0, folder: str = 'Inbox', _user: str = 'Wisestockx@gmail.com'):
    def return_found(reg_list: list, text, return_not_found: bool = False, msg_date=None):
        for reg in reg_list:
            found = search(reg, text)
            if found:
                return found.group(1)
        if return_not_found:
            j1g = msg.date.astimezone(timezone).strftime('%d/%Y %I/%M')
            return f"Not Found - {j1g}"

        log.error('Error Parsing Email. Looks like email format has changed. '
                  'Message winwinwinwin#0001 on discord.')
        with open('error_parsing_this_email.html', 'w', encoding='utf-8') as file:
            file.write(msg.html)
        input()
        return 'Not Found'

    _day_str = None
    num_emails_found = 0

    if _day == 0:
        _day_str = 'Today'
    if _day == 1:
        _day_str = 'Yesterday'
    if _day > 1:
        _day_str = f'{_day} days ago'

    printed = False
    allowed_subjects = ('Delivered', 'Order Confirmed', 'Shipped To StockX',
                        'Refund Issued', 'Verified & Shipped', 'Arrived At StockX', 'Update On Your Order Status')
    for msg in mail_box.fetch(
            AND(from_='noreply@stockx.com',
                date=datetime.date(datetime.today() - timedelta(days=_day)),
                ),
            mark_seen=False,
            bulk=False
    ):
        if not printed:
            log.info(f'Currently Grabbing {folder} in {_user} from {_day_str}')
            printed = True

        status = None
        for subj in allowed_subjects:
            if subj in msg.subject:
                status = subj

        if not msg.html:
            return

        if 'Update On Your Order Status' in msg.subject:
            status = 'Refund Issued'

        if not status:
            continue
        est_time = msg.date.astimezone(timezone).strftime('%a %d %b %Y - %I:%M:%S %p')
        item = return_found(
            [
                r'<td id=\"productname\"[\s\S]+?\"><a[\s\S]+?\">([\s\S]+?)</a',
                r'<td class=\"productName\"[\s\S]+?\"><a[\s\S]+?\">([\s\S]+?)</a'
            ], msg.html)
        sku = return_found(
            [
                r'\">Style ID:</span>&nbsp;([\s\S]+?)</li>',
                r'\">Style ID:&nbsp;([\s\S]+?)</li>'
            ], msg.html)
        size = return_found(
            [
                r'\">[\s\S]+?Size:</span>&nbsp;([\s\S]+?)</li>',
                r'\">[\s\S]+?Size:&nbsp;([\s\S]+?)</li>'
            ], msg.html)
        order_number = return_found(
            [
                r'\">[\s\S]+?Order number:</span>&nbsp;([\s\S]+?)</li>',
                r'\">[\s\S]+?Order number:&nbsp;([\s\S]+?)</li>'
            ], msg.html, return_not_found=True, msg_date=msg.date)
        purchase_price = return_found(
            [
                r'\">Total Payment</span></td>[\s\S]+?\">[\s\S]+?\">\$([\s\S]+?)\*</',
                r'\">Total Payment</td>[\s\S]+?\">[\s\S]+?([\s\S]+?)\*</'
            ], msg.html, return_not_found=True, msg_date=msg.date)
        num_emails_found += 1

        # update_title(f'Emails Grabbed - [{count.emails_grabbed}]')
        row = OrderStatusRow(
            item=item,
            sku=sku,
            size=size,
            order_num=order_number,
            date_of_purchase='Not Set',
            purchase_price=purchase_price,
            status=status,
            status_update_date=est_time
        )
        if row.order_num == 'Not Found':
            continue
        out.append(row)

        # total emails grabbed
        count.emails_grabbed += 1

    if num_emails_found != 0:
        log.info(f'Done Grabbing {num_emails_found} Emails. {folder} in {_user} from {_day_str}')
    else:
        log.info(f'No Emails Found. {folder} in {_user} from {_day_str}')


def return_today_emails() -> list[OrderStatusRow]:
    out = []
    mail_box = login_to_mailbox()
    for day in range(3):  # gets last 3 days, jic.
        grab_links_from_day(mail_box=mail_box, _day=day, out=out)
    out.reverse()  # reversing so we start from the oldest.
    return out


def grab_all():
    out = []
    mail_box = login_to_mailbox()
    for day in range(200):
        grab_links_from_day(_day=day, out=out, mail_box=mail_box)

    out = [', '.join(OrderStatusRow._fields)] + [', '.join(item) for item in out]

    with open(f'{get_project_root()}/program_data/orders.csv', 'w') as file:
        file.write('\n'.join(out))


if __name__ == "__main__":
    a = return_today_emails()
    print(a)
    for row in a:
        print(row)
        print(row.status_update_date)
