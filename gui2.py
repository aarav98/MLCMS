import wx
import sys
import system as model
import json


def initialize_system(file_name):
    """
    Reads the scenario file and initializes the system with pro
    :param file_name:
    :return:
    """
    with open(file_name) as scenario:
        data = json.load(scenario)
    rows = data['rows']
    cols = data['cols']
    system = model.System(cols, rows)
    for col, row in data['pedestrians']:
        system.add_pedestrian((col, row))

    for col, row in data['obstacles']:
        system.add_obstacle((col, row))

    col, row = data['target']
    target = system.add_target((col, row))

    model.evaluate_cell_distance(system, target)
    return system


class Frame(wx.Frame):
    def __init__(self, parent, system):
        wx.Frame.__init__(self, parent)
        self.system = system
        self.cell_size = 10
        self.InitUI()

    def InitUI(self):
        # self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetTitle("Cellular Automaton")
        self.SetSize((self.system.cols + 10) * self.cell_size, (self.system.rows + 10) * self.cell_size)
        self.canvas_panel = Canvas(self)
        self.button_panel = ButtonPanel(self)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.canvas_panel, 1, wx.EXPAND | wx.ALL, 0)
        sizer_1.Add(self.button_panel, 0, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(sizer_1)
        self.Layout()
        # self.Centre()


class Canvas(wx.Panel):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name="Canvas"):
        super(Canvas, self).__init__(parent, id, pos, size, style, name)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.parent = parent

    def OnSize(self, event):
        # print("OnSize" + str(event))
        # self.SetClientRect(event.GetRect()) # no need
        self.Refresh()  # MUST have this, else the rectangle gets rendered corruptly when resizing the window!
        event.Skip()  # seems to reduce the ammount of OnSize and OnPaint events generated when resizing the window

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        for row in self.parent.system.grid:
            for cell in row:
                # dc.SetPen(wx.Pen(cell.state))
                dc.SetBrush(wx.Brush(cell.state))
                dc.DrawRectangle(cell.row * self.parent.cell_size, cell.col * self.parent.cell_size,
                                 self.parent.cell_size, self.parent.cell_size)


class ButtonPanel(wx.Panel):
    def __init__(self, parent: Frame, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name="ButtonPanel"):
        super(ButtonPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetSize(10*parent.cell_size, parent.system.rows*parent.cell_size)
        self.button_start = wx.Button(self, -1, "Start")
        self.button_stop = wx.Button(self, -1, "Stop")
        self.button_step = wx.Button(self, -1, "Step")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.button_start, 1, 0)
        sizer_1.Add(self.button_stop, 1, wx.EXPAND | wx.ALL, 0)
        sizer_1.Add(self.button_step, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(sizer_1)
        self.Layout()


def main():
    # file_name = input("Please enter a scenario file name: ")
    app = wx.App()
    # gui = Frame(parent= None, system=initialize_system('Scenarios/' + file_name))
    gui = Frame(parent=None, system=initialize_system('Scenarios/scenario_task2.json'))
    gui.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
