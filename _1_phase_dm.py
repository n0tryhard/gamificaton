import arcade
import math
from start import StartView
from start import Button

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Диалог: список кортежей (имя_говорящего, текст). None = три точки.
DIALOGUE = [
    (None, "..."),
    ("Начальник", "Дмитрий, доброе утро! Нам нужно поговорить."),
    ("Дмитрий", "Доброе утро, Александр Иванович. Слушаю вас."),
    ("Начальник",
     "Руководство приняло решение о внедрении новой системы документооборота. Это затронет всех сотрудников."),
    ("Начальник", "Речь идёт о полной автоматизации: сканирование, CRM, распределение документов. Что думаешь?"),
]

CHOICES = [
    "Я открыт к новому — когда начинаем?",
    "Мне нужно время подумать...",
    "Это разрушит привычный процесс!",
]


def _rounded_rect_points(cx, cy, w, h, radius):
    """Генерация точек скруглённого прямоугольника"""
    r = min(radius, w / 2, h / 2)
    points = []
    segments = 8
    corners = [
        (cx + w / 2 - r, cy + h / 2 - r, 0, 90),
        (cx - w / 2 + r, cy + h / 2 - r, 90, 180),
        (cx - w / 2 + r, cy - h / 2 + r, 180, 270),
        (cx + w / 2 - r, cy - h / 2 + r, 270, 360),
    ]
    for corner_x, corner_y, start_angle, end_angle in corners:
        for i in range(segments + 1):
            angle = math.radians(start_angle + (end_angle - start_angle) * i / segments)
            x = corner_x + r * math.cos(angle)
            y = corner_y + r * math.sin(angle)
            points.append((x, y))
    return points


def _lerp_color(c1, c2, t):
    return tuple(max(0, min(255, int(a + (b - a) * t))) for a, b in zip(c1, c2))


class ChoiceButton:
    """Кнопка выбора ответа"""

    def __init__(self, center_x, center_y, width, height, text):
        self.center_x = center_x
        self.center_y = center_y
        self.width = width
        self.height = height
        self.text = text
        self.hovered = False
        self.hover_progress = 0.0
        self.on_click = None

    def update(self, delta_time):
        target = 1.0 if self.hovered else 0.0
        self.hover_progress += (target - self.hover_progress) * 8.0 * delta_time

    def draw(self):
        t = self.hover_progress
        bg = _lerp_color((35, 40, 50, 220), (50, 55, 65, 240), t)
        border = _lerp_color((80, 85, 95, 150), (180, 175, 160, 220), t)
        text_col = _lerp_color((200, 200, 205, 255), (255, 250, 240, 255), t)

        points = _rounded_rect_points(self.center_x, self.center_y,
                                      self.width, self.height, 10)
        arcade.draw_polygon_filled(points, bg)
        arcade.draw_polygon_outline(points, border, 1)

        arcade.draw_text(
            self.text,
            self.center_x - self.width / 2 + 25, self.center_y,
            text_col, font_size=16,
            font_name=("Garamond", "Palatino Linotype", "Georgia"),
            anchor_x="left", anchor_y="center",
        )

    def check_hover(self, x, y):
        half_w = self.width / 2
        half_h = self.height / 2
        self.hovered = (self.center_x - half_w <= x <= self.center_x + half_w and
                        self.center_y - half_h <= y <= self.center_y + half_h)
        return self.hovered

    def check_click(self, x, y):
        if self.check_hover(x, y):
            if self.on_click:
                self.on_click()
            return True
        return False


class Phase1DmView(arcade.View):
    """Первая фаза Дмитрия — диалог с начальником"""

    def __init__(self):
        super().__init__()

        self.menu_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 100, 250, 60, "В ГЛАВНОЕ МЕНЮ")
        self.next_button = Button(SCREEN_WIDTH // 2 + 150, SCREEN_HEIGHT // 2 - 100, 250, 60, "ДАЛЕЕ")

        # Привязываем функции клика (создадим их чуть ниже)
        self.menu_button.on_click = self.go_to_menu
        self.next_button.on_click = self.go_to_next_phase

        self.phase_finished = False
        # Фон

        self.background_list = arcade.SpriteList()
        try:
            self.bg = arcade.Sprite("1_phase_dm.png")
            self.background_list.append(self.bg)
        except Exception as e:
            print(f"Не удалось загрузить фон: {e}")
            self.bg = None

        # Диалог
        self.dialogue_index = 0  # Начинаем с "..."
        self.show_choices = False
        self.chosen_index = -1

        # Кнопки выбора ответа
        self.choice_buttons = []
        for i, text in enumerate(CHOICES):
            btn = ChoiceButton(0, 0, 700, 50, text)
            btn.on_click = lambda idx=i: self.on_choice(idx)
            self.choice_buttons.append(btn)

        # Анимация
        self.fade_alpha = 255
        self.fading_in = True
        self.time = 0.0

        self.hover_progress = 0.0

    def _position_elements(self, width, height):
        if self.bg:
            self.bg.center_x = width / 2
            self.bg.center_y = height / 2
            self.bg.width = width
            self.bg.height = height
        # Позиция кнопок выбора (по центру, друг под другом)
        for i, btn in enumerate(self.choice_buttons):
            btn.center_x = width / 2
            btn.center_y = height * 0.32 - i * 65
        self.menu_button.center_x = 150
        self.menu_button.center_y = 60

        self.next_button.center_x = width - 150
        self.next_button.center_y = 60

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self._position_elements(width, height)

    def on_show_view(self):
        arcade.set_background_color((20, 22, 28))
        self._position_elements(self.window.width, self.window.height)
        self.fade_alpha = 255
        self.fading_in = True
        self.phase_finished = False

    def on_update(self, delta_time):
        self.time += delta_time

        if self.fading_in:
            self.fade_alpha -= delta_time * 300
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fading_in = False

        if self.phase_finished:
            if self.fade_alpha < 255:
                self.fade_alpha += delta_time * 350  # Увеличиваем черноту
            if self.fade_alpha > 255:
                self.fade_alpha = 255

        if self.show_choices:
            for btn in self.choice_buttons:
                btn.update(delta_time)
        if self.phase_finished and self.fade_alpha >= 250:
            self.menu_button.update(delta_time)
            self.next_button.update(delta_time)

    def _advance_dialogue(self):
        """Продвинуть диалог на следующую реплику"""
        if self.dialogue_index < len(DIALOGUE) - 1:
            self.dialogue_index += 1
        else:
            # Последняя реплика — показываем выбор ответа
            self.show_choices = True

    def on_choice(self, index):
        self.chosen_index = index
        choice_text = CHOICES[index]
        print(f"Выбран ответ: {index}")
        self.phase_finished = True

    def _draw_dialog_box(self, w, h):
        """Рисуем окно диалога внизу экрана"""
        box_w = w * 0.85
        box_h = 140
        box_x = w / 2
        box_y = box_h / 2 + 30

        # Фон окна диалога
        points = _rounded_rect_points(box_x, box_y, box_w, box_h, 14)
        arcade.draw_polygon_filled(points, (20, 22, 30, 210))
        arcade.draw_polygon_outline(points, (90, 90, 100, 150), 1)

        speaker, text = DIALOGUE[self.dialogue_index]

        if speaker is None:
            # Три точки (начальное состояние)
            dots_alpha = int(180 + 75 * math.sin(self.time * 3))
            arcade.draw_text(
                ". . .",
                box_x, box_y, (200, 200, 205, dots_alpha),
                font_size=28,
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="center", anchor_y="center",
            )
        else:
            # Имя говорящего
            name_x = box_x - box_w / 2 + 30
            name_y = box_y + box_h / 2 - 30

            if speaker == "Начальник":
                name_color = (200, 180, 120, 255)
            else:
                name_color = (130, 180, 220, 255)

            arcade.draw_text(
                speaker, name_x, name_y, name_color,
                font_size=18,
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="left", anchor_y="center", bold=True,
            )

            # Текст реплики
            arcade.draw_text(
                text, name_x, name_y - 35,
                (220, 220, 225, 255),
                font_size=16,
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="left", anchor_y="center",
                multiline=True, width=int(box_w - 60),
            )

        # Подсказка "нажмите для продолжения" (мигающая)
        if not self.show_choices:
            hint_alpha = int(100 + 80 * math.sin(self.time * 2.5))
            arcade.draw_text(
                "Нажмите, чтобы продолжить",
                box_x + box_w / 2 - 20, box_y - box_h / 2 + 15,
                (160, 160, 165, hint_alpha),
                font_size=15,
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="right", anchor_y="center",
            )

    def _draw_choices(self, w, h):
        """Рисуем заголовок и кнопки выбора ответа"""
        header_y = h * 0.38
        arcade.draw_text(
            "Выберите ответ:", w / 2, header_y,
            (255, 255, 255, 255),
            font_size=30,
            font_name=("Garamond", "Palatino Linotype", "Georgia"),
            anchor_x="center", anchor_y="center",
        )
        for btn in self.choice_buttons:
            btn.draw()

    def on_draw(self):
        self.clear()
        w = self.window.width
        h = self.window.height

        # 1. Сначала рисуем базовый фон и диалоги (пока экран не стал совсем черным)
        if not self.phase_finished or self.fade_alpha < 255:
            self.background_list.draw()
            arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (0, 0, 0, 60))
            self._draw_dialog_box(w, h)
            if self.show_choices:
                self._draw_choices(w, h)

        # 2. Рисуем слой затемнения (Fade overlay)
        if self.fade_alpha > 0:
            arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (0, 0, 0, int(self.fade_alpha)))

        # 3. САМОЕ ВАЖНОЕ: Рисуем финал ПОВЕРХ черного слоя
        if self.phase_finished and self.fade_alpha >= 250:
            arcade.draw_text(
                "ФАЗА 1 ОКОНЧЕНА",
                w / 2, h * 0.8,
                arcade.color.GOLD,
                font_size=40,
                anchor_x="center",
                font_name=("Garamond", "Palatino Linotype", "Georgia")
            )
            self.menu_button.draw()
            self.next_button.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        if self.phase_finished and self.fade_alpha >= 250:
            self.menu_button.check_hover(x, y)
            self.next_button.check_hover(x, y)
        if self.show_choices:
            for btn in self.choice_buttons:
                btn.check_hover(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.phase_finished and self.fade_alpha >= 250:
                self.menu_button.check_press(x, y)
                self.next_button.check_press(x, y)
            elif self.show_choices:
                for btn in self.choice_buttons:
                    btn.check_click(x, y)
            else:
                self._advance_dialogue()

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.phase_finished and self.fade_alpha >= 250:
                self.menu_button.check_release(x, y)
                self.next_button.check_release(x, y)

    def go_to_menu(self):
        menu = StartView()
        self.window.show_view(menu)

    def go_to_next_phase(self):
        print("Переход к Фазе 2: Дмитрий Частичная Автоматизация")
