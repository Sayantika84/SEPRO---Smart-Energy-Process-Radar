from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from collections import deque

class ProcessGraph(QWidget):
    def __init__(self, max_points=300):
        super().__init__()

        self.cpu_history = deque(maxlen=max_points)
        self.score_history = deque(maxlen=max_points)

        layout = QVBoxLayout(self)

        self.base_title = "Power Trend (CPU% vs Score)"
        self.plot = pg.PlotWidget(title=self.base_title)
        self.plot.showGrid(x=True, y=True, alpha=0.4)

        # CPU Curve (Left Axis)
        self.cpu_curve = self.plot.plot(
            pen=pg.mkPen('#00E5FF', width=2),
            name="CPU %"
        )

        # Enable right axis
        self.plot.showAxis('right')

        # Create second ViewBox for score
        self.score_axis = pg.ViewBox()
        self.plot.scene().addItem(self.score_axis)
        self.plot.getAxis('right').linkToView(self.score_axis)
        self.score_axis.setXLink(self.plot)

        # Score Curve (Right Axis)
        self.score_curve = pg.PlotCurveItem(
            pen=pg.mkPen('#FFE600', width=2, style=pg.QtCore.Qt.PenStyle.DashLine)
        )
        self.score_axis.addItem(self.score_curve)

        self.plot.setLabel('left', 'CPU %')
        self.plot.setLabel('right', 'Score ×100')
        self.plot.setLabel('bottom', 'Time (samples)')

        layout.addWidget(self.plot)

        # Sync sizes without deprecated VB access
        self.plot.getViewBox().sigResized.connect(self._sync_axes)

    def _sync_axes(self):
        self.score_axis.setGeometry(self.plot.getViewBox().sceneBoundingRect())
        self.score_axis.linkedViewChanged(self.plot.getViewBox(), self.score_axis.XAxis)

    def update(self, cpu, score):
        self.cpu_history.append(cpu)
        self.score_history.append(score * 100)

        self.cpu_curve.setData(list(self.cpu_history))
        self.score_curve.setData(list(self.score_history))
    def set_tracking_process(self, process_name):
        """Resets the title when tracking a new process."""
        self.plot.setTitle(f"{self.base_title} - Tracking: {process_name}")
    def freeze(self):
        self.plot.setTitle("Process Closed — Graph Frozen")
