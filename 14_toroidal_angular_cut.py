import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QSpinBox, QDoubleSpinBox, QComboBox,
                             QLabel, QPushButton, QGroupBox, QCheckBox)
from PySide6.QtCore import Qt

# Лимиты контролов (min, max, default)
BOX_DIM_MIN, BOX_DIM_MAX, BOX_DIM_DEFAULT = 20, 300, 90
MATH_DIM_MIN, MATH_DIM_MAX, MATH_DIM_DEFAULT = 10, 500, 60
FREQ_MIN, FREQ_MAX = 0, 20
FREQ_PHI_DEFAULT, FREQ_THETA_DEFAULT = 3, 2
CUT_ANGLE_MIN, CUT_ANGLE_MAX, CUT_ANGLE_DEFAULT = 0, 360, 90
OPACITY_MIN, OPACITY_MAX, OPACITY_DEFAULT = 0.0, 1.0, 0.50

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Симулятор полей: Угловой секторный вырез тора")
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

        # Группа 2: Частоты поля
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

        controls_layout.addWidget(group_freq)

        # Группа 3: Угловой вырез (Обновлено под градусы!)
        group_clip = QGroupBox("Сечение объема (Angular Cut)", self)
        clip_layout = QVBoxLayout(group_clip)

        self.check_clip = QCheckBox("Включить угловой вырез", self)
        self.check_clip.setChecked(True)
        clip_layout.addWidget(self.check_clip)

        clip_layout.addWidget(QLabel("Угол выреза (в градусах):", self))
        self.spin_cut_angle = QSpinBox(self)
        self.spin_cut_angle.setRange(CUT_ANGLE_MIN, CUT_ANGLE_MAX)
        self.spin_cut_angle.setSingleStep(15)
        self.spin_cut_angle.setValue(CUT_ANGLE_DEFAULT) # По умолчанию вырезаем четверть бублика (90 градусов)
        clip_layout.addWidget(self.spin_cut_angle)

        controls_layout.addWidget(group_clip)

        # Группа 4: Визуальные свойства
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

        # Группа 5: Экшены
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
        self.plotter.add_text("Toroidal Field with Angular Cut", position="upper_left", font_size=10)

        # Первичный запуск отрисовки
        self.generate_and_render()
        self.plotter.reset_camera()
        self.show()

    def generate_and_render(self):
        """Полный перерасчет тороидального объема с угловым вырезом сектора."""
        box_dim = self.spin_box_dim.value()
        current_cmap = self.combo_cmap.currentText()
        opacity_factor = self.spin_opacity.value()

        freq_phi = self.spin_freq_phi.value()
        freq_theta = self.spin_freq_theta.value()

        # Параметры углового выреза
        is_clip_enabled = self.check_clip.isChecked()
        cut_angle_deg = self.spin_cut_angle.value()
        # Переводим угол из градусов в радианы для работы с массивами NumPy
        cut_angle_rad = np.radians(cut_angle_deg)

        R_major = 3.0
        R_minor_max = 1.2

        # 1. Создаем ImageData (Текстура GPU)
        grid_gpu = pv.ImageData(dimensions=(box_dim, box_dim, box_dim))
        grid_gpu.origin = (-4.5, -4.5, -1.5)
        grid_gpu.spacing = (9.0 / (box_dim - 1), 9.0 / (box_dim - 1), 3.0 / (box_dim - 1))

        # 2. Декартовы координаты
        points = grid_gpu.points
        X, Y, Z = points[:, 0], points[:, 1], points[:, 2]

        # 3. Обратное вычисление тороидальной геометрии
        # np.arctan2 возвращает углы в диапазоне от -pi до pi
        PHI = np.arctan2(Y, X)

        # Переводим PHI в диапазон от 0 до 2*pi для удобного отсечения секторов
        PHI_pos = np.where(PHI >= 0, PHI, PHI + 2 * np.pi)

        r_current = np.sqrt(X**2 + Y**2)
        THETA = np.arctan2(Z, r_current - R_major)
        R = np.sqrt((r_current - R_major)**2 + Z**2)

        # 4. Расчет математического поля
        field = np.sin(freq_phi * PHI + freq_theta * THETA) * (1.0 - (R / R_minor_max)**2)

        # Маскирование А: зануление за пределами физических границ тора
        field = np.where(R <= R_minor_max, field, 0.0)

        # Маскирование Б: Угловой клиппинг сектора «пирога»
        # Если угол точки попадает в диапазон от 0 до cut_angle_rad, зануляем поле в этой зоне
        if is_clip_enabled and cut_angle_rad > 0:
            field = np.where((PHI_pos >= 0) & (PHI_pos <= cut_angle_rad), 0.0, field)

        # Модуль для идеальной прозрачности фона и вырезанного сегмента
        field_abs = np.abs(field)
        grid_gpu.point_data["Field"] = field_abs.ravel(order="F")

        # 5. Профиль прозрачности
        base_opacity = np.array([0.0, 0.05, 0.1, 0.3, 0.6, 0.8, 1.0])
        dynamic_opacity = base_opacity * opacity_factor

        # 6. Отрисовка объема на GPU
        self.plotter.add_volume(
            grid_gpu,
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
