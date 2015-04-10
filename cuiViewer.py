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

  def paintEvent(self, event):
    opt = QStyleOption()
    opt.initFrom(self)
    p = QPainter(self)
    self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

  def timerEvent(self, event):
    if not self.hasFocus():
      print "LALA"
      self.updateControls()

  def closeEvent(self, event):
    self.killTimer(self.timer)
    event.accept()

  def focusInEvent(self, event):
    self.killTimer(self.timer)

  def focusOutEvent(self, event):
    self.timer = self.startTimer(500)

  def updateBackground(self):
    if self.background is None:
      return

    rootDir = pm.workspace(q=1, rd=1)
    charDir = rootDir+"characters/"
    imagePath = charDir+self.background
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
    rootDir = pm.workspace(q=1, rd=1)
    charDir = rootDir+"characters"
    result = QFileDialog.getOpenFileName(self, "Open", charDir, "CUI files (*.cui)")
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
      if ctrl.keys()[0] == "selector":
        newSelector = widgets.Selector(tab)
        newSelector.deserialize(ctrl["selector"])
        newSelector.setup(client=True)
        newSelector.redraw()
        newSelector.clicked.connect(self.selectorTriggered)

        if newSelector.override_color:
          try:
            top_obj = pm.PyNode(newSelector.target_objs[0])
          except:
            pm.warning("Object {} not found. Make sure the correct scene is loaded.".format(newSelector.target_objs[0]))
            continue
          color = utils.getOverrideColor(top_obj)
          if color:
            newSelector.color = color
            newSelector.redraw()

        tab.controls[newSelector.cid] = newSelector

      elif ctrl.keys()[0] == "slider":
        newSlider = widgets.Slider(tab)
        newSlider.deserialize(ctrl["slider"])
        newSlider.setup(client=True)
        newSlider.valueChanged.connect(self.sliderMoved)
        newSlider.released.connect(self.sliderReleased)
        tab.controls[newSlider.cid] = newSlider

      elif ctrl.keys()[0] == "command_button":
        newCommandButton = widgets.CommandButton(tab)
        newCommandButton.deserialize(ctrl["command_button"])
        newCommandButton.setup(client=True)
        newCommandButton.clicked.connect(self.commandButtonTriggered)
        tab.controls[newCommandButton.cid] = newCommandButton

      elif ctrl.keys()[0] == "checkbox":
        newCheckBox = widgets.CheckBox(tab)
        newCheckBox.deserialize(ctrl["checkbox"])
        newCheckBox.setup(client=True)
        newCheckBox.stateChanged.connect(self.checkboxToggled)
        tab.controls[newCheckBox.cid] = newCheckBox

    self.tabWidget.addTab(tab, tab.characterName)

  def selectorTriggered(self):
    selector = self.sender()

    if QApplication.keyboardModifiers() == Qt.ShiftModifier:
      pm.select(selector.target_objs, add=1)
    else:
      pm.select(selector.target_objs)

  def commandButtonTriggered(self):
    button = self.sender()

    if button.function is None:
      vis_range = {
        "pm": pm,
        "mc": mc,
        "cui": button.widget.parent()
        }
      try:
        button.function = utils.compileFunctions(button.cmd, ["clicked"], vis_range)[0]
      except Exception:
        pm.warning("Could not compile commands for this control. Please, check the code")
        return

    button.function()

  def sliderMoved(self):
    slider = self.sender()

    if not slider.target_attr:
      pm.warning("No attribute assigned to this slider")
      return

    range_ = slider.max_attr_val - slider.min_attr_val
    step = range_/100
    val = slider.min_attr_val + slider.value() * step

    if slider.clamp_to_int:
      val = round(val)
    
    utils.undoable_open()
    pm.setAttr(slider.target_attr, val)

  def sliderReleased(self):
    utils.undoable_close()

  def checkboxToggled(self):
    checkbox = self.sender()

    if checkbox.is_dir_ctrl:
      if not checkbox.target_attr:
        pm.warning("No attribute assigned to this checkbox")
        return
      pm.setAttr(checkbox.target_attr, checkbox.isChecked())

    else:
      if not (checkbox.on_cmd and checkbox.off_cmd):
        vis_range = {
          "pm": pm,
          "mc": mc,
          "cui": checkbox.parent()
          }
        try:
          funcs = utils.compileFunctions(checkbox.cmd, ["on", "off"], vis_range)
          checkbox.on_cmd = funcs[0]
          checkbox.off_cmd = funcs[1]
        except Exception:
          pm.warning("Could not compile commands for this control. Please, check the code")
          return

      if checkbox.isChecked():
        checkbox.on_cmd()
      else:
        checkbox.off_cmd()