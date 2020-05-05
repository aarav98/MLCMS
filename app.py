import wx
import model as model
import json
import os

INITIALIZED = False


def initialize_system(file_name):
    """
    Reads the scenario file and initializes the system
    :param file_name:
    :return:
    """

    with open(file_name) as scenario:
        data = json.load(scenario)
    cols = data['cols']
    rows = data['rows']
    system = model.System(cols, rows)

    for col, row in data['pedestrians']:
        system.add_pedestrian_at(coordinates=(col, row))

    if 'speeds' in data:
        system.initialize_speeds(data["speeds"])
    else:
        system.initialize_speeds()

    for col, row in data['obstacles']:
        system.add_obstacle_at(coordinates=(col, row))

    col, row = data['target']
    system.add_target_at(coordinates=(col, row))

    # if obstacle_avoidance == "True":
    #     system.evaluate_cell_utilities()
    #     # system.print_distance_utilities()
    # else:
    #     system.no_obstacle_avoidance()
    # system.init_fmm()
    # system.evaluate_cell_utilities()
    # system.print_utilities()
    # model.no_obstacle_avoidance(system)
    return system


class Frame(wx.Frame):
    def __init__(self, parent, system):
        wx.Frame.__init__(self, parent)
        self.system = system
        self.cell_size = 5
        self.InitUI()

    def InitUI(self):
        self.SetTitle("Cellular Automaton")
        self.SetSize(self.system.cols * self.cell_size, self.system.rows * self.cell_size + 50)
        self.canvas_panel = Canvas(self)
        self.button_panel = ButtonPanel(self)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.canvas_panel, 1, wx.EXPAND | wx.ALL, 0)
        sizer_1.Add(self.button_panel, 0, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(sizer_1)
        self.Layout()
        # self.Centre()


class Canvas(wx.Panel):
    def __init__(self, parent: Frame, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name="Canvas"):
        super(Canvas, self).__init__(parent, id, pos, size, style, name)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.parent = parent

    def OnSize(self, event):
        self.Refresh()  # MUST have this, else the rectangle gets rendered corruptly when resizing the window!
        event.Skip()  # seems to reduce the ammount of OnSize and OnPaint events generated when resizing the window

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        # print(self.parent.system.__str__())
        for col in self.parent.system.grid:
            for cell in col:
                if cell.state == model.EMPTY:
                    continue
                dc.SetBrush(wx.Brush(cell.state))
                dc.DrawRectangle(cell.col * self.parent.cell_size, cell.row * self.parent.cell_size,
                                 self.parent.cell_size, self.parent.cell_size)

    def color_gui_dijikstra(self, event):
        self.parent.button_panel.button_fmm.Disable()
        self.parent.button_panel.button_eucledian_step.Disable()
        if not INITIALIZED:
            self.parent.system.evaluate_cell_utilities()
        self.parent.system.update_sys()
        self.OnPaint(event)

    def color_gui_fmm(self, event):
        self.parent.button_panel.button_dijikstra.Disable()
        self.parent.button_panel.button_eucledian_step.Disable()
        self.parent.system.update_sys_fmm()
        self.OnPaint(event)

    def color_eucledian_step(self, event):
        self.parent.button_panel.button_dijikstra.Disable()
        self.parent.button_panel.button_fmm.Disable()
        if not INITIALIZED:
            self.parent.system.no_obstacle_avoidance()
        self.parent.system.no_obstacle_avoidance_update_sys()
        self.OnPaint(event)


class ButtonPanel(wx.Panel):
    def __init__(self, parent: Frame, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0,
                 name="ButtonPanel"):
        super(ButtonPanel, self).__init__(parent, id, pos, size, style, name)
        # self.SetSize(10*parent.cell_size, parent.system.rows*parent.cell_size)
        self.button_dijikstra = wx.Button(self, -1, "Dijikstra_Step")
        self.button_dijikstra.Bind(wx.EVT_BUTTON, parent.canvas_panel.color_gui_dijikstra)
        self.button_fmm = wx.Button(self, -1, "FMM_Step")
        self.button_fmm.Bind(wx.EVT_BUTTON, parent.canvas_panel.color_gui_fmm)
        self.button_eucledian_step = wx.Button(self, -1, "Eucledian Step")
        self.button_eucledian_step.Bind(wx.EVT_BUTTON, parent.canvas_panel.color_eucledian_step)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.button_dijikstra, 1, wx.EXPAND | wx.ALL, 0)
        sizer_1.Add(self.button_fmm, 1, wx.EXPAND | wx.ALL, 0)
        sizer_1.Add(self.button_eucledian_step, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(sizer_1)
        self.Layout()


def get_path(wildcard):
    style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    dialog = wx.FileDialog(None, "Choose a file", os.getcwd()+'Scenarios/', "", wildcard, style=style)
    if dialog.ShowModal() == wx.ID_OK:
        path = dialog.GetPath()
    else:
        path = None
    dialog.Destroy()
    return path


def main():
    app = wx.App()
    file_name = get_path('.json')
    gui = Frame(parent=None, system=initialize_system(file_name))
    gui.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
