import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Варианты pcolormesh в PySide6")
        self.setGeometry(100, 100, 1200, 500)

        # Интерфейс
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Создаем Figure с 3 подграфиками в один ряд
        self.figure = Figure(figsize=(12, 4), dpi=100, tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        # Создаем оси: первые две обычные, третья — полярная
        self.ax1 = self.figure.add_subplot(131)
        self.ax2 = self.figure.add_subplot(132)
        self.ax3 = self.figure.add_subplot(133, projection='polar')

        # Кнопка для смены цветовых схем (рандомизация)
        self.btn = QPushButton("Случайный сдвиг фазы данных", self)
        self.btn.clicked.connect(self.update_plots)
        main_layout.addWidget(self.btn)

        # Сохраняем colorbars, чтобы обновлять их, а не плодить новые
        self.cbars = [None, None, None]

        self.update_plots()

    def update_plots(self):
        # Очищаем старое содержимое и колорбары
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # Удаляем старые colorbars из фигуры, если они есть
        for cb in self.cbars:
            if cb:
                cb.remove()
        self.cbars = [None, None, None]

        # Случайный сдвиг фазы для динамики при нажатии кнопки
        phase = np.random.uniform(0, np.pi)

        # =====================================================================
        # ВАРИАНТ 1: Стандартная прямоугольная сетка (Математическая функция)
        # =====================================================================
        x = np.linspace(-3, 3, 100)
        y = np.linspace(-3, 3, 100)
        X, Y = np.meshgrid(x, y)
        # Функция: Гауссиана, умноженная на косинус со сдвигом фазы
        Z = np.exp(-X**2 - Y**2) * np.cos(2 * np.pi * X + phase)

        # shading='auto' автоматически обрабатывает размеры сетки и матрицы
        mesh1 = self.ax1.pcolormesh(X, Y, Z, cmap='viridis', shading='auto')
        self.ax1.set_title("1. Стандартная сетка")
        self.cbars[0] = self.figure.colorbar(mesh1, ax=self.ax1, orientation='horizontal', pad=0.15)

        # =====================================================================
        # ВАРИАНТ 2: Неравномерная / Искаженная сетка
        # =====================================================================
        # Создаем логарифмические или произвольно смещенные шаги по осям
        x2 = np.logspace(0.1, 1, 50)
        y2 = np.linspace(-2, 2, 50)
        X2, Y2 = np.meshgrid(x2, y2)
        # Искажаем сетку, делая её волнообразной
        X2 = X2 + 0.1 * np.sin(Y2 * 3)
        Z2 = np.sin(X2 + phase) * np.cosh(Y2 / 2)

        mesh2 = self.ax2.pcolormesh(X2, Y2, Z2, cmap='plasma', shading='auto')
        self.ax2.set_title("2. Искаженная сетка")
        self.cbars[1] = self.figure.colorbar(mesh2, ax=self.ax2, orientation='horizontal', pad=0.15)

        # =====================================================================
        # ВАРИАНТ 3: Полярные координаты (Polar pcolormesh)
        # =====================================================================
        r = np.linspace(0, 1, 50)
        theta = np.linspace(0, 2 * np.pi, 60)
        R, Theta = np.meshgrid(r, theta)
        # Значения зависят от радиуса и угла
        Z3 = R * np.sin(3 * Theta + phase)

        # Для полярных осей X — это угол (Theta), Y — это радиус (R)
        mesh3 = self.ax3.pcolormesh(Theta, R, Z3, cmap='inferno', shading='auto')
        self.ax3.set_title("3. Полярная сетка", pad=20)
        self.cbars[2] = self.figure.colorbar(mesh3, ax=self.ax3, orientation='horizontal', pad=0.2)

        # Перерисовываем холст
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
