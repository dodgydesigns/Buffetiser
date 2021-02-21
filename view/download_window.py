import json
import threading
import os
from datetime import datetime

import requests
from PySide2.QtCore import QObject, Signal, Qt
from PySide2.QtGui import QPalette, QBrush, QColor

from control.config import COLOUR0, COLOUR3
# from model.CoinSpot import Coinspot
from model.CoinSpot import Coinspot
from model.data_structures import InvestmentType
from view.qroundprogressbar import QRoundProgressBar

DATA_PATH = 'data'


class DownloadSignal(QObject):
    sig = Signal(object)


class DownloadThread(threading.Thread):
    downloadingFinished = DownloadSignal()

    def __init__(self, fatController, symbol=None):
        threading.Thread.__init__(self)
        self.downloadingWindow = fatController.view.mainWindow.progressDialog
        self.downloadingWindow.show()
        self.fatController = fatController
        self.portfolio = fatController.model.portfolio
        self.symbol = symbol
        self.halt = False

    def run(self):

        today = datetime.today()
        if self.symbol:
            self.portfolio = [stock.code for stock in self.portfolio if stock.code == self.symbol]
        try:
            os.mkdir(DATA_PATH)
        except FileExistsError as error:
            if os.path.isdir(DATA_PATH):
                pass
            else:
                print('Unexpected FileExistsError while creating data directory:', error)
        except OSError as error:
            print('Unexpected OSError while creating data directory:', error)

        self.getConversionRate()

        numberOfStocks = len(self.portfolio)
        for count, investment in enumerate(self.portfolio):
            if not self.halt:
                if investment.investmentType == InvestmentType.Share:
                    # Update historical share data
                    self.getShare(today, investment)

                elif investment.investmentType == InvestmentType.Crypto:
                    # Update historical crypto data
                    self.getCrypto(today, investment)

                self.downloadingWindow.setProgress(((1 + count) / numberOfStocks) * 100, investment.code)
                self.downloadingFinished.sig.emit(investment)
        self.downloadingWindow.hide()

    def getConversionRate(self):
        url = 'https://www.freeforexapi.com/api/live?pairs=USDAUD'
        self.fatController.usdToAudConversion = float(requests.get(url=url).json()['rates']['USDAUD']['rate'])
        self.fatController.model.writeUsdToAudConversionValue()

    def getShare(self, today, investment):
        url = 'https://eodhistoricaldata.com/api/eod/' + \
              investment.code + \
              '.AU?api_token=' + \
              self.fatController.key + \
              '&fmt=json' + \
              '&from={}-{}-{}'.format(today.year - 1, today.month, today.strftime("%d")) + \
              '&to={}-{}-{}'.format(today.year, today.month, today.strftime("%d")) + \
              '&g=m'
        response = requests.get(url=url).json()
        with open(os.path.join(DATA_PATH, f'data-{investment.code}.txt'), 'w') as outfile:
            json.dump(response, outfile)

        # Update current priceHistory
        url = 'https://eodhistoricaldata.com/api/real-time/' + \
              investment.code + \
              '.AU?api_token=' + \
              self.fatController.key + \
              '&fmt=json'
        response = requests.get(url=url).json()
        investment.livePrice = float(response['close'])

    def getCrypto(self, today, investment):
        url = 'https://eodhistoricaldata.com/api/eod/' + \
              investment.code + \
              '-USD.CC?api_token=' + \
              self.fatController.key + \
              '&order=m' + \
              '&fmt=json' + \
              '&from={}-{}-{}'.format(today.year - 1, today.month, today.strftime("%d")) + \
              '&to={}-{}-{}'.format(today.year, today.month, today.strftime("%d")) + \
              '&g=m'

        response = requests.get(url=url).json()
        with open(os.path.join(DATA_PATH, f'data-{investment.code}.txt'), 'w') as outfile:
            json.dump(response, outfile)

        # Update current priceHistory
        url = 'https://eodhistoricaldata.com/api/real-time/' + \
              investment.code + \
              '-USD.CC?api_token=' + \
              self.fatController.key + \
              '&fmt=json'
        response = requests.get(url=url).json()

        investment.livePrice = float(response['close']) * self.fatController.usdToAudConversion if response['close'] != 'NA' else investment.priceHistory['close'][-1]

    def getCoinSpot(self):
        api_key = '7a95f252'
        api_secret = '08TV3MDJUQN7JDM5L8PQHUUTCCZHTFRMBACL2L'

        client = Coinspot(api_key, api_secret)
        print(client.balances())
        print(self.portfolio)


class DownloadWindow(QRoundProgressBar):
    def __init__(self):
        super(DownloadWindow, self).__init__()

        self.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.setStyleSheet("""QWidget {background-color: """ + COLOUR0 + """}""")
        palette = QPalette()
        brush = QBrush(QColor(COLOUR3))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Highlight, brush)

        self.setPalette(palette)
        self.setFixedSize(50, 50)

    def setProgress(self, value, text):
        self.setValue(value, text)
