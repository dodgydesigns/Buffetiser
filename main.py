'''
Created on 4 Jul. 2020

@author: mullsy
'''
import sys

from PySide2.QtWidgets import QApplication

from controller import FatController

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
#     w = TestWindow()
    controller = FatController()

    sys.exit(app.exec_())