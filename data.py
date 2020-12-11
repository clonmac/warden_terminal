import ast
import subprocess
import emoji
import dashing
from tabulate import tabulate

from datetime import datetime, timedelta
from dateutil import parser

from connections import test_tor
from ansi_management import (warning, success, error, info, clear_screen, bold,
                             jformat, muted)

from pricing_engine import multiple_price_grab


def data_tor(tor=None):
    if not tor:
        tor = test_tor()

    tor_string = f"""
   {success("Running on port")} {info(bold(tor['port']))}

   Tor  IP Address {tor['post_proxy']['origin']}
   Ping Time {tor['post_proxy_ping']}

   Real IP Address {tor['pre_proxy']['origin']}
   Ping Time {tor['pre_proxy_ping']}

        """
    return (tor_string)


def data_login(return_widget):

    return_widget.append("")
    processes = subprocess.check_output("last")
    processes = list(processes.splitlines())
    for process in processes:
        try:
            process = process.decode("utf-8")
            user = process.split()[0]
            process = process.replace(user, '')
            console = process.split()[0]
            process = process.replace(console, '')
            date_str = parser.parse(process, fuzzy=True)
            # Check if someone logged in the last 60 minutes
            expiration = 60
            too_soon = datetime.now() - timedelta(minutes=expiration)
            if date_str > too_soon:
                warn = warning(emoji.emojize(':warning:'))
                return_widget.append(
                    error(
                        f" {warn} {error(f'User Recently Logged in (last {expiration} min)')}:"
                    ))
            return_widget.append(
                f"   {warning(user)} at {muted(console)} " + bold(
                    f"logged on {success(date_str.strftime('%H:%M (%b-%d)' ))}"
                ))
        except Exception as e:
            return_widget.append(f"  {process}")
            return_widget.append(f"  {e}")

    return (return_widget)


def data_btc_price():
    from node_warden import load_config
    config = load_config(quiet=True)
    updt = muted(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
    fx_config = config['CURRENCIES']
    currencies = ast.literal_eval(fx_config.get('fx_list'))
    primary_fx = ast.literal_eval(fx_config.get('primary_fx'))
    price_data = multiple_price_grab('BTC', ','.join(currencies))

    # Get prices in different currencies
    tabs = []
    for fx in currencies:
        try:
            price_str = price_data['DISPLAY']['BTC'][fx]['PRICE']
            chg_str = price_data['DISPLAY']['BTC'][fx]['CHANGEPCTDAY']
            high = price_data['DISPLAY']['BTC'][fx]['HIGHDAY']
            low = price_data['DISPLAY']['BTC'][fx]['LOWDAY']
            try:
                chg = float(chg_str)
                if chg > 0:
                    chg_str = success(chg_str + ' %')
                elif chg < 0:
                    chg_str = error(chg_str + ' %')
            except Exception:
                chg_str = muted(chg_str + ' %')

            if fx == primary_fx:
                fx = info(fx)
            tabs.append(['  ' + fx, price_str, chg_str, low + ' - ' + high])

        except Exception as e:
            tabs.append([fx, 'error', e])

    tabs = tabulate(tabs,
                    headers=['fx', 'Price', '% change', '24h Range'],
                    colalign=["center", "right", "right", "right"])
    return_widget = dashing.Text(tabs,
                                 title=f'   ₿ Realtime Prices ({updt})  ',
                                 color=7,
                                 border_color=7)

    return return_widget