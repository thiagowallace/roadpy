"""
RoadPy – Calculadora de Curvas Horizontais
Versão 1.0  |  UFRGS / IGEO / DGEO
"""

import math
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation

from calculator import calculate_curve, generate_staking_table, format_dms

# ─── Paleta de cores ───────────────────────────────────────────────────────────
BG_DARK   = (0.051, 0.067, 0.090, 1)    # #0D1117
BG_CARD   = (0.102, 0.122, 0.161, 1)    # #1A1F29
BG_CARD2  = (0.078, 0.094, 0.125, 1)    # #141820
ORANGE    = (1.0,   0.392, 0.188, 1)    # #FF6430
ORANGE_D  = (0.85,  0.31,  0.12,  1)    # #D94F1F  (pressionado)
WHITE     = (1, 1, 1, 1)
GRAY_L    = (0.75, 0.75, 0.78, 1)
GRAY_M    = (0.45, 0.45, 0.50, 1)
GREEN     = (0.24, 0.78, 0.53, 1)       # #3DC787
CYAN      = (0.25, 0.75, 0.90, 1)       # #40BFE6
YELLOW    = (0.96, 0.78, 0.26, 1)       # #F5C742

# ─── KV Language string ───────────────────────────────────────────────────────
KV = r"""
#:import dp kivy.metrics.dp

<RoundedLabel@Label>:
    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(self.radius_val)]
    bg_color: (0.102, 0.122, 0.161, 1)
    radius_val: 12

<StyledInput@TextInput>:
    background_color: 0, 0, 0, 0
    foreground_color: 1, 1, 1, 1
    cursor_color: 1, 0.392, 0.188, 1
    hint_text_color: 0.4, 0.4, 0.45, 1
    multiline: False
    font_size: dp(20)
    padding: [dp(0), dp(12), dp(0), dp(0)]
    size_hint_y: None
    height: dp(44)

<ScreenManager>:
    InputScreen:
    ResultsScreen:
    StakingScreen:
"""


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers de UI
# ─────────────────────────────────────────────────────────────────────────────

def with_bg(widget, color=BG_CARD, radius=12):
    """Desenha fundo arredondado num widget."""
    with widget.canvas.before:
        Color(*color)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size,
                                radius=[dp(radius)])
    widget.bind(pos=lambda *_: setattr(rect, 'pos', widget.pos),
                size=lambda *_: setattr(rect, 'size', widget.size))
    return widget


def card(orientation='vertical', padding=16, spacing=8, color=BG_CARD, radius=12, **kw):
    b = BoxLayout(orientation=orientation,
                  padding=[dp(padding)]*4,
                  spacing=dp(spacing),
                  size_hint_y=None, **kw)
    b.bind(minimum_height=b.setter('height'))
    with_bg(b, color, radius)
    return b


def small_label(text, color=GRAY_M, font_size=11, halign='left', **kw):
    lbl = Label(text=text, font_size=dp(font_size), color=color,
                size_hint_y=None, height=dp(18),
                halign=halign, **kw)
    lbl.bind(width=lambda *_: setattr(lbl, 'text_size', (lbl.width, None)))
    return lbl


def value_label(text, color=WHITE, font_size=20, bold=False, halign='left', **kw):
    lbl = Label(text=text, font_size=dp(font_size), color=color,
                bold=bold, size_hint_y=None, height=dp(32),
                halign=halign, **kw)
    lbl.bind(width=lambda *_: setattr(lbl, 'text_size', (lbl.width, None)))
    return lbl


def section_label(text):
    lbl = Label(text=text.upper(), font_size=dp(11), color=ORANGE,
                bold=True, size_hint_y=None, height=dp(24),
                halign='left')
    lbl.bind(width=lambda *_: setattr(lbl, 'text_size', (lbl.width, None)))
    return lbl


def input_card(label_text, hint, input_filter='float', **kw):
    """Cria card de input com label superior."""
    box = BoxLayout(orientation='vertical',
                    padding=[dp(16), dp(10), dp(16), dp(8)],
                    spacing=dp(2),
                    size_hint_y=None, height=dp(80), **kw)
    with_bg(box)
    box.add_widget(small_label(label_text))
    inp = TextInput(hint_text=hint, input_filter=input_filter,
                    background_color=(0, 0, 0, 0),
                    foreground_color=WHITE,
                    cursor_color=ORANGE,
                    hint_text_color=GRAY_M,
                    multiline=False, font_size=dp(20),
                    padding=[0, dp(8), 0, 0],
                    size_hint_y=None, height=dp(44))
    box.add_widget(inp)
    return box, inp


def result_card(label, value, sub='', accent=WHITE):
    """Card de resultado com label, valor e sub-texto opcional."""
    box = BoxLayout(orientation='vertical',
                    padding=[dp(16), dp(12), dp(16), dp(12)],
                    spacing=dp(2),
                    size_hint_y=None, height=dp(80 if not sub else 96))
    with_bg(box)
    box.add_widget(small_label(label))
    box.add_widget(value_label(value, color=accent, font_size=22, bold=True))
    if sub:
        box.add_widget(small_label(sub, color=GRAY_M, font_size=10))
    return box


# ─────────────────────────────────────────────────────────────────────────────
#  Tela de entrada
# ─────────────────────────────────────────────────────────────────────────────

class InputScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name='input', **kw)
        self._build_ui()

    def _build_ui(self):
        # Fundo
        with self.canvas.before:
            Color(*BG_DARK)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, 'pos', self.pos),
                  size=lambda *_: setattr(self._bg, 'size', self.size))

        scroll = ScrollView()
        root = BoxLayout(orientation='vertical',
                         padding=[dp(20), dp(20), dp(20), dp(30)],
                         spacing=dp(14),
                         size_hint_y=None)
        root.bind(minimum_height=root.setter('height'))
        scroll.add_widget(root)
        self.add_widget(scroll)

        # ── Header ──────────────────────────────────────────────────────────
        header = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(90))
        title = Label(text='[b]ROAD[color=#FF6430]PY[/color][/b]',
                      markup=True, font_size=dp(42),
                      size_hint_y=None, height=dp(56),
                      halign='left', color=WHITE)
        title.bind(width=lambda *_: setattr(title, 'text_size', (title.width, None)))
        sub = Label(text='Calculadora de Curvas Horizontais',
                    font_size=dp(13), color=GRAY_M,
                    size_hint_y=None, height=dp(22), halign='left')
        sub.bind(width=lambda *_: setattr(sub, 'text_size', (sub.width, None)))
        header.add_widget(title)
        header.add_widget(sub)
        root.add_widget(header)

        # ── Seção: Raio ──────────────────────────────────────────────────────
        root.add_widget(section_label('Raio da Curva'))
        raio_card, self.raio_inp = input_card('Raio (m)', 'Ex: 295')
        root.add_widget(raio_card)

        # ── Seção: Ponto de Interseção ───────────────────────────────────────
        root.add_widget(section_label('Ponto de Interseção (PI)'))
        pi_row = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(80))
        c1, self.estaca_inp = input_card('Estaca (E)', 'Ex: 100', 'int')
        c2, self.fracao_inp = input_card('Fração (m)', 'Ex: 7.40')
        pi_row.add_widget(c1)
        pi_row.add_widget(c2)
        root.add_widget(pi_row)

        # ── Seção: Ângulo Central ─────────────────────────────────────────────
        root.add_widget(section_label('Ângulo Central (AC)'))
        ac_row = GridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(80))
        c1, self.graus_inp   = input_card('Graus (°)', '30', 'int')
        c2, self.min_inp     = input_card("Min (')", '20', 'int')
        c3, self.seg_inp     = input_card('Seg (")', '00')
        ac_row.add_widget(c1)
        ac_row.add_widget(c2)
        ac_row.add_widget(c3)
        root.add_widget(ac_row)

        # ── Erro ─────────────────────────────────────────────────────────────
        self.error_lbl = Label(text='', font_size=dp(12), color=(1, 0.35, 0.35, 1),
                               size_hint_y=None, height=dp(20), halign='left')
        self.error_lbl.bind(width=lambda *_: setattr(self.error_lbl, 'text_size',
                                                     (self.error_lbl.width, None)))
        root.add_widget(self.error_lbl)

        # ── Botão Calcular ────────────────────────────────────────────────────
        self.calc_btn = Button(
            text='CALCULAR CURVA',
            size_hint_y=None, height=dp(58),
            font_size=dp(16), bold=True,
            background_color=(0, 0, 0, 0), color=WHITE,
        )
        with self.calc_btn.canvas.before:
            Color(*ORANGE)
            self._btn_rect = RoundedRectangle(
                pos=self.calc_btn.pos, size=self.calc_btn.size, radius=[dp(18)])
        self.calc_btn.bind(
            pos=lambda *_: setattr(self._btn_rect, 'pos', self.calc_btn.pos),
            size=lambda *_: setattr(self._btn_rect, 'size', self.calc_btn.size),
        )
        self.calc_btn.bind(on_press=self._on_calc_press)
        root.add_widget(self.calc_btn)
        root.add_widget(Widget(size_hint_y=None, height=dp(10)))

    def _on_calc_press(self, *_):
        self.error_lbl.text = ''
        try:
            raio     = float(self.raio_inp.text or '0')
            estaca   = int(self.estaca_inp.text or '0')
            fracao   = float(self.fracao_inp.text or '0')
            graus    = float(self.graus_inp.text or '0')
            minutos  = float(self.min_inp.text or '0')
            segundos = float(self.seg_inp.text or '0')

            if raio <= 0:
                raise ValueError("Raio deve ser maior que zero.")
            if graus <= 0 and minutos <= 0 and segundos <= 0:
                raise ValueError("Ângulo Central deve ser maior que zero.")
            if fracao < 0 or fracao >= 20:
                raise ValueError("Fração da estaca deve estar entre 0 e 19.99 m.")

            result = calculate_curve(raio, graus, minutos, segundos, estaca, fracao)
            app = App.get_running_app()
            app.last_result = result
            res_screen = self.manager.get_screen('results')
            res_screen.populate(result)
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = 'results'

        except ValueError as e:
            self.error_lbl.text = f'⚠  {e}'
        except Exception as e:
            self.error_lbl.text = f'Erro inesperado: {e}'


# ─────────────────────────────────────────────────────────────────────────────
#  Tela de resultados
# ─────────────────────────────────────────────────────────────────────────────

class ResultsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name='results', **kw)
        self._build_shell()

    def _build_shell(self):
        with self.canvas.before:
            Color(*BG_DARK)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, 'pos', self.pos),
                  size=lambda *_: setattr(self._bg, 'size', self.size))

        root = BoxLayout(orientation='vertical')
        self.add_widget(root)

        # Top bar
        topbar = BoxLayout(size_hint_y=None, height=dp(58), padding=[dp(6), 0])
        with topbar.canvas.before:
            Color(*BG_CARD)
            self._tb_rect = Rectangle(pos=topbar.pos, size=topbar.size)
        topbar.bind(pos=lambda *_: setattr(self._tb_rect, 'pos', topbar.pos),
                    size=lambda *_: setattr(self._tb_rect, 'size', topbar.size))

        back_btn = Button(text='◀', size_hint_x=None, width=dp(50),
                          font_size=dp(20), background_color=(0, 0, 0, 0),
                          color=ORANGE, bold=True)
        back_btn.bind(on_press=self._go_back)
        title_lbl = Label(text='Elementos da Curva', font_size=dp(17),
                          bold=True, color=WHITE)

        stake_btn = Button(text='Estaqueamento  ▶',
                           size_hint_x=None, width=dp(160),
                           font_size=dp(12), background_color=(0, 0, 0, 0),
                           color=ORANGE, bold=True)
        stake_btn.bind(on_press=self._go_staking)

        topbar.add_widget(back_btn)
        topbar.add_widget(title_lbl)
        topbar.add_widget(stake_btn)
        root.add_widget(topbar)

        # Scroll area
        self.scroll = ScrollView()
        self.content = BoxLayout(orientation='vertical',
                                 padding=[dp(16), dp(14), dp(16), dp(30)],
                                 spacing=dp(10),
                                 size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        root.add_widget(self.scroll)

    def _go_back(self, *_):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'input'

    def _go_staking(self, *_):
        app = App.get_running_app()
        if hasattr(app, 'last_result') and app.last_result:
            sk = self.manager.get_screen('staking')
            sk.populate(app.last_result)
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = 'staking'

    def populate(self, r: dict):
        self.content.clear_widgets()
        c = self.content

        # ── Ângulo e Raio (entrada confirmada) ──────────────────────────────
        c.add_widget(section_label('Dados de Entrada'))
        row = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(80))
        row.add_widget(result_card('Raio (R)', f"{App.get_running_app().raio:.2f} m",
                                   accent=CYAN))
        row.add_widget(result_card('Ângulo Central (AC)', r['ac_fmt'], accent=CYAN))
        c.add_widget(row)

        # ── Corda ────────────────────────────────────────────────────────────
        c.add_widget(section_label('Corda (Tabela DNIT)'))
        c.add_widget(result_card('Comprimento da Corda', f"{r['corda']:.0f} m",
                                 sub='Baseado no Raio da Curva', accent=YELLOW))

        # ── Elementos Geométricos ─────────────────────────────────────────────
        c.add_widget(section_label('Elementos Geométricos'))

        row1 = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(80))
        row1.add_widget(result_card('Tangente Externa (T)', f"{r['T']:.3f} m"))
        row1.add_widget(result_card('Desenvolvimento (D)', f"{r['D']:.3f} m"))
        c.add_widget(row1)

        row2 = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(80))
        row2.add_widget(result_card('Afastamento (E)', f"{r['E']:.3f} m"))
        row2.add_widget(result_card('Corda Longa (CL)', f"{r['corda_longa']:.3f} m"))
        c.add_widget(row2)

        # ── Grau e Deflexão ──────────────────────────────────────────────────
        c.add_widget(section_label('Grau e Deflexão'))

        row3 = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(80))
        row3.add_widget(result_card('Grau da Curva (Gc)', r['Gc_fmt'], accent=GREEN))
        row3.add_widget(result_card('Deflexão / Metro (dm)', r['dm_fmt'], accent=GREEN))
        c.add_widget(row3)

        # ── Deflexões Parciais ───────────────────────────────────────────────
        c.add_widget(section_label('Deflexões Parciais'))

        row4 = GridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(80))
        row4.add_widget(result_card('Corda PC', r['d_pc_fmt'],
                                    sub=f"{r['primeira_corda']:.3f} m"))
        row4.add_widget(result_card('Corda Padrão', r['d_corda_fmt'],
                                    sub=f"{r['corda']:.0f} m"))
        row4.add_widget(result_card('Corda PT', r['d_pt_fmt'],
                                    sub=f"{r['ultima_corda']:.3f} m"))
        c.add_widget(row4)

        # ── Locação PC e PT ──────────────────────────────────────────────────
        c.add_widget(section_label('Locação das Estacas'))

        row5 = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(96))
        row5.add_widget(result_card(
            'PC – Ponto de Curvatura', r['pc_fmt'],
            sub=f"{r['pc_metros']:.3f} m (decimal)", accent=ORANGE))
        row5.add_widget(result_card(
            'PT – Ponto de Tangência', r['pt_fmt'],
            sub=f"{r['pt_metros']:.3f} m (decimal)", accent=ORANGE))
        c.add_widget(row5)

        # ── Desenho simplificado da curva ─────────────────────────────────────
        c.add_widget(section_label('Diagrama da Curva'))
        draw = CurveDrawWidget(r, size_hint_y=None, height=dp(220))
        c.add_widget(draw)

        c.add_widget(Widget(size_hint_y=None, height=dp(20)))


# ─────────────────────────────────────────────────────────────────────────────
#  Widget de desenho da curva
# ─────────────────────────────────────────────────────────────────────────────

class CurveDrawWidget(Widget):
    def __init__(self, result, **kw):
        super().__init__(**kw)
        self.result = result
        self.bind(size=self._draw, pos=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        r = self.result
        w, h = self.width, self.height
        cx, cy = self.x + w / 2, self.y + h / 2

        ac_rad = math.radians(r['ac_dec'])
        R_norm = min(w, h) * 0.30  # raio normalizado para tela

        # Centro da circunferência (abaixo do PC/PT)
        ox, oy = cx, self.y + R_norm + dp(10)

        # Ângulos para PC e PT
        half = ac_rad / 2.0
        angle_pc = math.pi / 2 + half
        angle_pt = math.pi / 2 - half

        pc_x = ox + R_norm * math.cos(angle_pc)
        pc_y = oy + R_norm * math.sin(angle_pc)
        pt_x = ox + R_norm * math.cos(angle_pt)
        pt_y = oy + R_norm * math.sin(angle_pt)

        # PI (interseção das tangentes)
        pi_x = cx
        pi_y = pc_y + R_norm * math.sin(half) * math.tan(half) * 0.8

        # Ponto médio da curva (topo)
        pm_x = cx
        pm_y = oy + R_norm

        with self.canvas:
            # Fundo
            Color(*BG_CARD2)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])

            # Arco da curva
            Color(*ORANGE)
            start_a = math.degrees(angle_pt)
            sweep_a = math.degrees(ac_rad)
            Line(ellipse=(ox - R_norm, oy - R_norm,
                          2 * R_norm, 2 * R_norm,
                          start_a, start_a + sweep_a), width=dp(2.5))

            # Tangentes (PC→PI e PT→PI)
            Color(0.4, 0.4, 0.5, 1)
            Line(points=[pc_x, pc_y, pi_x, pi_y], width=dp(1.5), dash_length=6, dash_offset=4)
            Line(points=[pt_x, pt_y, pi_x, pi_y], width=dp(1.5), dash_length=6, dash_offset=4)

            # Linha R do centro até PM
            Color(*CYAN, 0.4)
            Line(points=[ox, oy, pm_x, pm_y], width=dp(1))

            # Raio R do centro até PC e PT
            Color(*CYAN, 0.25)
            Line(points=[ox, oy, pc_x, pc_y], width=dp(1))
            Line(points=[ox, oy, pt_x, pt_y], width=dp(1))

            # Pontos
            sz = dp(7)
            for px, py, cor in [
                (pc_x, pc_y, ORANGE),
                (pt_x, pt_y, ORANGE),
                (pi_x, pi_y, YELLOW),
                (ox,   oy,   GRAY_M),
                (pm_x, pm_y, GREEN),
            ]:
                Color(*cor)
                Ellipse(pos=(px - sz / 2, py - sz / 2), size=(sz, sz))

        # Labels via Label widgets (canvas não suporta texto nativo fácil)
        self._add_label('PC', pc_x, pc_y + dp(12), ORANGE)
        self._add_label('PT', pt_x, pt_y + dp(12), ORANGE)
        self._add_label('PI', pi_x, pi_y + dp(10), YELLOW)
        self._add_label('O', ox + dp(8), oy, GRAY_M)
        self._add_label(f"R={App.get_running_app().raio:.0f}m",
                        (ox + pm_x) / 2 + dp(10), (oy + pm_y) / 2, CYAN)

    def _add_label(self, text, x, y, color):
        lbl = Label(text=text, font_size=dp(10), color=(*color[:3], 0.9),
                    size=(dp(60), dp(18)),
                    pos=(x - dp(30), y - dp(9)),
                    bold=True)
        self.add_widget(lbl)


# ─────────────────────────────────────────────────────────────────────────────
#  Tela de estaqueamento
# ─────────────────────────────────────────────────────────────────────────────

class StakingScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name='staking', **kw)
        self._build_shell()

    def _build_shell(self):
        with self.canvas.before:
            Color(*BG_DARK)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, 'pos', self.pos),
                  size=lambda *_: setattr(self._bg, 'size', self.size))

        root = BoxLayout(orientation='vertical')
        self.add_widget(root)

        # Top bar
        topbar = BoxLayout(size_hint_y=None, height=dp(58), padding=[dp(6), 0])
        with topbar.canvas.before:
            Color(*BG_CARD)
            tb = Rectangle(pos=topbar.pos, size=topbar.size)
        topbar.bind(pos=lambda *_: setattr(tb, 'pos', topbar.pos),
                    size=lambda *_: setattr(tb, 'size', topbar.size))

        back_btn = Button(text='◀', size_hint_x=None, width=dp(50),
                          font_size=dp(20), background_color=(0, 0, 0, 0),
                          color=ORANGE, bold=True)
        back_btn.bind(on_press=lambda *_: self._go_back())
        title_lbl = Label(text='Tabela de Estaqueamento', font_size=dp(16),
                          bold=True, color=WHITE)
        topbar.add_widget(back_btn)
        topbar.add_widget(title_lbl)
        root.add_widget(topbar)

        # Header da tabela
        self._table_header(root)

        # Scroll
        self.scroll = ScrollView()
        self.list_box = BoxLayout(orientation='vertical',
                                  spacing=dp(2),
                                  size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.scroll.add_widget(self.list_box)
        root.add_widget(self.scroll)

    def _table_header(self, root):
        hdr = GridLayout(cols=4,
                         size_hint_y=None, height=dp(36),
                         padding=[dp(8), 0, dp(8), 0])
        with hdr.canvas.before:
            Color(*BG_CARD)
            r = Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda *_: setattr(r, 'pos', hdr.pos),
                 size=lambda *_: setattr(r, 'size', hdr.size))
        for col in ['Estaca', 'Dist. (m)', 'Deflexão', 'Leitura L.']:
            lbl = Label(text=col, font_size=dp(10), color=ORANGE, bold=True)
            hdr.add_widget(lbl)
        root.add_widget(hdr)

    def _go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'results'

    def populate(self, result: dict):
        self.list_box.clear_widgets()
        rows = generate_staking_table(result)
        is_pc_pt = {'PC', 'PT'}

        for i, row in enumerate(rows):
            bg = BG_CARD if i % 2 == 0 else BG_CARD2
            accent = ORANGE if any(k in row['label'] for k in is_pc_pt) else WHITE

            grid = GridLayout(cols=4, size_hint_y=None, height=dp(40),
                              padding=[dp(8), 0, dp(8), 0])
            with grid.canvas.before:
                Color(*bg)
                rect = Rectangle(pos=grid.pos, size=grid.size)
            grid.bind(pos=lambda inst, *_: setattr(rect, 'pos', inst.pos),
                      size=lambda inst, *_: setattr(rect, 'size', inst.size))

            for txt, clr in [
                (row['label'],          accent),
                (f"{row['distancia']:.2f}", GRAY_L),
                (row['parcial_fmt'],    GRAY_L),
                (row['limbo'],          CYAN),
            ]:
                lbl = Label(text=txt, font_size=dp(11), color=clr,
                            bold=(txt == row['label']))
                grid.add_widget(lbl)

            self.list_box.add_widget(grid)


# ─────────────────────────────────────────────────────────────────────────────
#  App principal
# ─────────────────────────────────────────────────────────────────────────────

class RoadPyApp(App):
    title = 'RoadPy'
    last_result = None
    raio = 0.0  # Armazenado para o widget de desenho

    def build(self):
        Builder.load_string(KV)
        sm = ScreenManager()
        sm.add_widget(InputScreen())
        sm.add_widget(ResultsScreen())
        sm.add_widget(StakingScreen())

        # Patch: armazenar raio quando calcular
        inp = sm.get_screen('input')
        orig = inp._on_calc_press

        def patched_calc(btn):
            try:
                self.raio = float(inp.raio_inp.text or '0')
            except Exception:
                pass
            orig(btn)

        inp.calc_btn.unbind(on_press=inp._on_calc_press)
        inp.calc_btn.bind(on_press=patched_calc)

        Window.clearcolor = BG_DARK
        return sm


if __name__ == '__main__':
    RoadPyApp().run()
