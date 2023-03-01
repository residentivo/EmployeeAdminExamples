from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, pyqtSignal
import requests

class CustomEvent(QObject):
    signal = pyqtSignal()


class SelectEmployee(QObject):
    signal = pyqtSignal(object)


class SelectRoles(QObject):
    signal = pyqtSignal(object)


class MainApp:
    appFrame = None  # main frame of aplication
    app = None  # pyqt application in case needed in future
    services = None

    # create instances
    def __init__(self):
        self.services = Services()
        self.app = QApplication([])
        self.main_window = QWidget()
        self.main_window.setWindowTitle("PureMvc Employee Admin")
        self.appFrame = AppFrame(QVBoxLayout(self.main_window))

        # events
        self.appFrame.userList.EVT_DELETE.signal.connect(self.deleteEmployee)
        self.appFrame.userForm.EVT_SAVE.signal.connect(self.saveEmployee)

    def getList(self):
        if self.services != None:
            self.appFrame.userList.reciveEmployees(self.services.getEmployees())

    def saveEmployee(self, employee):
        if employee["id"] == 0:
            self.services.postEmployee(employee)
        else:
            self.services.patchEmployee(employee)
        self.getList()

    def deleteEmployee(self, employee):
        if employee != None:
            self.services.delEmployees(employee)
        self.getList()

    def MainLoop(self):
        self.getList()
        self.appFrame.rolePanel.reciveRoles(self.services.getRoles())
        self.appFrame.userForm.reciveDepartments(self.services.getDepart())
        self.main_window.show()
        self.app.exec_()


class AppFrame:
    mvcfacade = None  # reference for appinstance
    panel = None  # main painel

    # sections of the app
    userForm = None
    userList = None
    rolePanel = None

    # layout parts
    layout = None
    bottom_layout = None

    # main events
    EVT_SAVE = SelectEmployee()
    EVT_DELETE = SelectEmployee()

    def __init__(self, layout: QLayout):
        self.layout = layout
        self.userList = UserList(self)

        # create bottom part
        bottom = QWidget()
        self.bottom_layout = QGridLayout(bottom)
        self.layout.addWidget(bottom)

        self.rolePanel = RolePanel(self)

        self.userForm = UserForm(self)

        # evnets
        self.userList.EVT_USER_SELECTED.signal.connect(self.rolePanel.reciveEmployee)
        self.userList.EVT_USER_SELECTED.signal.connect(self.userForm.reciveEmployee)
        self.rolePanel.EVT_SYNC_ROLE.signal.connect(self.userForm.syncRoles)


class RolePanel:
    # variables
    SystemRoles = None
    selectedRole = None
    EmployeeRoles = []

    # components
    roleList: QListWidget = None
    roleCombo: QComboBox = None
    addBtn: QPushButton = None
    remBtn: QPushButton = None

    # Gardar referencia do app
    appFrame = None

    # # events
    # EVT_ADD_ROLE = CustomEvent()
    # EVT_REMOVE_ROLE = CustomEvent()
    EVT_SYNC_ROLE = SelectRoles()

    def createRoleListButtons(self) -> QWidget:
        roleListbuttons = QWidget()
        roleListbuttons_layout = QHBoxLayout(roleListbuttons)
        self.roleCombo = QComboBox()
        self.roleCombo.addItem("  ---Loading---  ")
        roleListbuttons_layout.addWidget(self.roleCombo)
        self.addBtn = QPushButton("Add")
        roleListbuttons_layout.addWidget(self.addBtn)
        self.remBtn = QPushButton("Remove")
        roleListbuttons_layout.addWidget(self.remBtn)
        return roleListbuttons

    def createRoleList(self) -> QWidget:
        panelroleList = QWidget()
        roleList_layout = QHBoxLayout(panelroleList)
        self.roleList = QListWidget()
        roleList_layout.addWidget(self.roleList)
        return panelroleList

    def __init__(self, parent: AppFrame) -> None:
        self.appFrame = parent

        roleform = self.createRoleList()
        self.appFrame.bottom_layout.addWidget(roleform, 0, 1)

        roleformbuttons = self.createRoleListButtons()
        self.appFrame.bottom_layout.addWidget(roleformbuttons, 1, 1)

        # envet
        self.roleList.itemSelectionChanged.connect(self.roleList_itemSelectionChanged)
        self.roleCombo.currentIndexChanged.connect(self.roleCombo_currentIndexChanged)
        self.addBtn.clicked.connect(self.addBtn_clicked)
        self.remBtn.clicked.connect(self.remBtn_clicked)

    def addBtn_clicked(self):
        if len(self.roleList.selectedItems()) == 0:
            item = QListWidgetItem(self.roleCombo.currentText(), self.roleList)
            self.roleList.setCurrentItem(item)
            self.syncList()

    def syncList(self):
        self.EmployeeRoles = []
        for i in range(self.roleList.count()):
            parsedItem = list(
                filter(
                    lambda person: person["name"] == self.roleList.item(i).text(),
                    self.SystemRoles,
                )
            )
            if len(parsedItem) >= 1:
                self.EmployeeRoles.append(
                    {"id": parsedItem[0]["value"], "name": parsedItem[0]["name"]}
                )
        self.EVT_SYNC_ROLE.signal.emit(self.EmployeeRoles)

    def remBtn_clicked(self):
        if len(self.roleList.selectedItems()) == 1:
            for i in self.roleList.selectedItems():
                self.roleList.takeItem(self.roleList.row(i))
            self.syncList()

    def roleCombo_currentIndexChanged(self):
        for i in range(self.roleList.count()):
            if self.roleList.item(i).text() == self.roleCombo.currentText():
                self.roleList.setCurrentItem(self.roleList.item(i))
                return None
        self.roleList.setCurrentItem(None)

    def roleList_itemSelectionChanged(self):
        self.selectedRole = self.roleList.selectedItems()
        if len(self.selectedRole) == 0:
            return None
        for item in self.selectedRole:
            self.roleCombo.setCurrentText(item.text())

    def reciveRoles(self, list):
        if len(list) > 0:
            self.SystemRoles = list
        self.roleCombo.clear()
        for itemR in self.SystemRoles:
            self.roleCombo.addItem(itemR["name"], itemR["value"])

    # events
    def reciveEmployee(self, employee):
        if employee != None and employee["roles"] != None:
            self.EmployeeRoles = employee["roles"]
        else:
            self.EmployeeRoles = []
        self.roleList.clear()
        for itemR in self.EmployeeRoles:
            QListWidgetItem(itemR["name"], self.roleList)


class UserForm:
    # internal variables
    SystemDeparts = []
    selectedEmployee = None
    mode = None

    # componentes
    usernameInput = None
    firstInput = None
    lastInput = None
    emailInput = None
    passwordInput = None
    confirmInput = None
    departmentCombo = None
    saveBtn = None
    cancelBtn = None

    # Gardar referencia do app
    appFrame = None

   # events
    EVT_SAVE = SelectEmployee()
    EVT_CANCEL = CustomEvent()

    def createUserFormButtons(self) -> QWidget:
        userformbuttons = QWidget()
        userformbuttons_layout = QHBoxLayout(userformbuttons)
        self.saveBtn = QPushButton("Save")
        userformbuttons_layout.addWidget(self.saveBtn)
        self.cancelBtn = QPushButton("Cancel")
        userformbuttons_layout.addWidget(self.cancelBtn)
        return userformbuttons

    def createUserForm(self) -> QWidget:
        userform = QWidget()
        userform_layout = QHBoxLayout(userform)
        qform = QWidget()
        form = QFormLayout()
        qform.setLayout(form)
        name_label = QLabel("First Name:")
        self.firstInput = QLineEdit()
        form.addRow(name_label, self.firstInput)
        lastname_label = QLabel("Last Name:")
        self.lastInput = QLineEdit()
        form.addRow(lastname_label, self.lastInput)
        email_label = QLabel("Email:")
        self.emailInput = QLineEdit()
        form.addRow(email_label, self.emailInput)
        UserName_label = QLabel("User Name:")
        self.usernameInput = QLineEdit()
        form.addRow(UserName_label, self.usernameInput)
        Password_label = QLabel("Password:")
        self.passwordInput = QLineEdit()
        form.addRow(Password_label, self.passwordInput)
        ConfirmPass_label = QLabel("Confirm Password:")
        self.confirmInput = QLineEdit()
        form.addRow(ConfirmPass_label, self.confirmInput)
        departament_label = QLabel("Departament:")
        self.departmentCombo = QComboBox()
        self.departmentCombo.addItem(" --Loading-- ")
        form.addRow(departament_label, self.departmentCombo)
        userform_layout.addWidget(qform)
        return userform

    # init layouts
    def __init__(self, parent: AppFrame) -> None:
        self.appFrame = parent

        userform = self.createUserForm()
        self.appFrame.bottom_layout.addWidget(userform, 0, 0)

        userformbuttons = self.createUserFormButtons()
        self.appFrame.bottom_layout.addWidget(userformbuttons, 1, 0)

        # events
        self.saveBtn.clicked.connect(self.saveBtn_clicked)
        self.cancelBtn.clicked.connect(self.cancelBtn_clicked)

    def saveBtn_clicked(self):
        self.selectedEmployee["first"] = self.firstInput.text()
        self.selectedEmployee["last"] = self.lastInput.text()
        # find department in SYSTEM
        parsedItem = list(
            filter(
                lambda person: person["name"] == self.departmentCombo.currentText(),
                self.SystemDeparts,
            )
        )
        if len(parsedItem) >= 1:
            self.selectedEmployee["department"]["name"] = parsedItem[0]["name"]
            self.selectedEmployee["department"]["id"] = parsedItem[0]["value"]

        self.EVT_SAVE.signal.emit(self.selectedEmployee)
        # self.selectedEmployee

    def syncRoles(self, roles):
        self.selectedEmployee["roles"] = roles

    def cancelBtn_clicked(self):
        self.reciveEmployee(None)
        self.EVT_CANCEL.signal.emit()

    def reciveDepartments(self, list=[]):
        if len(list) > 0:
            self.SystemDeparts = list
        self.departmentCombo.clear()
        self.departmentCombo.addItems([item["name"] for item in self.SystemDeparts])

    def reciveEmployee(self, employee):
        if employee == None:
            self.selectedEmployee = {}
            self.selectedEmployee["id"] = 0
            self.selectedEmployee["first"] = ""
            self.selectedEmployee["last"] = ""
            self.selectedEmployee["department"] = {}
            self.selectedEmployee["department"]["name"] = ""
            self.selectedEmployee["department"]["id"] = 0
            self.selectedEmployee["roles"] = {}
        else:
            self.selectedEmployee = employee

        self.departmentCombo.setCurrentText(self.selectedEmployee["department"]["name"])
        self.firstInput.setText(self.selectedEmployee["first"])
        self.lastInput.setText(self.selectedEmployee["last"])


class UserList:
    # variaveis do sistema
    employees = None
    selectedUser = None

    # Componentes
    userGrid: QTableWidget = None
    newBtn: QPushButton = None
    delBtn: QPushButton = None

    # Gardar referencia do app
    appFrame = None
    columns = ["Department", "Email", "First Name", "Last Name", "Password", "Username"]

    # events
    EVT_DELETE = SelectEmployee()
    EVT_NEW = CustomEvent()
    EVT_USER_SELECTED = SelectEmployee()

    def createUserListButtons(self) -> QWidget:
        UserButtons_panel = QWidget()  # Create the first panel
        UserButtons_panel.setFixedHeight(45)
        UserButtons_panel_layout = QHBoxLayout(UserButtons_panel)
        self.newBtn = QPushButton("New")
        UserButtons_panel_layout.addWidget(self.newBtn)
        self.delBtn = QPushButton("Delete")
        UserButtons_panel_layout.addWidget(self.delBtn)
        return UserButtons_panel

    def createUserList(self) -> QWidget:
        userlist_panel = QWidget()  # Create the first panel
        userlist_panel_layout = QHBoxLayout(userlist_panel)  # define layout
        self.userGrid = QTableWidget()
        self.userGrid.setColumnCount(len(self.columns))
        self.userGrid.setHorizontalHeaderLabels(self.columns)
        userlist_panel_layout.addWidget(self.userGrid)
        return userlist_panel

    def __init__(self, parent: AppFrame) -> None:
        self.appFrame = parent
        userlist_panel = self.createUserList()
        parent.layout.addWidget(userlist_panel)
        Userlistbuttons_panel = self.createUserListButtons()
        parent.layout.addWidget(Userlistbuttons_panel)
        # events internal
        self.userGrid.cellClicked.connect(self.selectItem)
        self.newBtn.clicked.connect(self.newbtn_clicked)
        self.delBtn.clicked.connect(self.delbtn_clicked)

    def selectItem(self):
        selected_items = self.getSelectedItem()
        # emmit event for user was selected
        if selected_items != None:
            self.EVT_USER_SELECTED.signal.emit(self.employees[selected_items])

    def getSelectedItem(self):
        for item in self.userGrid.selectedItems():
            return item.row()
        return None

    def newbtn_clicked(self):
        self.userGrid.clearSelection()
        self.EVT_USER_SELECTED.signal.emit(None)

    def delbtn_clicked(self):
        selected_items = self.getSelectedItem()        
        if selected_items != None:
            self.EVT_DELETE.signal.emit(self.employees[selected_items])
        # procede with delete

    def reciveEmployees(self, list=[]):
        if len(list) > 0:
            self.employees = list
        parsedList = [
            [item["first"], "", item["last"], item["department"]["name"]]
            for item in list
        ]
        self.userGrid.clearContents()
        self.userGrid.setRowCount(len(parsedList))
        for row in range(len(parsedList)):
            for col in range(len(parsedList[row])):
                self.userGrid.setItem(row, col, QTableWidgetItem(parsedList[row][col]))


class Services:
    basicUrl = "http://192.168.15.11:8090/"

    def getRoles(self):
        return requests.get(self.basicUrl + "roles").json()

    def getDepart(self):
        return requests.get(self.basicUrl + "departments").json()

    def getEmployees(self):
        return requests.get(self.basicUrl + "employees").json()

    def patchEmployee(self, employee):
        requests.patch(url=self.basicUrl + "employees/" + str(employee["id"]), json=employee)

    def postEmployee(self, employee):
        requests.post(url=self.basicUrl + "employees", json=employee)

    def delEmployees(self, employee):
        requests.delete(self.basicUrl + "employees/" + str(employee["id"]))


if __name__ == "__main__":
    # s = Services()
    # a = Services().getDepart()[0]['value']
    # print(a)
    qapp = MainApp()  # wxApp = components.WxApp()#requisito do wx
    qapp.MainLoop()  # wxApp.MainLoop()#requisito do wx
