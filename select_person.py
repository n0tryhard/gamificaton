import arcade
import math

from start import Button

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720


class CharacterCard:
    """Карточка персонажа с портретом, именем, ролью и фазами дня"""
    def __init__(self, center_x, center_y, name, role, image_path, phases):
        self.center_x = center_x
        self.center_y = center_y
        self.name = name
        self.role = role
        self.phases = phases  # список кортежей (время, описание)
        self.card_width = 420
        self.card_height = 740
        self.corner_radius = 14

        self.portrait_list = arcade.SpriteList()
        try:
            self.portrait = arcade.Sprite(image_path)
            self.portrait_list.append(self.portrait)
        except Exception as e:
            print(f"Не удалось загрузить портрет {name}: {e}")
            self.portrait = None

        self.hovered = False
        self.selected = False
        self.hover_progress = 0.0
        self.select_progress = 0.0

    def update(self, delta_time):
        target_hover = 1.0 if self.hovered else 0.0
        self.hover_progress += (target_hover - self.hover_progress) * 6.0 * delta_time
        target_select = 1.0 if self.selected else 0.0
        self.select_progress += (target_select - self.select_progress) * 5.0 * delta_time

    def _lerp_color(self, c1, c2, t):
        return tuple(max(0, min(255, int(a + (b - a) * t))) for a, b in zip(c1, c2))

    def _rounded_rect_points(self, cx, cy, w, h, radius):
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

    def draw(self):
        t = self.hover_progress
        s = self.select_progress
        scale = 1.0 + 0.02 * t
        w = self.card_width * scale
        h = self.card_height * scale

        bg_color = self._lerp_color((35, 35, 40, 220), (50, 50, 55, 240), t)
        border_normal = (100, 100, 105, 120)
        border_gold = (200, 180, 120, 255)
        border_color = self._lerp_color(border_normal, border_gold, max(t, s))
        border_width = 1 + int(2 * s)

        points = self._rounded_rect_points(self.center_x, self.center_y, w, h, self.corner_radius * scale)
        arcade.draw_polygon_filled(points, bg_color)
        arcade.draw_polygon_outline(points, border_color, border_width)

        # Портрет
        if self.portrait:
            portrait_size = 280 * scale
            self.portrait.center_x = self.center_x
            self.portrait.center_y = self.center_y + h / 2 - 20 * scale - portrait_size / 2
            self.portrait.width = portrait_size
            self.portrait.height = portrait_size
            self.portrait_list.draw()

        # Имя
        name_y = self.center_y + h / 2 - 20 * scale - 280 * scale - 22 * scale
        name_color = self._lerp_color((210, 210, 215, 255), (255, 250, 240, 255), t)
        arcade.draw_text(
            self.name, self.center_x, name_y, name_color,
            font_size=int(30 * scale),
            font_name=("Garamond", "Palatino Linotype", "Georgia"),
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Роль
        role_y = name_y - 37 * scale
        arcade.draw_text(
            self.role, self.center_x, role_y, (160, 158, 150, 200),
            font_size=int(16 * scale),
            font_name=("Garamond", "Palatino Linotype", "Georgia"),
            anchor_x="center", anchor_y="center",
            bold=True,
        )

        # Разделитель
        sep_y = role_y - 16 * scale
        arcade.draw_line(
            self.center_x - w * 0.35, sep_y,
            self.center_x + w * 0.35, sep_y,
            (100, 95, 80, 80), 1
        )

        # Заголовок "ФАЗЫ ДНЯ"
        phases_header_y = sep_y - 30 * scale
        arcade.draw_text(
            "ФАЗЫ ДНЯ", self.center_x, phases_header_y, (180, 165, 115, 200),
            font_size=int(18 * scale),
            font_name=("Garamond", "Palatino Linotype", "Georgia"),
            anchor_x="center", anchor_y="center",
            bold=True,
        )

        # Фазы
        phase_y = phases_header_y - 30 * scale
        
        for idx, (time_label, desc) in enumerate(self.phases):
            arcade.draw_text(
                f"{time_label}:", self.center_x - w * 0.38, phase_y,
                (200, 185, 130, 255),
                font_size=int(17 * scale),
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="left", anchor_y="top", bold=True,
            )
            arcade.draw_text(
                desc,
                self.center_x - w * 0.38 + 65 * scale, phase_y,
                (180, 180, 185, 220),
                font_size=int(15 * scale),
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="left", anchor_y="top",
                multiline=True, width=int(w * 0.6),
                bold=True,
            )
            
            phase_y -= 75 * scale


    def check_hover(self, x, y):
        half_w = self.card_width / 2
        half_h = self.card_height / 2
        self.hovered = (self.center_x - half_w <= x <= self.center_x + half_w and
                        self.center_y - half_h <= y <= self.center_y + half_h)
        return self.hovered

    def check_click(self, x, y):
        return self.check_hover(x, y)


# Данные персонажей
CHARACTERS = [
    {
        "name": "Дмитрий",
        "role": "Менеджер по работе с клиентами",
        "image": "дмитрий.png",
        "phases": [
            ("Утро", "Звонок начальника о новой системе — выбор ответа"),
            ("День", "Встреча с клиентами, подпись документов по таймеру"),
            ("Вечер", " Сканирование документов, заполнение базы данных"),
        ],
    },
    {
        "name": "Константин",
        "role": "Специалист по документообороту",
        "image": "константин.png",
        "phases": [
            ("Утро", "Распределение документов по отделам — сортировка"),
            ("День", "Работа с базой CRM по клиентским документам"),
            ("Вечер", " Пересылка отчётов между отделами"),
        ],
    },
]


class SelectPersonView(arcade.View):
    """Экран выбора персонажа"""
    def __init__(self):
        super().__init__()

        self.cards = []
        for data in CHARACTERS:
            card = CharacterCard(0, 0, data["name"], data["role"],
                                 data["image"], data["phases"])
            self.cards.append(card)

        # Кнопка подтверждения
        self.confirm_button = Button(0, 0, 300, 55, "ПОДТВЕРДИТЬ", font_size=20)
        self.confirm_button.on_click = self.on_confirm
        self.confirm_button.bg_normal = (55, 50, 35, 200)
        self.confirm_button.bg_hover = (80, 72, 45, 230)
        self.confirm_button.bg_press = (65, 58, 38, 255)
        self.confirm_button.border_normal = (180, 160, 100, 150)
        self.confirm_button.border_hover = (220, 200, 140, 220)
        self.confirm_button.text_normal = (200, 185, 130, 255)
        self.confirm_button.text_hover = (255, 240, 180, 255)

        # Кнопка "Назад"
        self.back_button = Button(0, 0, 200, 45, "НАЗАД", font_size=18)
        self.back_button.on_click = self.on_back

        self.selected_index = -1
        self.fade_alpha = 255
        self.fading_in = True
        self.fading_out = False
        self.fade_target = None
        self.time = 0.0

    def _position_elements(self, width, height):
        spacing = 300
        for i, card in enumerate(self.cards):
            card.center_x = width / 2 + (i - 0.5) * spacing * 2
            card.center_y = height / 2

        self.confirm_button.center_x = width / 2
        self.confirm_button.center_y = height * 0.08
        self.back_button.center_x = 160
        self.back_button.center_y = height * 0.08

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self._position_elements(width, height)

    def on_show_view(self):
        arcade.set_background_color((30, 30, 35))
        self._position_elements(self.window.width, self.window.height)
        self.fade_alpha = 255
        self.fading_in = True

    def on_update(self, delta_time):
        self.time += delta_time

        if self.fading_in:
            self.fade_alpha -= delta_time * 300
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fading_in = False

        if self.fading_out:
            self.fade_alpha += delta_time * 350
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                if self.fade_target == "start":
                    from start import StartView
                    self.window.show_view(StartView())
                elif self.fade_target == "dmitry_phase1":
                    from _1_phase_dm import Phase1DmView
                    self.window.show_view(Phase1DmView())
                elif self.fade_target == "konstantin_phase1":
                    from _1_phase_ko import Phase1KoView
                    self.window.show_view(Phase1KoView())

        for card in self.cards:
            card.update(delta_time)
        self.confirm_button.update(delta_time)
        self.back_button.update(delta_time)

    def on_confirm(self):
        if self.selected_index >= 0 and not self.fading_out:
            name = self.cards[self.selected_index].name
            if name == "Дмитрий":
                self.fading_out = True
                self.fade_target = "dmitry_phase1"
            elif name == "Константин":
                self.fading_out = True
                self.fade_target = "konstantin_phase1"

    def on_back(self):
        if not self.fading_out:
            self.fading_out = True
            self.fade_target = "start"

    def _draw_gold_decorations(self, w, h):
        pulse = 0.7 + 0.3 * math.sin(self.time * 1.2)
        gold_alpha = int(70 * pulse)
        gold = (180, 160, 100, gold_alpha)

        # Рамка по краям
        margin = 45
        arcade.draw_line(margin, margin, w - margin, margin, gold, 2)
        arcade.draw_line(margin, h - margin, w - margin, h - margin, gold, 2)
        arcade.draw_line(margin, margin, margin, h - margin, gold, 2)
        arcade.draw_line(w - margin, margin, w - margin, h - margin, gold, 2)

        # Ромбы по углам рамки
        diamond_size = 10
        for dx, dy in [(margin, margin), (w - margin, margin),
                       (margin, h - margin), (w - margin, h - margin)]:
            pts = [(dx, dy + diamond_size), (dx + diamond_size, dy),
                   (dx, dy - diamond_size), (dx - diamond_size, dy)]
            arcade.draw_polygon_filled(pts, (200, 180, 120, int(120 * pulse)))

        # Вертикальные линии по бокам
        v_margin = 100
        arcade.draw_line(margin, v_margin, margin, h - v_margin, gold, 2)
        arcade.draw_line(w - margin, v_margin, w - margin, h - v_margin, gold, 2)

    def on_draw(self):
        self.clear()
        w = self.window.width
        h = self.window.height

        arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (35, 35, 40, 255))
        self._draw_gold_decorations(w, h)

        title_y = h * 0.93
        arcade.draw_text(
            "ВЫБЕРИТЕ ПЕРСОНАЖА", w / 2, title_y, (220, 200, 150, 255),
            font_size=42,
            font_name=("Garamond", "Palatino Linotype", "Georgia"),
            anchor_x="center", anchor_y="center",
        )

        pulse = 0.85 + 0.15 * math.sin(self.time * 1.5)
        line_alpha = int(100 * pulse)
        arcade.draw_line(w / 2 - 180, title_y - 30, w / 2 + 180, title_y - 30,
                         (180, 160, 100, line_alpha), 1)

        for card in self.cards:
            card.draw()

        if self.selected_index >= 0:
            self.confirm_button.draw()
        self.back_button.draw()

        if self.fade_alpha > 0:
            arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (0, 0, 0, int(self.fade_alpha)))

    def on_mouse_motion(self, x, y, dx, dy):
        for card in self.cards:
            card.check_hover(x, y)
        self.confirm_button.check_hover(x, y)
        self.back_button.check_hover(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for i, card in enumerate(self.cards):
                if card.check_click(x, y):
                    for c in self.cards:
                        c.selected = False
                    card.selected = True
                    self.selected_index = i
            self.confirm_button.check_press(x, y)
            self.back_button.check_press(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.confirm_button.check_release(x, y)
            self.back_button.check_release(x, y)
