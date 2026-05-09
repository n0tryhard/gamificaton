import arcade
import math
import random
import os
import tempfile
from start import Button
from PIL import Image
from start import StartView

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
# Загрузка документов как изображений
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "_cache")


def _render_doc_to_images(doc_name, dpi_scale=2.0):
    """Конвертирует документ в список PNG-изображений (страниц).
    Возвращает список путей к PNG файлам."""
    # Создаём кэш-директорию
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Проверяем кэш
    cache_pattern = os.path.join(CACHE_DIR, doc_name + "_page_")
    existing = sorted([f for f in os.listdir(CACHE_DIR) if f.startswith(doc_name + "_page_") and f.endswith(".png")])
    if existing:
        return [os.path.join(CACHE_DIR, f) for f in existing]

    # Ищем PDF файл
    pdf_path = os.path.join(DOCS_DIR, doc_name + ".pdf")
    if not os.path.exists(pdf_path):
        print(f"Файл документа '{doc_name}.pdf' не найден в {DOCS_DIR}")
        return []

    try:
        # Рендерим PDF в изображения через PyMuPDF
        import fitz
        pdf = fitz.open(pdf_path)
        result = []
        mat = fitz.Matrix(dpi_scale, dpi_scale)
        for i, page in enumerate(pdf):
            pix = page.get_pixmap(matrix=mat)
            img_path = os.path.join(CACHE_DIR, f"{doc_name}_page_{i:02d}.png")
            pix.save(img_path)
            result.append(img_path)
        pdf.close()

        print(f"Документ '{doc_name}' — {len(result)} стр.")
        return result

    except Exception as e:
        print(f"Ошибка рендеринга '{doc_name}': {e}")
        return []


# ─── Данные документов ────────────────────────────────────────────────
# (название, правильный отдел)
DOCUMENTS = [
    ("Договор поставки запчастей №127", "Юридический"),
    ("Расчётный лист за март 2025", "Финансы"),
    ("Заявление на отпуск — Иванов А.С.", "HR"),
    ("Коммерческое предложение AutoParts", "Продажи"),
    ("Акт приёма-передачи автомобиля", "Юридический"),
    ("Счёт-фактура №0892", "Финансы"),
    ("Резюме — кандидат на менеджера", "HR"),
    ("Заявка на тест-драйв от клиента", "Продажи"),
    ("Допсоглашение к трудовому договору", "Юридический"),
    ("Отчёт о продажах за I квартал", "Продажи"),
    ("Табель учёта рабочего времени", "HR"),
    ("Претензия по гарантийному случаю", "Юридический"),
    ("Платёжное поручение №415", "Финансы"),
    ("Заявка на подбор персонала", "HR"),
    ("Накладная на приход автомобилей", "Финансы"),
    ("Договор купли-продажи ТС №304", "Продажи"),
]

DOC_REASONS = {
    "Договор поставки запчастей №127": "Это договор, он требует обязательной правовой экспертизы в Юридическом отделе.",
    "Расчётный лист за март 2025": "Расчётные листы содержат информацию по зарплате. Их обрабатывают Финансы.",
    "Заявление на отпуск — Иванов А.С.": "Все заявления сотрудников, включая отпуска, находятся в ведении HR.",
    "Коммерческое предложение AutoParts": "Взаимодействие с клиентами и коммерческие предложения — задача отдела Продаж.",
    "Акт приёма-передачи автомобиля": "Акты приёма-передачи — это юридические документы, подтверждающие переход прав.",
    "Счёт-фактура №0892": "Счета-фактуры используются для налогового и бухгалтерского учёта (Финансы).",
    "Резюме — кандидат на менеджера": "Подбором и наймом новых сотрудников занимается исключительно HR.",
    "Заявка на тест-драйв от клиента": "Обработка заявок от клиентов — прямая обязанность отдела Продаж.",
    "Допсоглашение к трудовому договору": "Любые изменения в договорах, включая трудовые, требуют юридического оформления.",
    "Отчёт о продажах за I квартал": "Статистика и аналитика продаж направляется руководителю отдела Продаж.",
    "Табель учёта рабочего времени": "Контроль за отработанным временем сотрудников ведёт HR-отдел.",
    "Претензия по гарантийному случаю": "Претензии могут вести к судебным разбирательствам. Ими занимается Юридический отдел.",
    "Платёжное поручение №415": "Платежные поручения связаны с движением денежных средств (Финансы).",
    "Заявка на подбор персонала": "Рекрутинг и поиск новых кадров — функция HR.",
    "Накладная на приход автомобилей": "Накладные фиксируют поступление активов для бухгалтерского баланса в Финансах.",
    "Договор купли-продажи ТС №304": "Оформлением сделок с клиентами занимается отдел Продаж."
}

DEPARTMENTS = ["Продажи", "Юридический", "Финансы", "HR"]

# ─── Состояния анимации ───────────────────────────────────────────────
STATE_IDLE = 0  # Ничего не открыто
STATE_OPENING = 1  # Документ раскрывается
STATE_OPEN = 2  # Документ открыт, ждём выбор отдела
STATE_FLYING = 3  # Документ летит в отдел
STATE_GAME_OVER = 4  # Увольнение (3 ошибки)


def _rounded_rect_points(cx, cy, w, h, radius):
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


def _lerp(a, b, t):
    return a + (b - a) * t


def _ease_out_back(t):
    """Easing для 'пружинящего' эффекта открытия"""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def _ease_in_quad(t):
    return t * t


class Phase1KoView(arcade.View):
    """Первая фаза Константина — сортировка документов по отделам"""

    def __init__(self):
        super().__init__()

        # Фон
        self.background_list = arcade.SpriteList()
        try:
            self.bg = arcade.Sprite("стол константина.png")
            self.background_list.append(self.bg)
        except Exception as e:
            print(f"Не удалось загрузить фон: {e}")
            self.bg = None

        # Перемешиваем документы и берём 10
        shuffled = list(DOCUMENTS)
        random.shuffle(shuffled)
        self.doc_queue = shuffled[:10]
        self.current_doc_index = 0
        self.correct_count = 0
        self.mistakes = 0
        self.total_sorted = 0

        self.notification = None  # Сюда пишем {'text': ..., 'color': ..., 'timer': ...}

        # Состояние анимации
        self.state = STATE_IDLE
        self.anim_progress = 0.0  # 0→1

        # Координаты для анимации полёта
        self.fly_start_x = 0
        self.fly_start_y = 0
        self.fly_target_x = 0
        self.fly_target_y = 0
        self.fly_correct = False

        # Позиции элементов
        self.doc_list_x = 0
        self.doc_list_y = 0
        self.dept_buttons = []
        self.dept_positions = {}

        # Hover-состояния
        self.hovered_doc = -1
        self.hovered_dept = -1

        # Содержимое открытого документа (страницы как текстуры)
        self.page_textures = []  # список arcade.Texture
        self.page_heights = []  # высоты страниц в пикселях (масштабированные)
        self.total_doc_height = 0
        self.scroll_offset = 0.0
        self.max_scroll = 0.0

        # Fade
        self.fade_alpha = 255
        self.fading_in = True
        self.time = 0.0

        # Окончание фазы

        self.menu_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 100, 250, 60, "В ГЛАВНОЕ МЕНЮ")
        self.next_button = Button(SCREEN_WIDTH // 2 + 150, SCREEN_HEIGHT // 2 - 100, 250, 60, "ДАЛЕЕ")
        self.menu_button.on_click = self.go_to_menu
        self.next_button.on_click = self.go_to_next_phase
        self.phase_finished = False
        self.end_delay_timer = 2.0

    def _position_elements(self, width, height):
        if self.bg:
            self.bg.center_x = width / 2
            self.bg.center_y = height / 2
            self.bg.width = width
            self.bg.height = height

        # --- НОВАЯ ЛОГИКА ДЛЯ ПРАВОЙ ПАНЕЛИ ---
        # Панель будет занимать 18% экрана справа
        panel_w = width * 0.18
        dept_x = width - panel_w / 2

        # Распределяем кнопки по вертикали и центрируем весь блок
        dept_spacing = 90
        total_h = (len(DEPARTMENTS) - 1) * dept_spacing
        dept_start_y = (height / 2) + (total_h / 2)

        self.dept_positions = {}
        for i, dept in enumerate(DEPARTMENTS):
            y = dept_start_y - i * dept_spacing
            self.dept_positions[dept] = (dept_x, y)

        self.menu_button.center_x = 150
        self.menu_button.center_y = 60

        self.next_button.center_x = width - 150
        self.next_button.center_y = 60

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self._position_elements(width, height)

    def on_show_view(self):
        arcade.set_background_color((25, 25, 30))
        self._position_elements(self.window.width, self.window.height)
        self.fade_alpha = 255
        self.fading_in = True
        self.phase_finished = False

    def on_update(self, delta_time):
        self.time += delta_time

        # Fade in
        if self.fading_in:
            self.fade_alpha -= delta_time * 300
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fading_in = False

        # Обновляем таймер уведомления
        if self.notification:
            self.notification["timer"] -= delta_time
            if self.notification["timer"] <= 0:
                self.notification = None

        # Анимация открытия документа
        if self.state == STATE_OPENING:
            self.anim_progress += delta_time * 1.5
            if self.anim_progress >= 1.0:
                self.anim_progress = 1.0
                self.state = STATE_OPEN

        # Анимация полёта документа в отдел
        elif self.state == STATE_FLYING:
            self.anim_progress += delta_time * 3.0
            if self.anim_progress >= 1.0:
                self.anim_progress = 1.0
                self._finish_sort()

        if self.phase_finished:
            if self.end_delay_timer > 0:
                # Сначала просто ждем, чтобы игрок прочитал надпись
                self.end_delay_timer -= delta_time
            else:
                if self.fade_alpha < 255:
                    self.fade_alpha += delta_time * 350  # Увеличиваем черноту
                if self.fade_alpha > 255:
                    self.fade_alpha = 255
        if self.phase_finished and self.fade_alpha >= 250:
            self.menu_button.update(delta_time)
            self.next_button.update(delta_time)

    def _open_document(self, index):
        """Открыть документ из списка"""
        if self.state != STATE_IDLE:
            return
        if index < 0 or index >= len(self.doc_queue):
            return
        self.current_doc_index = index
        self.state = STATE_OPENING
        self.anim_progress = 0.0
        self.scroll_offset = 0.0

        # Загружаем страницы документа как изображения
        doc_name = self.doc_queue[index][0]
        image_paths = _render_doc_to_images(doc_name)
        self.page_textures = []
        self.page_heights = []
        self.total_doc_height = 0

        # Определяем ширину: альбомные одностраничные — хр2, остальные — х1.5
        is_landscape_single = False
        if len(image_paths) > 0:
            try:
                test_tex = arcade.load_texture(image_paths[0])
                if test_tex.width > test_tex.height:
                    is_landscape_single = True
            except Exception:
                pass
        display_width = 1100 if is_landscape_single else 840
        self.doc_display_width = display_width

        for img_path in image_paths:
            try:
                tex = arcade.load_texture(img_path)
                ratio = display_width / tex.width
                page_h = tex.height * ratio
                self.page_textures.append(tex)
                self.page_heights.append(page_h)
                self.total_doc_height += page_h + 8
            except Exception as e:
                print(f"Ошибка загрузки страницы: {e}")

    def _send_to_department(self, dept_name):
        """Отправить открытый документ в отдел"""
        if self.state != STATE_OPEN:
            return

        w = self.window.width
        h = self.window.height

        doc_name, correct_dept = self.doc_queue[self.current_doc_index]
        self.fly_correct = (dept_name == correct_dept)

        # Начальная позиция — центр экрана
        self.fly_start_x = w / 2
        self.fly_start_y = h / 2

        # Конечная позиция — кнопка отдела
        tx, ty = self.dept_positions.get(dept_name, (w / 2, h / 2))
        self.fly_target_x = tx
        self.fly_target_y = ty

        self.state = STATE_FLYING
        self.anim_progress = 0.0

    def _finish_sort(self):
        """Завершить сортировку текущего документа"""
        doc_name, _ = self.doc_queue[self.current_doc_index]

        if self.fly_correct:
            self.correct_count += 1
            self.notification = {
                "text": "Верно! Документ передан в нужный отдел.",
                "color": (80, 220, 100, 255),
                "timer": 3.5
            }
        else:
            self.mistakes += 1
            reason = DOC_REASONS.get(doc_name, "Вы ошиблись отделом.")
            self.notification = {
                "text": f"Ошибка!\n{reason}",
                "color": (220, 80, 80, 255),
                "timer": 4.5
            }

        self.total_sorted += 1

        # Удаляем документ из очереди
        self.doc_queue.pop(self.current_doc_index)
        self.current_doc_index = 0

        if self.mistakes >= 3:
            self.state = STATE_GAME_OVER
        else:
            self.state = STATE_IDLE
        self.anim_progress = 0.0

    # ─── Отрисовка ────────────────────────────────────────────────────

    def _draw_doc_list(self, w, h):
        """Рисуем список документов слева"""
        list_x = w * 0.18
        list_top = h * 0.82

        # 1. СНАЧАЛА РИСУЕМ ФОН (чтобы он был под текстом)
        # Увеличиваем базовую высоту (+80 вместо +20) 
        # и чуть увеличиваем лимит высоты экрана (до h * 0.75)
        panel_h = min(len(self.doc_queue) * 52 + 80, h * 0.75)

        # Сдвигаем центр рамки ВВЕРХ (+55), чтобы она накрыла заголовок 
        # и дала красивый отступ над первой кнопкой
        pts = _rounded_rect_points(list_x, list_top - panel_h / 2 + 55, w * 0.28, panel_h, 12)

        arcade.draw_polygon_filled(pts, (25, 27, 35, 200))
        arcade.draw_polygon_outline(pts, (80, 80, 85, 120), 1)

        # 2. ПОТОМ РИСУЕМ ЗАГОЛОВОК (теперь он красиво сидит внутри рамки)
        arcade.draw_text(
            "ДОКУМЕНТЫ", list_x, list_top + 30,
            (200, 185, 130, 255), font_size=20,
            font_name=("Garamond", "Palatino Linotype", "Georgia"),
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Документы
        for i, (doc_name, _) in enumerate(self.doc_queue):
            y = list_top - 20 - i * 52
            item_w = w * 0.26
            item_h = 44

            # Подсветка при наведении
            if self.hovered_doc == i and self.state == STATE_IDLE:
                bg = (55, 55, 60, 200)
                text_col = (255, 250, 240, 255)
                border_col = (180, 165, 115, 150)
            else:
                bg = (38, 40, 48, 180)
                text_col = (200, 200, 205, 255)
                border_col = (70, 70, 75, 80)

            pts = _rounded_rect_points(list_x, y, item_w, item_h, 8)
            arcade.draw_polygon_filled(pts, bg)
            arcade.draw_polygon_outline(pts, border_col, 1)

            arcade.draw_text(
                doc_name, list_x - item_w / 2 + 14, y,
                text_col, font_size=20,
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="left", anchor_y="center",
            )

    def _draw_departments(self, w, h):
        """Рисуем отделы как боковую панель во всю высоту экрана"""
        panel_w = w * 0.18
        dept_x = w - panel_w / 2

        # Сплошной фон во всю высоту экрана (альфа 255 - полностью непрозрачный)
        arcade.draw_lbwh_rectangle_filled(w - panel_w, 0, panel_w, h, (25, 27, 35, 255))
        # Левая разделительная линия
        arcade.draw_line(w - panel_w, 0, w - panel_w, h, (80, 80, 85, 150), 2)

        # Заголовок (фиксируем в верхней части экрана)
        arcade.draw_text(
            "ОТДЕЛЫ", dept_x, h * 0.9,
            (200, 185, 130, 255), font_size=30,
            font_name=("Garamond", "Palatino Linotype", "Georgia"),
            anchor_x="center", anchor_y="center", bold=True,
        )

        for i, dept in enumerate(DEPARTMENTS):
            dx, dy = self.dept_positions[dept]
            btn_w = panel_w * 0.85  # Кнопки занимают 85% от ширины панели
            btn_h = 70

            # Подсветка
            if self.hovered_dept == i and self.state == STATE_OPEN:
                bg = (55, 50, 40, 220)
                text_col = (255, 250, 240, 255)
                border_col = (200, 180, 120, 200)
            else:
                bg = (35, 37, 45, 200)
                text_col = (200, 200, 205, 255)
                border_col = (80, 80, 85, 100)

            pts = _rounded_rect_points(dx, dy, btn_w, btn_h, 10)
            arcade.draw_polygon_filled(pts, bg)
            arcade.draw_polygon_outline(pts, border_col, 1)

            arcade.draw_text(
                dept, dx, dy,
                text_col, font_size=24,
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="center", anchor_y="center", bold=True,
            )

    def _draw_open_document(self, w, h):  # тут остановился
        """Рисуем открытый документ как оригинальное изображение Word-страниц"""
        if self.state == STATE_OPENING:
            t = _ease_out_back(min(self.anim_progress, 1.0))
        elif self.state == STATE_OPEN:
            t = 1.0
        else:
            return

        doc_name = self.doc_queue[self.current_doc_index][0]
        scale = min(t, 1.0)
        viewer_w = 900 * scale
        viewer_h = h * 0.88 * scale
        cx = w / 2
        cy = h / 2

        # Затемнение фона
        arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (0, 0, 0, min(255, int(170 * scale))))

        if scale < 0.3 or not self.page_textures:
            if scale >= 0.3 and not self.page_textures:
                arcade.draw_text(
                    f"Не удалось загрузить: {doc_name}", cx, cy,
                    (200, 200, 205, 200), font_size=16,
                    font_name=("Garamond", "Palatino Linotype", "Georgia"),
                    anchor_x="center", anchor_y="center",
                )
            return

        # Область просмотра
        view_top = cy + viewer_h / 2
        view_bottom = cy - viewer_h / 2 + 30 * scale
        view_height = view_top - view_bottom
        display_width = getattr(self, 'doc_display_width', 840) * scale
        page_gap = 8 * scale

        # Прокрутка
        self.max_scroll = max(0, self.total_doc_height * scale - view_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

        # Рисуем страницы
        y_cursor = view_top + self.scroll_offset
        for tex, page_h in zip(self.page_textures, self.page_heights):
            scaled_h = page_h * scale
            y_cursor -= scaled_h

            page_top = y_cursor + scaled_h
            if page_top < view_bottom - 50 or y_cursor > view_top + 50:
                y_cursor -= page_gap
                continue

            page_cx = cx
            page_cy = y_cursor + scaled_h / 2

            # Тень
            arcade.draw_lbwh_rectangle_filled(
                page_cx - display_width / 2 + 3,
                page_cy - scaled_h / 2 - 3,
                display_width, scaled_h,
                (0, 0, 0, int(40 * scale))
            )
            # Белая страница
            arcade.draw_lbwh_rectangle_filled(
                page_cx - display_width / 2,
                page_cy - scaled_h / 2,
                display_width, scaled_h,
                (255, 255, 255, 255)
            )
            # Содержимое (текстура)
            arcade.draw_texture_rect(
                tex,
                arcade.LBWH(
                    page_cx - display_width / 2,
                    page_cy - scaled_h / 2,
                    display_width, scaled_h
                ),
            )
            y_cursor -= page_gap

        # Скроллбар
        if self.max_scroll > 0 and self.state == STATE_OPEN:
            bar_x = cx + viewer_w / 2 - 6
            bar_h = view_height
            thumb_h = max(20, bar_h * (view_height / (view_height + self.max_scroll)))
            thumb_y = view_top - (self.scroll_offset / self.max_scroll) * (bar_h - thumb_h)
            arcade.draw_line(bar_x, view_top, bar_x, view_top - bar_h, (100, 100, 105, 60), 2)
            arcade.draw_line(bar_x, thumb_y, bar_x, thumb_y - thumb_h, (180, 165, 115, 180), 4)

        # Подсказка
        pulse = 0.8 + 0.2 * math.sin(self.time * 2.5)

    def _draw_flying_document(self, w, h):
        """Рисуем документ, летящий в отдел"""
        if self.state != STATE_FLYING:
            return

        t = _ease_in_quad(self.anim_progress)
        scale = 1.0 - t * 0.85  # Уменьшается

        cx = _lerp(self.fly_start_x, self.fly_target_x, t)
        cy = _lerp(self.fly_start_y, self.fly_target_y, t)

        doc_w = 420 * scale
        doc_h = 280 * scale
        alpha = int(255 * (1.0 - t * 0.5))

        # Цвет рамки: зелёный если правильно, красный если нет
        if self.fly_correct:
            border = (100, 200, 120, alpha)
        else:
            border = (200, 100, 100, alpha)

        pts = _rounded_rect_points(cx, cy, doc_w, doc_h, 14 * scale)
        arcade.draw_polygon_filled(pts, (40, 42, 52, int(200 * (1.0 - t * 0.7))))
        arcade.draw_polygon_outline(pts, border, 2)

        doc_name = self.doc_queue[self.current_doc_index][0]
        if scale > 0.2:
            arcade.draw_text(
                doc_name, cx, cy,
                (240, 238, 230, int(alpha * 0.8)),
                font_size=max(8, int(18 * scale)),
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="center", anchor_y="center", bold=True,
                multiline=True, width=max(50, int(doc_w * 0.85)),
            )

    def _draw_score(self, w, h):
        """Счётчик прогресса"""
        remaining = len(self.doc_queue)
        arcade.draw_text(
            f"Осталось: {remaining}  |  Ошибки: {self.mistakes}/3",
            w / 2, h * 0.96,
            (255, 255, 255, 255), font_size=18,
            font_name=("Garamond", "Palatino Linotype", "Georgia"),
            anchor_x="center", anchor_y="center",
        )

        # Результат когда всё отсортировано
        if remaining == 0 and self.state == STATE_IDLE:
            self.phase_finished = True
            arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (0, 0, 0, 150))
            arcade.draw_text(
                "СОРТИРОВКА ЗАВЕРШЕНА", w / 2, h / 2 + 30,
                (220, 200, 150, 255), font_size=38,
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="center", anchor_y="center", bold=True,
            )
            arcade.draw_text(
                f"Правильно: {self.correct_count} из {self.total_sorted}",
                w / 2, h / 2 - 30,
                (200, 200, 205, 255), font_size=20,
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="center", anchor_y="center",
            )

    def on_draw(self):
        self.clear()
        w = self.window.width
        h = self.window.height

        # Фон
        self.background_list.draw()
        arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (0, 0, 0, 80))

        # Список документов (слева)
        self._draw_doc_list(w, h)

        # Отделы (справа)
        self._draw_departments(w, h)

        # Счётчик
        self._draw_score(w, h)

        # Открытый документ (центр) или летящий документ
        if self.state != STATE_GAME_OVER:
            self._draw_open_document(w, h)
            self._draw_flying_document(w, h)

        # Отделы поверх документа (чтобы можно было отправить при просмотре)
        if self.state in (STATE_OPEN, STATE_OPENING):
            self._draw_departments(w, h)

        # Уведомление об ошибке / успехе
        if self.notification:
            text = self.notification["text"]
            color = self.notification["color"]
            alpha = min(255, int(self.notification["timer"] * 255))
            arcade.draw_text(
                text, w / 2, h * 0.15,
                      color[:3] + (alpha,), font_size=16,
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="center", anchor_y="center", bold=True,
                multiline=True, width=600, align="center"
            )

        # Экран увольнения
        if self.state == STATE_GAME_OVER:
            arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (0, 0, 0, 200))
            arcade.draw_text(
                "ВЫ УВОЛЕНЫ", w / 2, h / 2 + 20,
                (220, 80, 80, 255), font_size=42,
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="center", anchor_y="center", bold=True,
            )
            arcade.draw_text(
                "Допущено 3 критические ошибки при распределении документов.",
                w / 2, h / 2 - 30,
                (200, 200, 205, 255), font_size=18,
                font_name=("Garamond", "Palatino Linotype", "Georgia"),
                anchor_x="center", anchor_y="center",
            )
            self.phase_finished = True

        # Fade overlay
        if self.fade_alpha > 0:
            arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (0, 0, 0, int(self.fade_alpha)))
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

    # ─── Ввод ─────────────────────────────────────────────────────────

    def on_mouse_motion(self, x, y, dx, dy):
        w = self.window.width
        h = self.window.height
        if self.phase_finished and self.fade_alpha >= 250:
            self.menu_button.check_hover(x, y)
            self.next_button.check_hover(x, y)
            return
        # Проверяем наведение на документы
        self.hovered_doc = -1
        if self.state == STATE_IDLE:
            list_x = w * 0.18
            list_top = h * 0.82
            item_w = w * 0.26
            for i in range(len(self.doc_queue)):
                iy = list_top - 20 - i * 52
                if (list_x - item_w / 2 <= x <= list_x + item_w / 2 and
                        iy - 22 <= y <= iy + 22):
                    self.hovered_doc = i
                    break

        # Проверяем наведение на отделы
        self.hovered_dept = -1
        if self.state == STATE_OPEN:
            panel_w = w * 0.18
            btn_w = panel_w * 0.85
            btn_h = 70
            for i, dept in enumerate(DEPARTMENTS):
                dx_pos, dy_pos = self.dept_positions[dept]
                if (dx_pos - btn_w / 2 <= x <= dx_pos + btn_w / 2 and
                        dy_pos - btn_h / 2 <= y <= dy_pos + btn_h / 2):
                    self.hovered_dept = i
                    break

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        w = self.window.width
        h = self.window.height

        if self.phase_finished and self.fade_alpha >= 250:
            self.menu_button.check_press(x, y)
            self.next_button.check_press(x, y)
            return
        # Клик по документу из списка
        if self.state == STATE_IDLE and len(self.doc_queue) > 0:
            list_x = w * 0.18
            list_top = h * 0.82
            item_w = w * 0.26
            for i in range(len(self.doc_queue)):
                iy = list_top - 20 - i * 52
                if (list_x - item_w / 2 <= x <= list_x + item_w / 2 and
                        iy - 22 <= y <= iy + 22):
                    self._open_document(i)
                    return

        # Клик по отделу (когда документ открыт)
        if self.state == STATE_OPEN:
            panel_w = w * 0.18
            btn_w = panel_w * 0.85
            btn_h = 70
            for dept in DEPARTMENTS:
                dx_pos, dy_pos = self.dept_positions[dept]
                if (dx_pos - btn_w / 2 <= x <= dx_pos + btn_w / 2 and
                        dy_pos - btn_h / 2 <= y <= dy_pos + btn_h / 2):
                    self._send_to_department(dept)
                    return

            # Клик мимо — закрыть документ
            self.state = STATE_IDLE
            self.anim_progress = 0.0

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Прокрутка колёсиком мыши для просмотра документа"""
        if self.state == STATE_OPEN and not self.phase_finished:
            self.scroll_offset -= scroll_y * 40
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.phase_finished and self.fade_alpha >= 250:
                self.menu_button.check_release(x, y)
                self.next_button.check_release(x, y)

    def go_to_menu(self):
        menu = StartView()
        self.window.show_view(menu)

    def go_to_next_phase(self):
        print("Переход к Фазе 2: Константин Частичная Автоматизация")
