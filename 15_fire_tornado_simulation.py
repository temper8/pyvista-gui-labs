import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QSpinBox, QDoubleSpinBox, QComboBox,
                             QLabel, QPushButton, QGroupBox)
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("3D Симулятор огненного вихря (Fire Tornado)")
        self.setGeometry(100, 100, 1200, 850)

        # Главный контейнер
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # =====================================================================
        # ЛЕВАЯ ПАНЕЛЬ: Управление
        # =====================================================================
        controls_widget = QWidget(self)
        controls_widget.setFixedWidth(320)
        controls_layout = QVBoxLayout(controls_widget)
        main_layout.addWidget(controls_widget)

        # Группа 1: Геометрия и сетка
        group_res = QGroupBox("Параметры симуляции", self)
        res_layout = QVBoxLayout(group_res)

        res_layout.addWidget(QLabel("Разрешение 3D текстуры (box_dim):", self))
        self.spin_box_dim = QSpinBox(self)
        self.spin_box_dim.setRange(30, 200)
        self.spin_box_dim.setValue(100)
        res_layout.addWidget(self.spin_box_dim)

        controls_layout.addWidget(group_res)

        # Группа 2: Вихрь (Частоты и закрутка)
        group_freq = QGroupBox("Динамика пламени", self)
        freq_layout = QVBoxLayout(group_freq)

        freq_layout.addWidget(QLabel("Количество языков пламени:", self))
        self.spin_flames = QSpinBox(self)
        self.spin_flames.setRange(1, 10)
        self.spin_flames.setValue(3)  # Количество переплетенных струй огня
        freq_layout.addWidget(self.spin_flames)

        freq_layout.addWidget(QLabel("Шаг скручивания вихря:", self))
        self.spin_twist = QDoubleSpinBox(self)
        self.spin_twist.setRange(0.0, 5.0)
        self.spin_twist.setValue(1.5)  # Насколько сильно закручивается спираль вверх
        freq_layout.addWidget(self.spin_twist)

        controls_layout.addWidget(group_freq)

        # Группа 3: Оптика и свет
        group_vis = QGroupBox("Оптика пламени", self)
        vis_layout = QVBoxLayout(group_vis)

        vis_layout.addWidget(QLabel("Яркость/Прозрачность (0.0 - 1.0):", self))
        self.spin_opacity = QDoubleSpinBox(self)
        self.spin_opacity.setRange(0.0, 1.0)
        self.spin_opacity.setSingleStep(0.05)
        self.spin_opacity.setValue(0.60)
        vis_layout.addWidget(self.spin_opacity)

        vis_layout.addWidget(QLabel("Внутреннее свечение (Ambient):", self))
        self.spin_ambient = QDoubleSpinBox(self)
        self.spin_ambient.setRange(0.0, 1.0)
        self.spin_ambient.setSingleStep(0.1)
        self.spin_ambient.setValue(0.4)  # Самосвечение газа
        vis_layout.addWidget(self.spin_ambient)

        vis_layout.addWidget(QLabel("Цветовая схема:", self))
        self.combo_cmap = QComboBox(self)
        self.combo_cmap.addItems(["Настоящее пламя 🔥", "magma", "plasma", "inferno"])
        vis_layout.addWidget(self.combo_cmap)

        controls_layout.addWidget(group_vis)

        # Кнопка обновления
        controls_layout.addSpacing(10)
        self.btn_update = QPushButton("🔥 Поджечь вихрь", self)
        self.btn_update.setStyleSheet("font-weight: bold; font-size: 14px; padding: 8px;")
        self.btn_update.clicked.connect(self.generate_and_render)
        controls_layout.addWidget(self.btn_update)

        controls_layout.addStretch()

        # =====================================================================
        # ПРАВАЯ ПАНЕЛЬ: 3D Окно (PyVista)
        # =====================================================================
        self.plotter = QtInteractor(self)
        main_layout.addWidget(self.plotter.interactor)

        # Настраиваем темную кинематографичную сцену (как задний фон на фото)
        self.plotter.set_background("black")
        self.plotter.add_text("Fire Tornado Volume Simulation", position="upper_left", font_size=10, color="white")

        self.generate_and_render()
        self.plotter.reset_camera()
        self.show()

    def generate_and_render(self):
        """Генерирует вертикальное вихревое поле и запекает его в текстуру пламени."""
        box_dim = self.spin_box_dim.value()
        cmap_type = self.combo_cmap.currentText()
        opacity_factor = self.spin_opacity.value()
        ambient_value = self.spin_ambient.value()

        num_flames = self.spin_flames.value()
        twist_speed = self.spin_twist.value()

        # 1. Создаем вытянутый вверх 3D-куб (коробку для смерча)
        grid_gpu = pv.ImageData(dimensions=(box_dim, box_dim, int(box_dim * 1.5)))
        grid_gpu.origin = (-2.0, -2.0, 0.0)
        # Вытягиваем сетку по вертикали (ось Z)
        grid_gpu.spacing = (4.0 / (box_dim - 1), 4.0 / (box_dim - 1), 7.0 / (int(box_dim * 1.5) - 1))

        # 2. Получаем координаты точек
        points = grid_gpu.points
        X, Y, Z = points[:, 0], points[:, 1], points[:, 2]

        # 3. Переводим координаты XY в цилиндрические (радиус r, угол phi) для закрутки
        R_cyl = np.sqrt(X**2 + Y**2)
        PHI = np.arctan2(Y, X)

        # 4. МАТЕМАТИКА ОГНЕННОГО СМЕРЧА
        # Динамический радиус вихря: пламя расширяется у основания и сужается кверху (конус)
        max_z = 7.0
        cone_radius = 1.2 * (1.0 - 0.5 * (Z / max_z))

        # Винтовое скручивание: угол сдвигается пропорционально высоте Z
        twisted_phi = PHI - twist_speed * Z

        # Формируем языки пламени (синусоида по закрученному углу)
        flame_strands = np.cos(num_flames * twisted_phi)

        # Ограничиваем толщину огненного столба и добавляем затухание тепла кверху
        intensity = (1.0 - (R_cyl / cone_radius)**2) * (1.0 - (Z / max_z)**0.7)

        # Объединяем структуру струй и тепловое поле
        field = (flame_strands + 1.0) * 0.5 * intensity

        # Маскируем строго по конусу пламени, всё что за ним — абсолютный ноль (невидимо)
        field = np.where((R_cyl <= cone_radius) & (Z < max_z - 0.1), field, 0.0)

        # Избавляемся от шумов
        field = np.clip(field, 0.0, 1.0)
        grid_gpu.point_data["FlameDensity"] = field.ravel(order="F")

        # 5. Настройка палитры и прозрачности
        if cmap_type == "Настоящее пламя 🔥":
            # Наша кастомная палитра с фотографии: от черного угля через искры к белому ядру
            chosen_cmap = ["#000000", "#1f0600", "#5c0c00", "#bf2a00", "#ff6a00", "#ffb700", "#ffee99", "#ffffff"]
            # Зануляем первые два темных цвета, чтобы края пламени "растворялись" в темноте мягко
            base_opacity = np.array([0.0, 0.02, 0.10, 0.35, 0.65, 0.85, 0.95, 1.0])
        else:
            chosen_cmap = cmap_type
            base_opacity = np.array([0.0, 0.01, 0.05, 0.20, 0.50, 0.75, 1.0])

        dynamic_opacity = base_opacity * opacity_factor

        # 6. Объемный рендеринг
        self.plotter.add_volume(
            grid_gpu,
            scalars="FlameDensity",
            cmap=chosen_cmap,
            opacity=list(dynamic_opacity),
            shade=True,
            name="fire_tornado_volume",
            show_scalar_bar=False
        )

        # 7. Тонкая настройка оптических шейдеров актера (Эффект внутреннего свечения газа)
        volume_actor = self.plotter.renderer.actors["fire_tornado_volume"]
        prop = volume_actor.GetProperty()
        prop.SetAmbient(ambient_value)      # Эффект самосвечения раскаленных газов
        prop.SetDiffuse(1.0 - ambient_value) # Рассеивание внешнего света

        self.plotter.render()

    def closeEvent(self, event):
        self.plotter.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
