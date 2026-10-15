import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Интеграция Matplotlib и PySide6")
        self.setGeometry(100, 100, 900, 700)

        # Главный виджет и слой
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Создаем объект Figure (контейнер для графиков)
        # tight_layout=True автоматически настраивает отступы между графиками
        self.figure = Figure(figsize=(8, 6), dpi=100, tight_layout=True)

        # 2. Создаем холст (Canvas), который является виджетом Qt
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        # 3. Создаем сетку графиков (2 строки, 2 столбца) внутри Figure
        self.axes = self.figure.subplots(2, 2)

        # Разворачиваем двумерный массив осей в одномерный для удобного перебора
        self.ax_flat = self.axes.flatten()

        # Кнопка для генерации новых данных
        self.btn_update = QPushButton("Сгенерировать новые данные", self)
        self.btn_update.clicked.connect(self.plot_data)
        main_layout.addWidget(self.btn_update)

        # Отрисовываем графики при запуске
        self.plot_data()

    def plot_data(self):
        """Очищает старые графики и строит новые случайные данные."""
        # Генерируем тестовые данные
        x = np.linspace(0, 10, 100)

        # Очищаем каждую ось перед новой отрисовкой
        for ax in self.ax_flat:
            ax.clear()

        # --- График 1: Линейный (Синусоида с шумом) ---
        noise = np.random.normal(0, 0.2, len(x))
        self.ax_flat[0].plot(x, np.sin(x) + noise, color="crimson", label="Синус")
        self.ax_flat[0].set_title("Линейный график")
        self.ax_flat[0].grid(True)

        # --- График 2: Scatter (Точечный) ---
        x_rand = np.random.rand(50) * 10
        y_rand = np.random.rand(50) * 10
        colors = np.random.rand(50)
        self.ax_flat[1].scatter(x_rand, y_rand, c=colors, cmap="viridis", alpha=0.7)
        self.ax_flat[1].set_title("Точечная диаграмма")

        # --- График 3: Столбчатая диаграмма (Bar) ---
        categories = ["A", "B", "C", "D", "E"]
        values = np.random.randint(1, 15, size=5)
        self.ax_flat[2].bar(categories, values, color="teal")
        self.ax_flat[2].set_title("Столбчатая диаграмма")

        # --- График 4: Гистограмма распределения ---
        data_normal = np.random.normal(0, 1, 500)
        self.ax_flat[3].hist(data_normal, bins=20, color="gold", edgecolor="black", alpha=0.8)
        self.ax_flat[3].set_title("Гистограмма")

        # Обязательно вызываем draw(), чтобы Matplotlib перерисовал холст в Qt
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
