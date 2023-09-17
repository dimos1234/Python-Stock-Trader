# Python-Stock-Trader
An attempt to create a stock trading bot that uses the TD Ameritrade API and basic trading indicators.

If you want to use this, create a seperate file in the main branch and name it "configs"
Make a python file that uses the following code and add in your TD Ameritrade account number and ID. You need an access token in TS_STATE.JSON for this to work as well as a TD Ameritrade account, therefore it is not very practical.

from configparser import ConfigParser

config = ConfigParser()

config.add_section('main')
config.set('main', 'CLIENT_ID', 'ID HERE')
config.set('main', 'REDIRECT_URI', 'http://localhost')
config.set('main', 'JSON_PATH', 'PATH TO TS_STATE.JSON')
config.set('main', 'ACCOUNT_NUMBER', 'NUMBER HERE')

with open(file='configs/config.ini', mode='w+') as f:
    config.write(f)
