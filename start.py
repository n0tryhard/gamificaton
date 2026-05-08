import arcade
import math

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Prestige Motors"


class Button:
    """Кастомная кнопка с анимациями наведения и нажатия"""

    def __init__(self, center_x, center_y, width, height, text, font_size=22):
        self.center_x = center_x
        self.center_y = center_y
        self.width = width
        self.height = height
        self.text = text
        self.font_size = font_size

        # Состояния кнопки
        self.hovered = False
        self.pressed = False

        # Анимация плавного перехода (0.0 = обычное состояние, 1.0 = полное наведение)
        self.hover_progress = 0.0
        # Анимация нажатия (масштаб)
        self.press_scale = 1.0

        # Цвета
        self.bg_normal = (40, 40, 45, 200)  # Тёмно-серый полупрозрачный
        self.bg_hover = (70, 70, 75, 230)  # Светлее при наведении
        self.bg_press = (55, 55, 60, 255)  # Чуть темнее при нажатии
        self.border_normal = (120, 120, 125, 150)  # Серая рамка
        self.border_hover = (200, 195, 180, 220)  # Светлая рамка при наведении
        self.text_normal = (210, 210, 215, 255)  # Светло-серый текст
        self.text_hover = (255, 250, 240, 255)  # Белый текст при наведении

        # Callback при клике
        self.on_click = None

    def update(self, delta_time):
        """Обновление анимаций"""
        # Плавный переход hover_progress
        target = 1.0 if self.hovered else 0.0
        speed = 6.0  # Скорость анимации
        self.hover_progress += (target - self.hover_progress) * speed * delta_time

        # Плавное возвращение масштаба после нажатия
        target_scale = 0.96 if self.pressed else 1.0
        self.press_scale += (target_scale - self.press_scale) * 12.0 * delta_time

    def _lerp_color(self, c1, c2, t):
        """Линейная интерполяция между двумя цветами"""
        return tuple(max(0, min(255, int(a + (b - a) * t))) for a, b in zip(c1, c2))

    def _rounded_rect_points(self, cx, cy, w, h, radius):
        """Генерация точек скруглённого прямоугольника"""
        r = min(radius, w / 2, h / 2)
        points = []
        # Количество сегментов на каждый угол
        segments = 8

        # Четыре угла: правый верхний, левый верхний, левый нижний, правый нижний
        corners = [
            (cx + w / 2 - r, cy + h / 2 - r, 0, 90),  # Правый верхний
            (cx - w / 2 + r, cy + h / 2 - r, 90, 180),  # Левый верхний
            (cx - w / 2 + r, cy - h / 2 + r, 180, 270),  # Левый нижний
            (cx + w / 2 - r, cy - h / 2 + r, 270, 360),  # Правый нижний
        ]

        for corner_x, corner_y, start_angle, end_angle in corners:
            for i in range(segments + 1):
                angle = math.radians(start_angle + (end_angle - start_angle) * i / segments)
                x = corner_x + r * math.cos(angle)
                y = corner_y + r * math.sin(angle)
                points.append((x, y))

        return points

    def draw(self):
        """Отрисовка кнопки"""
        t = self.hover_progress
        scale = self.press_scale

        w = self.width * scale
        h = self.height * scale
        radius = 12 * scale  # Радиус скругления углов

        # Интерполяция цветов
        if self.pressed:
            bg = self.bg_press
        else:
            bg = self._lerp_color(self.bg_normal, self.bg_hover, t)

        border = self._lerp_color(self.border_normal, self.border_hover, t)
        text_color = self._lerp_color(self.text_normal, self.text_hover, t)

        # Генерируем точки скруглённого прямоугольника
        points = self._rounded_rect_points(self.center_x, self.center_y, w, h, radius)

        # Фон кнопки (залитый скруглённый прямоугольник)
        arcade.draw_polygon_filled(points, bg)

        # Рамка кнопки (контур скруглённого прямоугольника)
        arcade.draw_polygon_outline(points, border, 1)

        # Текст кнопки
        arcade.draw_text(
            self.text,
            self.center_x, self.center_y,
            text_color,
            font_size=int(self.font_size * scale),
            font_name=("Garamond", "Palatino Linotype", "Georgia"),
            anchor_x="center",
            anchor_y="center",
        )

    def check_hover(self, x, y):
        """Проверка, находится ли мышь над кнопкой"""
        half_w = self.width / 2
        half_h = self.height / 2
        self.hovered = (self.center_x - half_w <= x <= self.center_x + half_w and
                        self.center_y - half_h <= y <= self.center_y + half_h)
        return self.hovered

    def check_press(self, x, y):
        """Проверка нажатия на кнопку"""
        if self.check_hover(x, y):
            self.pressed = True
            return True
        return False

    def check_release(self, x, y):
        """Проверка отпускания кнопки"""
        was_pressed = self.pressed
        self.pressed = False
        if was_pressed and self.check_hover(x, y):
            if self.on_click:
                self.on_click()
            return True
        return False


class StartView(arcade.View):
    def __init__(self):
        super().__init__()

        # Загружаем задний фон из указанного файла
        self.background_list = arcade.SpriteList()
        try:
            self.background = arcade.Sprite("background.png")
            self.background_list.append(self.background)
        except Exception as e:
            print(f"Не удалось загрузить фон: {e}")
            self.background = None

        # Кнопки (будут позиционированы в on_resize)
        self.buttons = []

        # Создаем кнопки меню
        btn_new = Button(0, 0, 380, 55, "НАЧАТЬ ИГРУ", font_size=30)
        btn_new.on_click = self.on_click_start
        self.buttons.append(btn_new)

        btn_exit = Button(0, 0, 380, 55, "ВЫХОД", font_size=30)
        btn_exit.on_click = self.on_click_exit
        self.buttons.append(btn_exit)

        # Анимация заголовка
        self.time = 0.0

        # Анимация перехода (fade out)
        self.fade_alpha = 0.0
        self.fading_out = False

    def _position_elements(self, width, height):
        """Позиционируем все элементы относительно текущего размера окна"""
        # Фон — растягиваем на весь экран
        if self.background:
            self.background.center_x = width / 2
            self.background.center_y = height / 2
            self.background.width = width
            self.background.height = height

        # Кнопки — размещаем ниже центра экрана, друг под другом
        btn_x = width / 2
        btn_start_y = height * 0.38  # Начинаем чуть ниже центра
        btn_spacing = 68

        for i, btn in enumerate(self.buttons):
            btn.center_x = btn_x
            btn.center_y = btn_start_y - i * btn_spacing

    def on_resize(self, width: int, height: int):
        """Вызывается при изменении размеров окна"""
        super().on_resize(width, height)
        self._position_elements(width, height)

    def on_show_view(self):
        """Вызывается, когда мы переключаемся на этот экран"""
        arcade.set_background_color((15, 15, 20))
        self._position_elements(self.window.width, self.window.height)

    def on_update(self, delta_time):
        """Обновление анимаций"""
        self.time += delta_time
        for btn in self.buttons:
            btn.update(delta_time)

        # Обновляем анимацию fade out
        if self.fading_out:
            self.fade_alpha += delta_time * 350  # Скорость затемнения
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                # Переходим на экран выбора персонажа
                from select_person import SelectPersonView
                next_view = SelectPersonView()
                self.window.show_view(next_view)

    def on_click_start(self):
        """Запуск плавного перехода к экрану выбора персонажа"""
        if not self.fading_out:
            self.fading_out = True

    def on_click_continue(self):
        print("Кнопка 'Продолжить' нажата!")

    def on_click_settings(self):
        print("Кнопка 'Настройки' нажата!")

    def on_click_exit(self):
        arcade.exit()

    def on_draw(self):
        """Отрисовка экрана"""
        self.clear()

        w = self.window.width
        h = self.window.height

        # 1. Рисуем фон
        self.background_list.draw()

        # 2. Полупрозрачное затемнение поверх фона (для контраста текста)
        arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (0, 0, 0, 100))

        # 3. Декоративные элементы
        pulse = 0.7 + 0.3 * math.sin(self.time * 1.2)
        gold_alpha = int(70 * pulse)
        gold = (180, 160, 100, gold_alpha)

        # Рамка по краям экрана
        margin = 50
        arcade.draw_line(margin, margin, w - margin, margin, gold, 2)
        arcade.draw_line(margin, h - margin, w - margin, h - margin, gold, 2)
        arcade.draw_line(margin, margin, margin, h - margin, gold, 2)
        arcade.draw_line(w - margin, margin, w - margin, h - margin, gold, 2)

        # Ромбы по углам рамки
        ds = 10
        for dx, dy in [(margin, margin), (w - margin, margin),
                       (margin, h - margin), (w - margin, h - margin)]:
            pts = [(dx, dy + ds), (dx + ds, dy), (dx, dy - ds), (dx - ds, dy)]
            arcade.draw_polygon_filled(pts, (200, 180, 120, int(120 * pulse)))

        # Декоративные линии вокруг заголовка
        title_y = h * 0.68
        line_half = 320
        line_alpha = int(80 * pulse)
        lc = (180, 160, 100, line_alpha)
        arcade.draw_line(w / 2 - line_half, title_y - 60, w / 2 + line_half, title_y - 60, lc, 2)
        arcade.draw_line(w / 2 - line_half, title_y + 60, w / 2 + line_half, title_y + 60, lc, 2)

        # Ромбы на концах линий
        for lx in [w / 2 - line_half, w / 2 + line_half]:
            for ly in [title_y - 60, title_y + 60]:
                pts = [(lx, ly + 7), (lx + 7, ly), (lx, ly - 7), (lx - 7, ly)]
                arcade.draw_polygon_filled(pts, (200, 180, 120, int(100 * pulse)))

        # 4. Заголовок "Prestige Motors"
        arcade.draw_text(
            "Prestige Motors",
            w / 2, title_y,
            (240, 238, 230, 255),
            font_size=100,
            font_name=("Garamond", "Palatino Linotype", "Georgia"),
            anchor_x="center",
            anchor_y="center",
        )

        # 5. Рисуем кнопки
        for btn in self.buttons:
            btn.draw()

        # 6. Overlay затемнения для перехода
        if self.fade_alpha > 0:
            arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (0, 0, 0, int(self.fade_alpha)))

    def on_mouse_motion(self, x, y, dx, dy):
        """Отслеживание движения мыши (для наведения на кнопки)"""
        for btn in self.buttons:
            btn.check_hover(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        """Нажатие мыши"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            for btn in self.buttons:
                btn.check_press(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        """Отпускание мыши"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            for btn in self.buttons:
                btn.check_release(x, y)


def main():
    # Полноэкранный режим
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=False, resizable=True)
    start_view = StartView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()
