from . import DEBUG

import widgets
import utils
import ui

if DEBUG:
  reload(widgets)
  reload(utils)
  reload(ui)

from ui import maya_main_window 
from PySide.QtGui import *
from PySide.QtCore import *
from maya import mel
import pymel.core as pm
import maya.cmds as mc
import json

'''
Implements a CUI Viewer tab
'''
class CUILayoutWidget(QWidget):
  def __init__(self):
    super(CUILayoutWidget, self).__init__()
    self.controls = {}
    self.w = 0
    self.h = 0
    self.characterName = ""
    self.timer = self.startTimer(500) # set timer for control updates (every .5 sec)
    self.setFocusPolicy(Qt.StrongFocus) # receive focus from both keyboard and mouse
    self.symbols = { # the vision scope for compiling the custom commands
      "pm": pm, # pymel.core as pm
      "mc": mc, # maya.cmds as mc
      "cui": self # this instance of CUILayoutWidget
    }
    self.selectionRect = None # rubber band for drag selection
    self.dragging = False # drag selection state
    self.dragOrigin = None # the start position of drag selection
    # Maya script job to update the states of selectors
    self.selectionChangedSJ = pm.scriptJob(event=["SelectionChanged", self.updateSelection])

  '''
  Without this stylesheets will not work (Qt peculiarity)
  '''
  def paintEvent(self, event):
    opt = QStyleOption()
    opt.initFrom(self)
    p = QPainter(self)
    self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

  '''
  Called when the timer expires, updates the controls states
  '''
  def timerEvent(self, event):
    if not (self.hasFocus() or self.childHasFocus()): # if not focused
      self.updateControls() # update the controls

  '''
  Cleaning up before closing
  '''
  def closeEvent(self, event):
    self.killTimer(self.timer) # kill the update timer
    pm.scriptJob(kill=self.selectionChangedSJ) # kill the script job
    event.accept() # go ahead with the event

  '''
  Returns True if some of the controls has focus
  Otherwise returns False
  '''
  def childHasFocus(self):
    for control in self.controls.values():
      if control.widget.hasFocus():
        return True
    return False

  '''
  Called when the Maya selection is updated
  '''
  def updateSelection(self):
    selection = set(map(str, pm.ls(sl=1))) # the selected objects and convert to set for convenience
    for control in self.controls.values(): # iterate over all controls
      if isinstance(control, widgets.Selector): # if the control is a selector
        if set(control.target_objs) <= selection: # if its target objects are selected
          control.is_selected = True # set selected
        else:
          control.is_selected = False # otherwise set not selected
        control.redraw() # redraw to update the appearance (selected controls are circled)

  '''
  Returns all the active selectors
  '''
  def activeSelectors(self):
    active_selectors = []
    for control in self.controls.values():
      if isinstance(control, widgets.Selector) and control.is_selected:
        active_selectors.append(control)
    return active_selectors

  '''
  Used for drag selection
  '''
  def activateSelectorsAsGroup(self, selectors):
    if not QApplication.keyboardModifiers() == Qt.ShiftModifier: # if shift is not pressed
      for selector in self.activeSelectors():
        selector.action(drag=True) # deselect all active selectors

    for selector in selectors:
      selector.action(drag=1) # activate the given selectors

  def addControl(self, control):
    self.controls[control.cid] = control

  def updateBackground(self):
    if self.background is None: # abort if has not BG
      return

    imagePath = utils.charactersDir()+self.background # format the BG file path
    # set the BG using a stylesheet
    self.setStyleSheet("CUILayoutWidget {background-image: url(%s); background-repeat: none;}" % imagePath)

  '''
  Update the controls to match the current attribute states
  '''
  def updateControls(self):
    for control in self.controls.values():
      control.updateControl()

  '''
  Show the control with specified cid
  If ~obj~ is True shows the assigned objects as well (for selectors)
  '''
  def showByCid(self, cid, obj=False):
    self.controls[cid].show()
    
    if obj and isinstance(self.controls[cid], widgets.Selector):
      for obj in self.controls[cid].target_objs:
        pm.setAttr("{}.visibility".format(obj), True)

  '''
  Hide the control with specified cid
  If ~obj~ is True hides the assigned objects as well (for selectors)
  '''
  def hideByCid(self, cid, obj=False):
    self.controls[cid].hide()

    if obj and isinstance(self.controls[cid], widgets.Selector):
      for obj in self.controls[cid].target_objs:
        pm.setAttr("{}.visibility".format(obj), False)

  '''
  Show all objects tagged by ~tag~
  If ~obj~ is True shows the assigned objects as well (for selectors)
  '''
  def showByTag(self, tag, obj=False):
    for control in self.controls.values():
      if tag in control.tags:
        control.show()
        
        if obj and isinstance(control, widgets.Selector):
          for obj in control.target_objs:
            pm.setAttr("{}.visibility".format(obj), True)

  '''
  Hide all objects tagged by ~tag~
  If ~obj~ is True hides the assigned objects as well (for selectors)
  '''
  def hideByTag(self, tag, obj=False):
    for control in self.controls.values():
        if tag in control.tags:
          control.hide()

          if obj and isinstance(control, widgets.Selector):
            for obj in control.target_objs:
              pm.setAttr("{}.visibility".format(obj), False)

  '''
  Activate all the selectors tagged by ~tag~
  '''
  def selectByTag(self, tag):
    pm.select([])

    for control in self.controls.values():
      if isinstance(control, widgets.Selector) and tag in control.tags:
        pm.select(control.target_objs, add=1)

  '''
  Init drag selection
  '''
  def mousePressEvent(self, event):
    self.selectionRect = QRubberBand(QRubberBand.Rectangle, self) # create the visible rectangle
    self.dragOrigin = event.pos() # set the drag origin
    self.selectionRect.setGeometry(QRect(self.dragOrigin, QSize())) # set up the selection rectangle location
    self.selectionRect.show() # and show it
    
  '''
  Process drag selection
  '''
  def mouseMoveEvent(self, event):
    if self.selectionRect: # if not dragging a control
      geo = QRect(*utils.calculateCorners(self.dragOrigin, event.pos())) # calculate the rectangle corners
      self.selectionRect.setGeometry(geo) # set the rectangle position and size

  '''
  Finalize drag selection
  '''
  def mouseReleaseEvent(self, event):
    if self.selectionRect: # if not dragging a control
      area = QRect(*utils.calculateCorners(self.dragOrigin, event.pos())) # calculate the affected area

      controls_in_area = [] # container for all affected selectors
      for control in self.controls.values():
        if isinstance(control, widgets.Selector) and area.contains(control.pos):
          controls_in_area.append(control) # if control is a selector and located inside the affected area

      # clear the selection if clicked or dragged on blank space without shift pressed
      if not controls_in_area and not QApplication.keyboardModifiers() == Qt.ShiftModifier:
        pm.select([])
      else: # otherwise activate the affected selectors
        self.activateSelectorsAsGroup(controls_in_area)
      self.selectionRect.deleteLater() # destroy the selection rectangle
      self.selectionRect = None
      event.accept() # go ahead with the event

'''
Implements the main window of CUI Viewer
'''
class CUIViewer(QDialog):
  def __init__(self, tab=None):
    super(CUIViewer, self).__init__(maya_main_window())
    self.setWindowFlags(Qt.Window)
    self.setAttribute(Qt.WA_DeleteOnClose)
    self.setWindowTitle("Character UI Viewer")
    self.setObjectName("CUIViewerMain")
    self.setFixedSize(400, 300)
    self.verticalLayout = QVBoxLayout(self)
    self.tabWidget = QTabWidget(self)
    self.tabWidget.setDocumentMode(True) # do not show the tab widget overlay
    self.verticalLayout.addWidget(self.tabWidget)
    self.verticalLayout.setContentsMargins(1, 1, 1, 1) # set minimal margins from window borders

    self.tabWidget.currentChanged.connect(self.matchTabSize)

    if tab:
      self.tabWidget.addTab(tab, tab.characterName)
    else:
      self.loadUi() # init the new tab

  '''
  Resize the window according to the tab size
  '''
  def matchTabSize(self):
    if self.tabWidget.currentWidget():
      w = self.tabWidget.currentWidget().w + 10
      h = self.tabWidget.currentWidget().h + 20
      self.setFixedSize(w, h)

  '''
  Clean up before exit
  '''
  def closeEvent(self, event):
    while self.tabWidget.currentWidget(): # destroy all tabs
      tab = self.tabWidget.currentWidget()
      tabId = self.tabWidget.currentIndex()
      self.tabWidget.removeTab(tabId)
      tab.close()
      tab.deleteLater()

  '''
  Process the hotkeys inside the CUI Viewer window
  '''
  def keyPressEvent(self, event):
    if event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier:
      # Ctrl+Q => new tab
      self.loadUi()

    elif event.key() == Qt.Key_W and event.modifiers() == Qt.ControlModifier:
      # Ctrl+W => previous tab
      self.tabWidget.setCurrentIndex(self.tabWidget.currentIndex() - 1)

    elif event.key() == Qt.Key_E and event.modifiers() == Qt.ControlModifier:
      # Ctrl+E => next tab
      self.tabWidget.setCurrentIndex(self.tabWidget.currentIndex() + 1)

    elif event.key() == Qt.Key_R and event.modifiers() == Qt.ControlModifier:
      # Ctrl+R => close the current tab
      tab = self.tabWidget.currentIndex()
      self.tabWidget.removeTab(tab)
      tab.close()
      tab.deleteLater()

    elif event.key() == Qt.Key_Space and event.modifiers() == Qt.ControlModifier:
      # Ctrl+Space => tear off current tab
      tab = self.tabWidget.currentWidget()
      tab_id = self.tabWidget.currentIndex()
      self.tabWidget.removeTab(tab_id)
      from . import viewer
      viewer(tab)

    elif event.key() == Qt.Key_Q:
      # Q => switch Maya tool to Selection Tool
      mel.eval("SelectToolOptionsMarkingMenu")

    elif event.key() == Qt.Key_W:
      # W => switch Maya tool to Move Tool
      mel.eval("TranslateToolWithSnapMarkingMenu")

    elif event.key() == Qt.Key_E:
      # E => switch Maya tool to Rotate Tool
      mel.eval("RotateToolWithSnapMarkingMenu")

    elif event.key() == Qt.Key_R:
      # R => switch Maya tool to Scale Tool
      mel.eval("ScaleToolWithSnapMarkingMenu")

  '''
  Create a new tab from file
  '''
  def loadUi(self):
    # request the file name from user
    result = QFileDialog.getOpenFileName(self, "Open", utils.charactersDir(), "CUI files (*.cui)")
    if result[1]:
      fileName = result[0]
    else: # abort if could not get the filename
      return

    with open(fileName, "r") as inputFile:
      jsonData = json.load(inputFile) # parse the file

    tab = CUILayoutWidget() # create a new tab instance

    # load settings from file
    tab.w = jsonData["window_width"]
    tab.h = jsonData["window_height"]
    tab.background = jsonData["background_image"]
    tab.updateBackground() # redraw the BG
    tab.characterName = jsonData["name"]

    for ctrl in jsonData["controls"]: # load the control from file
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

      elif controlType == "float_field":
        floatField = widgets.FloatField(tab)
        floatField.deserialize(control)
        floatField.setup(client=True)
        tab.addControl(floatField)

    self.tabWidget.addTab(tab, tab.characterName) # add the tab
    tab.updateSelection() # set up the selectors states