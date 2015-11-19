from __future__ import division
import sys
import datetime
import math
from PyQt4 import QtCore
import MOSES
import time
import pandas as pd

class IncredibleBulk(QtCore.QThread):
    sendCategoryTree = QtCore.pyqtSignal(pd.DataFrame)
    sendActivity = QtCore.pyqtSignal(int, str)
    sendEmployeesList = QtCore.pyqtSignal(pd.DataFrame)
    sendBrandList = QtCore.pyqtSignal(list)

    def __init__(self, user_id, password, *args, **kwargs):
        super(IncredibleBulk, self).__init__(*args, **kwargs)
        self.mutex = QtCore.QMutex()
        self.condition = QtCore.QWaitCondition()

        self.user_id, self.password = user_id, password
        if not self.isRunning():
            self.start(QtCore.QThread.LowPriority)

    def __del__(self):
        self.mutex.lock()
        self.condition.wakeOne()
        self.mutex.unlock()
        self.wait()

    def run(self):
        self.allow_run = True
        while True:
            self.mutex.unlock()
            if self.allow_run:
                self.sendActivity.emit(0, "Started fetching category tree at %s."%(datetime.datetime.now()))
                self.sendCategoryTree.emit(MOSES.getCategoryTree(self.user_id, self.password))
                self.sendActivity.emit(50, "Started fetching employees' data at %s."%(datetime.datetime.now()))
                self.sendEmployeesList.emit(MOSES.getEmployeesList(self.user_id, self.password, datetime.date.today()))
                self.sendActivity.emit(60, "Started fetching brand' list at %s."%(datetime.datetime.now()))
                self.sendBrandList.emit(MOSES.getBrandValues(self.user_id, self.password))
                self.sendActivity.emit(80, "Started updating work calendar at %s."%(datetime.datetime.now()))
                MOSES.checkAndInitWorkCalendar(self.user_id, self.password, datetime.date.today())
                self.sendActivity.emit(100, "Finished fetching data at %s."%(datetime.datetime.now()))
                self.allow_run = False
            self.mutex.lock()



