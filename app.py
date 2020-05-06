import wx
import model as model
import json
import os


def initialize_system(file_name):
    """
    Reads the scenario file and initializes the system.
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

    if 'cell_size' in data:
        cell_size = data["cell_size"]
    else:
        cell_size = 5

    return system, cell_size


class Frame(wx.Frame):
    """
    Main window that holds the canvas and button panel.
    """
    def __init__(self, parent, system, cell_size):
        wx.Frame.__init__(self, parent)
        self.system = system
        self.cell_size = cell_size

        self.SetTitle("Cellular Automaton")
        self.SetSize(self.system.cols * self.cell_size, self.system.rows * self.cell_size + 50)
        # self.SetMinSize((500, 500))
        self.canvas_panel = Canvas(self)
        self.button_panel = ButtonPanel(self)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.canvas_panel, 1, wx.EXPAND | wx.ALL, 0)
        sizer_1.Add(self.button_panel, 0, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(sizer_1)
        self.Layout()


class Canvas(wx.Panel):
    """
    Panel that is painted at every step to pictorially show most updated state of the system.
    """
    def __init__(self, parent: Frame, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name="Canvas"):
        super(Canvas, self).__init__(parent, id, pos, size, style, name)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.parent = parent

    def OnSize(self, event):
        self.Refresh()  # MUST have this, else the rectangle gets rendered corruptly when resizing the window!
        event.Skip()  # seems to reduce the amount of OnSize and OnPaint events generated when resizing the window

    def OnPaint(self, event):
        """
        Prints the current state of the system on canvas (Panel).
        :param event:
        :return:
        """
        dc = wx.PaintDC(self)
        dc.Clear()
        # print(self.parent.system.__str__())
        for col in self.parent.system.grid:
            for cell in col:
                if cell.state == model.EMPTY and self.parent.cell_size <= 5:
                    continue
                dc.SetBrush(wx.Brush(cell.state))
                dc.DrawRectangle(cell.col * self.parent.cell_size, cell.row * self.parent.cell_size,
                                 self.parent.cell_size, self.parent.cell_size)

    def update_step_dijikstra(self, event):
        """
        On button click, makes update call for system and prints updated state on canvas.
        :param event:
        :return:
        """
        self.parent.button_panel.button_fmm.Disable()
        self.parent.button_panel.button_eucledian_step.Disable()
        if not self.parent.system.initialized:
            self.parent.system.initialized = True
            self.parent.system.evaluate_dijikstra_cell_utilities()
        self.parent.system.update_system_dijikstra()
        self.OnPaint(event)

    def update_step_fmm(self, event):
        """
        On button click, makes update call to system and prints updated state on canvas.
        :param event:
        :return:
        """
        self.parent.button_panel.button_dijikstra.Disable()
        self.parent.button_panel.button_eucledian_step.Disable()
        self.parent.system.update_system_fmm()
        self.OnPaint(event)

    def update_step_euclidean(self, event):
        """
        On button click, makes update call to system and prints updated state on canvas.
        :param event:
        :return:
        """
        self.parent.button_panel.button_dijikstra.Disable()
        self.parent.button_panel.button_fmm.Disable()
        if not self.parent.system.initialized:
            self.parent.system.initialized = True
            self.parent.system.evaluate_euclidean_cell_utilities()
        self.parent.system.update_system_euclidean()
        self.OnPaint(event)


class ButtonPanel(wx.Panel):

    def __init__(self, parent: Frame, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0,
                 name="ButtonPanel"):
        super(ButtonPanel, self).__init__(parent, id, pos, size, style, name)
        self.button_dijikstra = wx.Button(self, -1, "Dijikstra_Step")
        self.button_dijikstra.Bind(wx.EVT_BUTTON, parent.canvas_panel.update_step_dijikstra)
        self.button_fmm = wx.Button(self, -1, "FMM_Step")
        self.button_fmm.Bind(wx.EVT_BUTTON, parent.canvas_panel.update_step_fmm)
        self.button_eucledian_step = wx.Button(self, -1, "Eucledian Step")
        self.button_eucledian_step.Bind(wx.EVT_BUTTON, parent.canvas_panel.update_step_euclidean)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.button_dijikstra, 1, wx.EXPAND | wx.ALL, 0)
        sizer_1.Add(self.button_fmm, 1, wx.EXPAND | wx.ALL, 0)
        sizer_1.Add(self.button_eucledian_step, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(sizer_1)
        self.Layout()


def get_path(wildcard):
    """
    Returns file name selected in the open dialog
    :param wildcard:
    :return:
    """
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
    system, cell_size = initialize_system(file_name)
    gui = Frame(None, system, cell_size,)
    gui.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
