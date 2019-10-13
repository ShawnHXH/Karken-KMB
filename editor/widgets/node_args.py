from PyQt5.QtWidgets import QTableView, QHeaderView, QCheckBox
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import Qt

from cfg import DEBUG
from lib import DataBase4Args
from editor.component.args_model import ArgsPreviewModel, ArgsEditableModel
from editor.component.args_model_item import ArgComboBox


class KMBNodesArgsMenu(QTableView):

    def __init__(self,
                 menu_delegate,
                 parent=None):
        super().__init__(parent)

        self.menu = menu_delegate
        self.head = QHeaderView(Qt.Horizontal, self)
        # link to database
        self.db_link = DataBase4Args()
        self.null_model = QStandardItemModel()
        # for collection
        self.edit_model = {}

        # set the horizontal head
        self.head.setStretchLastSection(True)
        self.setHorizontalHeader(self.head)
        # hide the vertical head
        self.verticalHeader().setHidden(True)
        # set width
        self.setMinimumWidth(320)

    def set_preview_args(self, node_name):
        id_string, inherit = self.db_link.get_args_id(node_name)
        preview_model = ArgsPreviewModel(self.db_link, id_string, inherit)
        preview_model.get_args()
        self.setModel(preview_model)

    def set_editing_args(self, node_id):
        if node_id == 0:
            # set an empty model.
            self.setModel(self.null_model)
            return
        # load args model that already exists.
        try:
            model = self.edit_model[node_id]
            self.setModel(model)
            if DEBUG:
                print(f"Get and set exist model => {model}")
            # try to set combo box args
            if model.combo_args:
                self.add_combobox_cell(model)
            # try to set check button args
            if model.check_args:
                self.add_checkbox_cell(model)
            model.itemChanged.connect(self.modify_item)
        except KeyError:
            self.setModel(self.null_model)

    def add_combobox_cell(self, model):
        # clean the widgets id, every time click node,
        # it will generate new ids.
        model.combo_widgets_id.clear()
        for row, col, arg_init, args_list, arg_set in model.combo_args:
            index = self.model().index(row, col)
            combo = ArgComboBox(args_list, arg_init)
            # set current new value
            if arg_set != "placeholder":
                combo.setCurrentText(arg_set)
            model.combo_widgets_id.append(id(combo))
            self.setIndexWidget(index, combo)
            combo.currentTextChanged.connect(lambda v: self.modify_args(v, combo, model))

    def add_checkbox_cell(self, model):
        model.check_widgets_id.clear()
        for row, col, arg_init in model.check_args:
            index = self.model().index(row, col)
            check = QCheckBox(arg_init)
            # initialize the checkbox
            if arg_init == "True":
                check.setChecked(True)
            else:
                check.setChecked(False)
            model.check_widgets_id.append(id(check))
            self.setIndexWidget(index, check)
            check.clicked.connect(lambda s: self.modify_state(s, model))

    def modify_item(self, item):
        item.has_changed()
        item.setText(item.text())
        if DEBUG:
            print(f"Argument item has been changed => {item} with '{item.text()}'")

    def modify_args(self, value, combo, model):
        # set the model's placeholder in combo_args
        if model.combo_widgets_id.__contains__(id(combo.sender())):
            idx = model.combo_widgets_id.index(id(combo.sender()))
            model.reassign_value(idx, value)
        else:
            model.reassign_value(-1, value)
        if DEBUG:
            print(f"Argument combobox value changed to => {value}")

    def modify_state(self, state, model):
        idx = model.check_widgets_id.index(id(self.sender()))
        model.reassign_state(idx, str(state))
        self.sender().setText(str(state))
        if DEBUG:
            print(f"Argument checkbox value changed to => {state}")

    def commit_node(self, node_name, node_id):
        # after adding node in canvas
        # first time make new model.
        id_string, inherit = self.db_link.get_args_id(node_name)
        model = ArgsEditableModel(self.db_link, id_string, inherit)
        model.name = node_name
        model.get_args()
        # then store it but don't display it.
        self.edit_model[node_id] = model
        if DEBUG:
            print(f"Node has been committed => id:{node_id}, name: {node_name}")

    def delete_node(self, node_id):
        self.edit_model.__delitem__(node_id)
        self.setModel(self.null_model)
        if DEBUG:
            print(f"Node has been removed => id:{node_id}")
