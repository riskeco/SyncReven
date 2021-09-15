
import idc
import reven2
import idaapi

from PyQt5 import QtCore, QtGui, QtWidgets


class TransitionsPanel(idaapi.PluginForm):

    def __init__(self, *args):

        super().__init__(*args)

        self._server = None


    def OnCreate(self, form):

        parent = self.FormToPyQtWidget(form)

        # Create layout

        layout = QtWidgets.QGridLayout()

        parent.setLayout(layout)

        # Connection properties

        self._param_server = QtWidgets.QLineEdit()
        self._param_server.setText('192.168.1.1')
        layout.addWidget(self._param_server, 0, 0)

        self._param_port = QtWidgets.QLineEdit()
        self._param_port.setText('12345')
        layout.addWidget(self._param_port, 0, 1)

        self._button = QtWidgets.QPushButton('Connect')
        self._button.clicked.connect(self._handle_connection)
        layout.addWidget(self._button, 0, 2)

        # Existing transitions

        self._rows = QtWidgets.QTableWidget()

        column_names = [ 'Transitions' ]

        self._rows.setColumnCount(len(column_names))
        self._rows.setHorizontalHeaderLabels(column_names)

        self._rows.setRowCount(0)
        self._rows.doubleClicked.connect(self.JumpSearch)

        layout.addWidget(self._rows, 1, 0, 1, 3)


    def _handle_connection(self):

        if self._server:

            self._server = None
            self._button.setText('Connect')

        else:

            self._server = reven2.RevenServer(self._param_server.text(), int(self._param_port.text()))

            print(self._server)

            if self._server:
                self._button.setText('Disconnect')


    def JumpSearch(self, item):

        tt = self._rows.item(item.row(), 0)

        tid = int(tt.text())

        idaapi.msg('Go to transition #%u\n' % tid)

        trans = self._server.trace.transition(tid)

        ret = self._server.sessions.publish_transition(trans)
        assert(ret)


    def update(self, new_ea):

        if self._server:

            #self._rows.clear()
            self._rows.setRowCount(0)

            found = self._server.trace.search.pc(new_ea)

            count = 0

            for f in found:

                index = self._rows.rowCount()
                self._rows.setRowCount(index + 1)

                item = QtWidgets.QTableWidgetItem('%u' % f._id)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)

                self._rows.setItem(index, 0, item)
                self._rows.update()

                count += 1

                if count > 20:
                    break

            if count == 0:
                idaapi.msg('No transition for 0x%x\n' % new_ea)


class NavTracker(idaapi.UI_Hooks):

    def __init__(self, *args):

        super().__init__(*args)

        self._form = None


    def screen_ea_changed(self, new_ea, old_ea):

        if not(self._form):
            self._form = TransitionsPanel()
            self._form.Show('Transitions')

        self._form.update(new_ea)

        return 0


class SyncWithReven(idaapi.plugin_t):

    flags = idaapi.PLUGIN_KEEP
    comment = 'Sync the Axion window with the current analyzed address.'

    wanted_name = 'syncreven'
    wanted_hotkey = ''
    help = 'Save the script into the plugin directory and move the analysis caret.'

    def init(self):

        idaapi.msg('Starting %s\n' % self.wanted_name)

        self._tracker = NavTracker()
        self._tracker.hook()

        return idaapi.PLUGIN_KEEP


    def run(self, arg):
        #pass
        idaapi.msg('Running %s\n' % self.wanted_name)


    def term(self):

        idaapi.msg('Terminating %s\n' % self.wanted_name)

        self._tracker.unhook()


def PLUGIN_ENTRY():
    return SyncWithReven()
