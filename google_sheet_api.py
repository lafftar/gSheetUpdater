from datetime import datetime
from dateutil import tz
import gspread
from time import sleep

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
                         "right": border}})
    log.debug('Base sheet created.')


def return_cell_color(cell_val):
    fmt = {"backgroundColorStyle": {"rgbColor": {}}}
    if cell_val == 'Delivered':
        fmt["backgroundColorStyle"]["rgbColor"] = {"red": 204 / 255, "green": 255 / 255, "blue": 204 / 255,
                                                   "alpha": 0.1}
    if cell_val == 'Shipped To Stockx':
        fmt["backgroundColorStyle"]["rgbColor"] = {"red": 255 / 255, "green": 204 / 255, "blue": 255 / 255,
                                                   "alpha": 0.1}
    if cell_val == 'Verified & Shipped':
        fmt["backgroundColorStyle"]["rgbColor"] = {"red": 153 / 255, "green": 204 / 255, "blue": 255 / 255,
                                                   "alpha": 0.1}
    if cell_val == 'Order Confirmed':
        fmt["backgroundColorStyle"]["rgbColor"] = {"red": 255 / 255, "green": 255 / 255, "blue": 204 / 255,
                                                   "alpha": 0.1}
    if cell_val == 'Refund Issued':
        fmt["backgroundColorStyle"]["rgbColor"] = {"red": 255 / 255, "green": 102 / 255, "blue": 102 / 255,
                                                   "alpha": 0.1}
    return fmt


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


def add_new_row():
    # get newest row
    row = OrderStatusRow(
        *('Refund Issued' for _ in range(8))
    )
    print(row)
    end = len(main_wks.get_values()) + 1
    main_wks.update(f'A{end}', [list(row)])
    main_wks.format(f"A{end}:H{end}",
                    {'horizontalAlignment': "CENTER",
                     'borders': {
                         "top": line_border,
                         "bottom": line_border,
                         "left": line_border,
                         "right": line_border}})
    main_wks.format(f"G{end}", return_cell_color(row.status))
    log.debug('Row added.')
    pass


tz = tz.gettz('America/New York')


def update_last_checked():
    pretty_time = datetime.now(tz=tz).strftime('%a %d %b %Y - %H:%M:%S')
    main_wks.format(f'J11', {"backgroundColorStyle":
                                 {"rgbColor": {"red": 204 / 255, "green": 204 / 255, "blue": 255 / 255, "alpha": 0.1}}
                             })
    main_wks.update(f'J10:J11', [['Last Updated'], [pretty_time]])
    main_wks.format(f'J10:J11',
                    {'horizontalAlignment': "CENTER",
                     'borders': {
                         "top": line_border,
                         "bottom": line_border,
                         "left": line_border,
                         "right": line_border}})
    main_wks.format(f'J10', {'textFormat': {'bold': True, 'fontSize': 14}})
    sleep(0.05)
    main_wks.format(f'J11', {'textFormat': {'fontSize': 12},
                             "backgroundColorStyle":
                                 {"rgbColor": {"red": 102 / 255, "green": 204 / 255, "blue": 255 / 255, "alpha": 0.1}}
                             })

while True:
    update_last_checked()
    sleep(3)

"""
https://docs.gspread.org/en/latest/user-guide.html#updating-cells
https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#cellformat
https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#Color

"""
