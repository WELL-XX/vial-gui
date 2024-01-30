# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QSizePolicy, QGridLayout, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QScrollArea, QFrame, QToolButton

from protocol.constants import VIAL_PROTOCOL_DYNAMIC
from util import make_scrollable, tr
from widgets.key_widget import KeyWidget
from protocol.key_override import KeyOverrideOptions, KeyOverrideEntry
from vial_device import VialKeyboard
from editor.basic_editor import BasicEditor
from widgets.checkbox_no_padding import CheckBoxNoPadding
from widgets.tab_widget_keycodes import TabWidgetWithKeycodes


class ModsUI(QWidget):

    changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.mods = [
            CheckBoxNoPadding("LCtrl"),
            CheckBoxNoPadding("LShift"),
            CheckBoxNoPadding("LAlt"),
            CheckBoxNoPadding("LGui"),
            CheckBoxNoPadding("RCtrl"),
            CheckBoxNoPadding("RShift"),
            CheckBoxNoPadding("RAlt"),
            CheckBoxNoPadding("RGui"),
        ]

        for w in self.mods:
            w.stateChanged.connect(self.on_change)

        container = QGridLayout()
        container.addWidget(self.mods[0], 0, 0)
        container.addWidget(self.mods[4], 1, 0)

        container.addWidget(self.mods[1], 0, 1)
        container.addWidget(self.mods[5], 1, 1)

        container.addWidget(self.mods[2], 0, 2)
        container.addWidget(self.mods[6], 1, 2)

        container.addWidget(self.mods[3], 0, 3)
        container.addWidget(self.mods[7], 1, 3)

        self.setLayout(container)

    def load(self, data):
        for x, chk in enumerate(self.mods):
            chk.setChecked(bool(data & (1 << x)))

    def save(self):
        out = 0
        for x, chk in enumerate(self.mods):
            out |= int(chk.isChecked()) << x
        return out

    def on_change(self):
        self.changed.emit()


class OptionsUI(QWidget):

    changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        container = QVBoxLayout()

        self.opt_activation_trigger_down = CheckBoxNoPadding("在触发按键按下时激活") # Activate when the trigger key is pressed down
        self.opt_activation_required_mod_down = CheckBoxNoPadding("在触发修饰键按下时激活") # Activate when a necessary modifier is pressed down
        self.opt_activation_negative_mod_up = CheckBoxNoPadding("在失效修饰键抬起时激活") # Activate when a negative modifier is released
        self.opt_one_mod = CheckBoxNoPadding("任意修饰键按下时激活") # Activate on one modifier
        self.opt_no_reregister_trigger = CheckBoxNoPadding("仅当其他按键按下时失效") # Don't deactivate when another key is pressed down
        self.opt_no_unregister_on_other_key_down = CheckBoxNoPadding(
            "键值覆盖失效后不再触发") #Don't register the trigger key again after the override is deactivated

        for w in [self.opt_activation_trigger_down, self.opt_activation_required_mod_down,
                  self.opt_activation_negative_mod_up, self.opt_one_mod, self.opt_no_reregister_trigger,
                  self.opt_no_unregister_on_other_key_down]:
            w.stateChanged.connect(self.on_change)
            container.addWidget(w)

        self.setLayout(container)

    def on_change(self):
        self.changed.emit()

    def load(self, opt: KeyOverrideOptions):
        self.opt_activation_trigger_down.setChecked(opt.activation_trigger_down)
        self.opt_activation_required_mod_down.setChecked(opt.activation_required_mod_down)
        self.opt_activation_negative_mod_up.setChecked(opt.activation_negative_mod_up)
        self.opt_one_mod.setChecked(opt.one_mod)
        self.opt_no_reregister_trigger.setChecked(opt.no_reregister_trigger)
        self.opt_no_unregister_on_other_key_down.setChecked(opt.no_unregister_on_other_key_down)

    def save(self) -> KeyOverrideOptions:
        opts = KeyOverrideOptions()
        opts.activation_trigger_down = self.opt_activation_trigger_down.isChecked()
        opts.activation_required_mod_down = self.opt_activation_required_mod_down.isChecked()
        opts.activation_negative_mod_up = self.opt_activation_negative_mod_up.isChecked()
        opts.one_mod = self.opt_one_mod.isChecked()
        opts.no_reregister_trigger = self.opt_no_reregister_trigger.isChecked()
        opts.no_unregister_on_other_key_down = self.opt_no_unregister_on_other_key_down.isChecked()
        return opts


class LayersUI(QWidget):

    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        container = QGridLayout()
        buttons = QHBoxLayout()
        self.layer_chks = [CheckBoxNoPadding(str(x)) for x in range(16)]
        for w in self.layer_chks:
            w.stateChanged.connect(self.on_change)
        btn_all_layers = QToolButton()
        btn_all_layers.setText(tr("KeyOverride", "启用全部"))  # Enable all
        btn_all_layers.setToolButtonStyle(Qt.ToolButtonTextOnly)
        btn_no_layers = QToolButton()
        btn_no_layers.setText(tr("KeyOverride", "禁用全部")) # Disable all
        btn_no_layers.setToolButtonStyle(Qt.ToolButtonTextOnly)
        btn_all_layers.clicked.connect(self.on_enable_all_layers)
        btn_no_layers.clicked.connect(self.on_disable_all_layers)

        for x in range(8):
            container.addWidget(self.layer_chks[x], 0, x)
            container.addWidget(self.layer_chks[x + 8], 1, x)

        buttons.addWidget(btn_all_layers)
        buttons.addWidget(btn_no_layers)
        buttons.addStretch()
        container.addLayout(buttons, 2, 0, 1, -1)

        self.setLayout(container)

    def load(self, data):
        for x, w in enumerate(self.layer_chks):
            w.setChecked(bool(data & (1 << x)))

    def save(self):
        out = 0
        for x, w in enumerate(self.layer_chks):
            out |= int(w.isChecked()) << x
        return out

    def on_change(self):
        self.changed.emit()

    def on_enable_all_layers(self):
        for x, w in enumerate(self.layer_chks):
            w.setChecked(True)

    def on_disable_all_layers(self):
        for x, w in enumerate(self.layer_chks):
            w.setChecked(False)


class KeyOverrideEntryUI(QObject):

    changed = pyqtSignal()

    def __init__(self, idx):
        super().__init__()

        self.enable_chk = QCheckBox()
        self.layers = LayersUI()
        self.trigger_key = KeyWidget()
        self.trigger_mods = ModsUI()
        self.negative_mods = ModsUI()
        self.suppressed_mods = ModsUI()
        self.key_replacement = KeyWidget()
        self.options = OptionsUI()

        self.widgets = [self.enable_chk]
        self.enable_chk.stateChanged.connect(self.on_change)
        for w in [self.layers, self.options, self.trigger_key, self.trigger_mods, self.negative_mods,
                  self.suppressed_mods, self.key_replacement]:
            w.changed.connect(self.on_change)
            self.widgets.append(w)

        self.idx = idx
        self.container = QGridLayout()
        self.populate_container()

        w = QWidget()
        w.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        w.setLayout(self.container)
        l = QVBoxLayout()
        l.addWidget(w)
        l.setAlignment(w, QtCore.Qt.AlignHCenter)
        self.w2 = make_scrollable(l)

    def populate_container(self):
        self.container.addWidget(QLabel("启用功能"), 0, 0) # Enable
        self.container.addWidget(self.enable_chk, 0, 1)

        self.container.addWidget(QLabel("在指定层上启用"), 1, 0) # Enable on layers
        self.container.addWidget(self.layers, 1, 1)

        self.container.addWidget(QLabel("触发按键"), 2, 0) # Trigger
        self.container.addWidget(self.trigger_key, 2, 1)

        self.container.addWidget(QLabel("触发修饰键"), 3, 0) # Trigger mods
        self.container.addWidget(self.trigger_mods, 3, 1)

        self.container.addWidget(QLabel("失效修饰键"), 4, 0) # Negative mods
        self.container.addWidget(self.negative_mods, 4, 1)

        self.container.addWidget(QLabel("禁用修饰键"), 5, 0) # Suppressed mods
        self.container.addWidget(self.suppressed_mods, 5, 1)

        self.container.addWidget(QLabel("输出按键"), 6, 0) # Replacement
        self.container.addWidget(self.key_replacement, 6, 1)

        self.container.addWidget(QLabel("选项"), 7, 0) # Options
        self.container.addWidget(self.options, 7, 1)

    def widget(self):
        return self.w2

    def load(self, ko):
        for w in self.widgets:
            w.blockSignals(True)

        self.enable_chk.setChecked(ko.options.enabled)
        self.trigger_key.set_keycode(ko.trigger)
        self.key_replacement.set_keycode(ko.replacement)
        self.layers.load(ko.layers)
        self.trigger_mods.load(ko.trigger_mods)
        self.negative_mods.load(ko.negative_mod_mask)
        self.suppressed_mods.load(ko.suppressed_mods)
        self.options.load(ko.options)

        for w in self.widgets:
            w.blockSignals(False)

    def save(self):
        ko = KeyOverrideEntry()
        ko.options = self.options.save()
        ko.options.enabled = self.enable_chk.isChecked()
        ko.trigger = self.trigger_key.keycode
        ko.replacement = self.key_replacement.keycode
        ko.layers = self.layers.save()
        ko.trigger_mods = self.trigger_mods.save()
        ko.negative_mod_mask = self.negative_mods.save()
        ko.suppressed_mods = self.suppressed_mods.save()
        return ko

    def on_change(self):
        self.changed.emit()


class KeyOverride(BasicEditor):

    def __init__(self):
        super().__init__()
        self.keyboard = None

        self.key_override_entries = []
        self.key_override_entries_available = []
        self.tabs = TabWidgetWithKeycodes()
        for x in range(128):
            entry = KeyOverrideEntryUI(x)
            entry.changed.connect(self.on_change)
            self.key_override_entries_available.append(entry)

        self.addWidget(self.tabs)

    def rebuild_ui(self):
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)
        self.key_override_entries = self.key_override_entries_available[:self.keyboard.key_override_count]
        for x, e in enumerate(self.key_override_entries):
            self.tabs.addTab(e.widget(), str(x + 1))
        for x, e in enumerate(self.key_override_entries):
            e.load(self.keyboard.key_override_get(x))

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.rebuild_ui()

    def valid(self):
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and self.device.keyboard.vial_protocol >= VIAL_PROTOCOL_DYNAMIC
                and self.device.keyboard.key_override_count > 0)

    def on_change(self):
        for x, e in enumerate(self.key_override_entries):
            self.keyboard.key_override_set(x, self.key_override_entries[x].save())
