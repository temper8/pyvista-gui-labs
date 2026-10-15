import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QSpinBox, QDoubleSpinBox, QComboBox,
                             QLabel, QPushButton, QGroupBox)
from PySide6.QtCore import Qt

# Лимиты контролов (min, max, default)
BOX_DIM_MIN, BOX_DIM_MAX, BOX_DIM_DEFAULT = 20, 300, 90
MATH_DIM_MIN, MATH_DIM_MAX, MATH_DIM_DEFAULT = 10, 500, 60
FREQ_MIN, FREQ_MAX = 0, 20
FREQ_PHI_DEFAULT, FREQ_THETA_DEFAULT = 3, 2
OPACITY_MIN, OPACITY_MAX, OPACITY_DEFAULT = 0.0, 1.0, 0.50
RADII_MIN = 10

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Симулятор тороидальных полей высокого разрешения")
        self.setGeometry(100, 100, 1200, 850)

        # Главный контейнер
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # =====================================================================
        # ЛЕВАЯ ПАНЕЛЬ: Элементы управления
        # =====================================================================
        controls_widget = QWidget(self)
        controls_widget.setFixedWidth(320)
        controls_layout = QVBoxLayout(controls_widget)
        main_layout.addWidget(controls_widget)

        # Группа 1: Разрешение сеток
        group_res = QGroupBox("Разрешение (Resolution)", self)
        res_layout = QVBoxLayout(group_res)

        res_layout.addWidget(QLabel("Текстура GPU (box_dim):", self))
        self.spin_box_dim = QSpinBox(self)
        self.spin_box_dim.setRange(BOX_DIM_MIN, BOX_DIM_MAX)
        self.spin_box_dim.setValue(BOX_DIM_DEFAULT)
        res_layout.addWidget(self.spin_box_dim)

        res_layout.addWidget(QLabel("Точность расчета поля:", self))
        self.spin_math_dim = QSpinBox(self)
        self.spin_math_dim.setRange(MATH_DIM_MIN, MATH_DIM_MAX)
        self.spin_math_dim.setValue(MATH_DIM_DEFAULT)
        res_layout.addWidget(self.spin_math_dim)

        controls_layout.addWidget(group_res)

        # Группа 2: Частоты поля (ИСПРАВЛЕНО: Теперь добавляется в компоновщик!)
        group_freq = QGroupBox("Параметры поля (Frequencies)", self)
        freq_layout = QVBoxLayout(group_freq)

        freq_layout.addWidget(QLabel("Главная частота (вокруг Z):", self))
        self.spin_freq_phi = QSpinBox(self)
        self.spin_freq_phi.setRange(FREQ_MIN, FREQ_MAX)
        self.spin_freq_phi.setValue(FREQ_PHI_DEFAULT)
        freq_layout.addWidget(self.spin_freq_phi)

        freq_layout.addWidget(QLabel("Малая частота (вокруг трубы):", self))
        self.spin_freq_theta = QSpinBox(self)
        self.spin_freq_theta.setRange(FREQ_MIN, FREQ_MAX)
        self.spin_freq_theta.setValue(FREQ_THETA_DEFAULT)
        freq_layout.addWidget(self.spin_freq_theta)

        controls_layout.addWidget(group_freq) # <-- ЭТА СТРОКА БЫЛА ПРОПУЩЕНА!

        # Группа 3: Визуальные свойства
        group_vis = QGroupBox("Визуализация (Visualization)", self)
        vis_layout = QVBoxLayout(group_vis)

        vis_layout.addWidget(QLabel("Прозрачность (0.0 - 1.0):", self))
        self.spin_opacity = QDoubleSpinBox(self)
        self.spin_opacity.setRange(OPACITY_MIN, OPACITY_MAX)
        self.spin_opacity.setSingleStep(0.05)
        self.spin_opacity.setValue(OPACITY_DEFAULT)
        vis_layout.addWidget(self.spin_opacity)

        vis_layout.addWidget(QLabel("Палитра цветов (Colormap):", self))
        self.combo_cmap = QComboBox(self)
        self.combo_cmap.addItems(["plasma", "viridis", "inferno", "coolwarm", "jet", "magma", "bone"])
        vis_layout.addWidget(self.combo_cmap)

        controls_layout.addWidget(group_vis)

        # Группа 4: Экшены
        controls_layout.addSpacing(10)
        self.btn_update = QPushButton("🚀 Update Scene", self)
        self.btn_update.setStyleSheet("font-weight: bold; font-size: 14px; padding: 8px;")
        self.btn_update.clicked.connect(self.generate_and_render)
        controls_layout.addWidget(self.btn_update)

        controls_layout.addStretch()

        # =====================================================================
        # ПРАВАЯ ПАНЕЛЬ: Окно 3D Визуализации PyVista
        # =====================================================================
        self.plotter = QtInteractor(self)
        main_layout.addWidget(self.plotter.interactor)

        self.plotter.show_grid(color='gray')
        self.plotter.add_text("Advanced Toroidal Control", position="upper_left", font_size=10)

        # Первичный запуск отрисовки
        self.generate_and_render()
        self.plotter.reset_camera()
        self.show()

    def generate_and_render(self):
        box_dim = self.spin_box_dim.value()
        math_dim = self.spin_math_dim.value()
        current_cmap = self.combo_cmap.currentText()
        opacity_factor = self.spin_opacity.value()

        freq_phi = self.spin_freq_phi.value()
        freq_theta = self.spin_freq_theta.value()

        R_major = 3.0
        R_minor_max = 1.2

        # 1. Считаем поле на торической сетке заданной точности (StructuredGrid)
        n_angles = math_dim
        n_radii = max(RADII_MIN, math_dim // 3)
        phi = np.linspace(0, 2 * np.pi, n_angles)
        theta = np.linspace(0, 2 * np.pi, n_angles)
        r = np.linspace(0.1, R_minor_max, n_radii)
        PHI, THETA, R = np.meshgrid(phi, theta, r, indexing='ij')

        X = (R_major + R * np.cos(THETA)) * np.cos(PHI)
        Y = (R_major + R * np.cos(THETA)) * np.sin(PHI)
        Z = R * np.sin(THETA)

        torus = pv.StructuredGrid(X, Y, Z)
        field = np.sin(freq_phi * PHI + freq_theta * THETA) * (1.0 - (R / R_minor_max)**2)
        torus.point_data["Field"] = field.ravel(order="F")

        # 2. Куб для GPU-рендеринга и перенос в него поля через ресемплинг
        grid_gpu = pv.ImageData(dimensions=(box_dim, box_dim, box_dim))
        grid_gpu.origin = (-4.5, -4.5, -1.5)
        grid_gpu.spacing = (9.0 / (box_dim - 1), 9.0 / (box_dim - 1), 3.0 / (box_dim - 1))

        resampled = grid_gpu.sample(torus)

        # 3. Берем модуль поля, чтобы были видны обе доли волны
        resampled.point_data["Field"] = np.abs(resampled.point_data["Field"])

        base_opacity = np.array([0.0, 0.05, 0.1, 0.3, 0.6, 0.8, 1.0])
        dynamic_opacity = base_opacity * opacity_factor

        self.plotter.add_volume(
            resampled,
            scalars="Field",
            cmap=current_cmap,
            opacity=list(dynamic_opacity),
            shade=True,
            name="toroidal_volume_advanced",
            show_scalar_bar=False
        )
        self.plotter.render()

    def closeEvent(self, event):
        self.plotter.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
