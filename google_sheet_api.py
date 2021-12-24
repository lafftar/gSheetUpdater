from datetime import datetime
from dateutil import tz
import gspread
from time import sleep
from gspread_formatting import ConditionalFormatRule, get_conditional_format_rules, GridRange, BooleanRule, \
    BooleanCondition, CellFormat, Color

from utils.custom_logger import Log
from utils.root import get_project_root
from utils.tools import OrderStatusRow

gc = gspread.service_account(filename=f'{get_project_root()}/program_data/auth.json')
sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/10XBH2g1b4W0e-QISct4YKTp5nzXy95s6l00Qmh1uJPw/edit#gid=0')
main_wks = sh.worksheet('Main')
log = Log('[SHEET HANDLER]')


def create_base_sheet():
    # check if base sheet already made.
    first_cell = main_wks.row_values(1)
    headers = ['Item', 'SKU', 'Size', 'Order Number', 'Date of Purchase', 'Purchase Price', 'Status',
               'Status Update Date (EST)']
    if first_cell == headers:
        log.debug('Base sheet already exists.')
        return
    log.debug('Base sheet not found at url. Creating.')

    # create base sheet
    main_wks.update('A1', [headers])
    border = {
        "style": 'SOLID_THICK',
        "colorStyle": {
            'rgbColor': {
                "red": 0,
                "green": 0,
                "blue": 0,
                "alpha": 1
            }
        }
    }
    main_wks.format("A1:H1",
                    {'horizontalAlignment': "CENTER",
                     'borders': {
                         "top": border,
                         "bottom": border,
                         "left": border,
                         "right": border},
                     'textFormat': {
                         "fontSize": 12,
                         "bold": True
                     }
                     })
    log.debug('Base sheet created.')
    add_color_rule()
    update_last_checked()


def add_color_rule():
    delivered = ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('G1:G5000', main_wks)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_CONTAINS', ['Delivered']),
            format=CellFormat(backgroundColor=Color(204/255,1,204/255))
        )
    )
    shipped_to_stockx = ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('G1:G5000', main_wks)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_CONTAINS', ['Shipped To Stockx']),
            format=CellFormat(backgroundColor=Color(1, 204 / 255, 1))
        )
    )
    verified_n_shipped = ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('G1:G5000', main_wks)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_CONTAINS', ['Verified & Shipped']),
            format=CellFormat(backgroundColor=Color(153/255, 204 / 255, 1))
        )
    )
    order_confirmed = ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('G1:G5000', main_wks)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_CONTAINS', ['Order Confirmed']),
            format=CellFormat(backgroundColor=Color(1, 1, 204/255))
        )
    )
    refund_issued = ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('G1:G5000', main_wks)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_CONTAINS', ['Refund Issued']),
            format=CellFormat(backgroundColor=Color(1, 102/255, 102/255))
        )
    )
    rules = get_conditional_format_rules(main_wks)
    rules.clear()
    rules.append(delivered)
    rules.append(shipped_to_stockx)
    rules.append(verified_n_shipped)
    rules.append(order_confirmed)
    rules.append(refund_issued)
    rules.save()
    log.debug('Color rule added.')


line_border = {
    "style": 'SOLID',
    "colorStyle": {
        'rgbColor': {
            "red": 0,
            "green": 0,
            "blue": 0,
            "alpha": 0.5
        }
    }
}


def add_new_row(row):
    main_wks.insert_row(list(row), index=2)
    # will only work if new rows are added sequentially.
    main_wks.format(f"A3:H3",
                    {'horizontalAlignment': "CENTER",
                     'borders': {
                         "top": line_border,
                         "bottom": line_border,
                         "left": line_border,
                         "right": line_border}})
    log.debug('Row added.')
    update_last_checked()


def add_many_rows(rows: list[list, ...]):
    start = len(main_wks.get_values()) + 1
    end = start + len(rows) - 1
    main_wks.append_rows(table_range=f'A{start}:A{end}', values=rows)
    main_wks.format(f"A{start}:H{end}",
                    {'horizontalAlignment': "CENTER",
                     'borders': {
                         "top": line_border,
                         "bottom": line_border,
                         "left": line_border,
                         "right": line_border}})
    log.debug('Added many rows.')
    update_last_checked()


tz = tz.gettz('America/New York')


def update_last_checked():
    pretty_time = datetime.now(tz=tz).strftime('%a %d %b %Y - %I:%M:%S %p')
    # clear all row values and formats
    clear_sheet(start='J1')

    # update and format last updated row
    main_wks.update(f'J1:J2', [['Last Updated'], [pretty_time]])
    main_wks.format(f'J1', {"backgroundColorStyle":
                                {"rgbColor": {"red": 204 / 255, "green": 204 / 255, "blue": 255 / 255, "alpha": 0.1}}
                            })
    main_wks.format(f'J1:J2',
                    {'horizontalAlignment': "CENTER",
                     'borders': {
                         "top": line_border,
                         "bottom": line_border,
                         "left": line_border,
                         "right": line_border}})
    main_wks.format(f'J1', {'textFormat': {'bold': True, 'fontSize': 14}})
    sleep(0.05)
    main_wks.format(f'J2', {'textFormat': {'fontSize': 12},
                            "backgroundColorStyle":
                                {"rgbColor": {"red": 102 / 255, "green": 204 / 255, "blue": 255 / 255, "alpha": 0.1}}
                            })

    log.debug('Updated last checked.')


def clear_sheet(start='A1'):
    main_wks.batch_clear([f'{start}:K3000'])
    main_wks.format(f'{start}:K3000', {'borders': {
            "top": {"style": 'NONE'},
            "bottom": {"style": 'NONE'},
            "left": {"style": 'NONE'},
            "right": {"style": 'NONE'}},
            "backgroundColorStyle":
                {"rgbColor": {"red": 255 / 255, "green": 255 / 255, "blue": 255 / 255, "alpha": 0.1}
                 }})
    log.debug('Sheet cleared.')

