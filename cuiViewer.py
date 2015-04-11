import widgets
#reload(widgets)

from ui import maya_main_window
from PySide.QtGui import *
from PySide.QtCore import *
from maya import mel

import pymel.core as pm
import maya.cmds as mc
import json
import utils

class CUILayoutWidget(QWidget):
  def __init__(self):
    super(CUILayoutWidget, self).__init__()
    self.controls = {}
    self.w = 0
    self.h = 0
    self.characterName = ""
    self.timer = self.startTimer(500)
    self.setFocusPolicy(Qt.StrongFocus)
    self.symbols = {
      "pm": pm,
      "mc": mc,
      "cui": self
    }

  def paintEvent(self, event):
    opt = QStyleOption()
    opt.initFrom(self)
    p = QPainter(self)
    self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

  def timerEvent(self, event):
    if not self.hasFocus():
      self.updateControls()

  def closeEvent(self, event):
    self.killTimer(self.timer)
    event.accept()

  def focusInEvent(self, event):
    self.killTimer(self.timer)

  def focusOutEvent(self, event):
    self.timer = self.startTimer(500)

  def addControl(self, control):
    self.controls[control.cid] = control

  def updateBackground(self):
    if self.background is None:
      return

    imagePath = utils.charactersDir()+self.background
    self.setStyleSheet("CUILayoutWidget {background-image: url(%s); background-repeat: none;}" % imagePath)

  def updateControls(self):
    for control in self.controls.values():
      control.updateControl()

  def showByCid(self, cid, obj=False):
    self.controls[cid].show()
    
    if obj and isinstance(self.controls[cid], widgets.Selector):
      for obj in self.controls[cid].target_objs:
        pm.setAttr("{}.visibility".format(obj), True)

  def hideByCid(self, cid, obj=False):
    self.controls[cid].hide()

    if obj and isinstance(self.controls[cid], widgets.Selector):
      for obj in self.controls[cid].target_objs:
        pm.setAttr("{}.visibility".format(obj), False)

  def showByTag(self, tag, obj=False):
    for control in self.controls.values():
      if tag in control.tags:
        control.show()
        
        if obj and isinstance(control, widgets.Selector):
          for obj in control.target_objs:
            pm.setAttr("{}.visibility".format(obj), True)

  def hideByTag(self, tag, obj=False):
    for control in self.controls.values():
        if tag in control.tags:
          control.hide()

          if obj and isinstance(control, widgets.Selector):
            for obj in control.target_objs:
              pm.setAttr("{}.visibility".format(obj), False)

  def selectByTag(self, tag):
    pm.select([])

    for control in self.controls.values():
      if isinstance(control, widgets.Selector) and tag in control.tags:
        pm.select(control.target_objs, add=1)

class CUIViewer(QDialog):
  def __init__(self):
    super(CUIViewer, self).__init__(maya_main_window())
    self.setWindowFlags(Qt.Window)
    self.setAttribute(Qt.WA_DeleteOnClose)
    self.setWindowTitle("Character UI Viewer")
    self.setObjectName("CUIViewerMain")
    self.setFixedSize(400, 300)
    self.verticalLayout = QVBoxLayout(self)
    self.tabWidget = QTabWidget(self)
    self.tabWidget.setDocumentMode(True)
    self.verticalLayout.addWidget(self.tabWidget)
    self.verticalLayout.setContentsMargins(1, 1, 1, 1)

    self.tabWidget.currentChanged.connect(self.matchTabSize)

    self.loadUi()

  def matchTabSize(self):
    if self.tabWidget.currentWidget():
      w = self.tabWidget.currentWidget().w + 10
      h = self.tabWidget.currentWidget().h + 20
      self.setFixedSize(w, h)

  def closeEvent(self, event):
    while self.tabWidget.currentWidget():
      tab = self.tabWidget.currentWidget()
      tabId = self.tabWidget.currentIndex()
      self.tabWidget.removeTab(tabId)
      tab.deleteLater()

  def keyPressEvent(self, event):
    if event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier:
      self.loadUi()

    elif event.key() == Qt.Key_W and event.modifiers() == Qt.ControlModifier:
      self.tabWidget.setCurrentIndex(self.tabWidget.currentIndex() - 1)

    elif event.key() == Qt.Key_E and event.modifiers() == Qt.ControlModifier:
      self.tabWidget.setCurrentIndex(self.tabWidget.currentIndex() + 1)

    elif event.key() == Qt.Key_R and event.modifiers() == Qt.ControlModifier:
      tab = self.tabWidget.currentIndex()
      self.tabWidget.removeTab(tab)
      tab.deleteLater()

    elif event.key() == Qt.Key_Q:
      mel.eval("SelectToolOptionsMarkingMenu; dR_SelectToolMarkingMenuPopDown;")

    elif event.key() == Qt.Key_W:
      mel.eval("TranslateToolWithSnapMarkingMenu; dR_TranslateToolMarkingMenuPopDown;")

    elif event.key() == Qt.Key_E:
      mel.eval("RotateToolWithSnapMarkingMenu; dR_RotateToolMarkingMenuPopDown;")

  def loadUi(self):
    result = QFileDialog.getOpenFileName(self, "Open", utils.charactersDir(), "CUI files (*.cui)")
    if result[1]:
      fileName = result[0]
    else:
      return

    with open(fileName, "r") as inputFile:
      jsonData = json.load(inputFile)

    tab = CUILayoutWidget()

    tab.w = jsonData["window_width"]
    tab.h = jsonData["window_height"]
    tab.background = jsonData["background_image"]
    tab.updateBackground()
    tab.characterName = jsonData["name"]

    for ctrl in jsonData["controls"]:
      controlType = ctrl.keys()[0]
      control = ctrl[controlType]

      if controlType == "selector":
        selector = widgets.Selector(tab)
        selector.deserialize(control)
        selector.setup(client=True)
        tab.addControl(selector)

      elif controlType == "slider":
        slider = widgets.Slider(tab)
        slider.deserialize(control)
        slider.setup(client=True)
        tab.addControl(slider)
        
      elif controlType == "command_button":
        cmdButton = widgets.CommandButton(tab)
        cmdButton.deserialize(control)
        cmdButton.setup(client=True)
        tab.addControl(cmdButton)

      elif controlType == "checkbox":
        checkBox = widgets.CheckBox(tab)
        checkBox.deserialize(control)
        checkBox.setup(client=True)
        tab.addControl(checkBox)

    self.tabWidget.addTab(tab, tab.characterName)