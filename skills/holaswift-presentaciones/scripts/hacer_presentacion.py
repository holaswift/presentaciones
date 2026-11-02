#!/usr/bin/env python3
"""hola Swift · genera una presentación .pptx (16:9) con el estilo de la marca a partir de un guion en JSON.

Uso:
    python3 hacer_presentacion.py guion.json salida.pptx

Necesita: python-pptx, Pillow y numpy  (pip install python-pptx pillow numpy)
El formato del guion está en ../references/guion.md. Cada diapositiva es un "tipo" con sus campos;
el script decide tamaños, posiciones y colores para que todo salga dentro de la marca.
"""
import json, os, re, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(AQUI, '..', 'assets')
W, H, M = 1920, 1080, 128          # lienzo en px (1 px = 0,5 pt) y margen
CACHE = os.path.join(tempfile.gettempdir(), 'holaswift-presentaciones')
os.makedirs(CACHE, exist_ok=True)

# ── Marca ────────────────────────────────────────────────────────────────
ESPECTRO = {'lavanda': '#7586EC', 'verde': '#33C468', 'amarillo': '#FFB823', 'naranja': '#FF7039',
            'rosa': '#FF4F8B', 'magenta': '#D553D3', 'violeta': '#6D5FF0', 'azul': '#3772F0'}
VECINOS = {'azul': ('lavanda', 'violeta'), 'verde': ('amarillo', 'lavanda'), 'naranja': ('amarillo', 'rosa'),
           'rosa': ('naranja', 'magenta'), 'violeta': ('magenta', 'azul'), 'lavanda': ('azul', 'verde'),
           'magenta': ('rosa', 'violeta'), 'amarillo': ('naranja', 'verde')}
CONTENIDO = {'charla': 'azul', 'encuentro': 'naranja', 'personas': 'verde', 'persona': 'verde',
             'embajador': 'verde', 'patrocinio': 'violeta', 'comunidad': 'rosa'}
TITULOS, TEXTO, CODIGO = 'Inter Display', 'Inter', 'Menlo'

def hx(c): c = c.lstrip('#'); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
def mezcla(a, b, t): a, b = hx(a), hx(b); return '#%02X%02X%02X' % tuple(round(x + (y - x) * t) for x, y in zip(a, b))

def tema(nombre, acento=None):
    if nombre == 'oscuro':
        return dict(id='oscuro', fondo='#0C0B0B', superficie='#1A1A1D', linea='#2A2A2F', texto='#FFFFFF', texto2='#B8B8C2',
                    texto3='#8C8C96', logo='hola-swift-color-oscuro', tubo='hola', excl='exclamacion')
    if nombre == 'color':
        c = ESPECTRO.get(acento or 'azul', ESPECTRO['azul'])
        return dict(id='color', acento=acento or 'azul', fondo=c, superficie=mezcla(c, '#FFFFFF', 0.16), linea=mezcla(c, '#FFFFFF', 0.3),
                    texto='#FFFFFF', texto2=mezcla(c, '#FFFFFF', 0.86), texto3=mezcla(c, '#FFFFFF', 0.72),
                    logo='hola-swift-blanco', tubo='hola-blanco', excl='exclamacion-blanco')
    return dict(id='claro', fondo='#F7F7F7', superficie='#FFFFFF', linea='#E3E3E8', texto='#111111', texto2='#55555F',
                texto3='#6E6E78', logo='hola-swift-color', tubo='hola', excl='exclamacion')

# ── Fondos: color plano + retícula de puntos + grano; en "color", esquinas punteadas del color vecino ──
def fondo_png(T):
    clave = T['id'] + '-' + T.get('acento', '')
    ruta = os.path.join(CACHE, f'fondo-{clave}.jpg')     # JPG: el grano no comprime en PNG (3 MB por fondo)
    if os.path.exists(ruta): return ruta
    rng = np.random.default_rng(7)
    img = np.zeros((H, W, 3), np.float32); img[:] = hx(T['fondo'])
    if T['id'] == 'color':
        yy, xx = np.mgrid[0:H, 0:W]
        for vecino, (cx, cy, r) in zip(VECINOS[T['acento']], [(W, 0, 0.55), (0, H, 0.6)]):
            d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (max(W, H) * r)
            a = np.clip(1 - d, 0, 1) ** 1.2
            punto = (rng.random((H, W)) < a * a * 1.15)[..., None]
            img = np.where(punto, np.array(hx(ESPECTRO[vecino]), np.float32), img)
    im = Image.fromarray(img.astype(np.uint8)).convert('RGBA')
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dib = ImageDraw.Draw(capa)
    tinta = {'claro': (17, 17, 17, 30), 'oscuro': (255, 255, 255, 26), 'color': (255, 255, 255, 70)}[T['id']]
    for y in range(20, H, 40):
        for x in range(20, W, 40): dib.ellipse((x - 2, y - 2, x + 2, y + 2), fill=tinta)
    im = Image.alpha_composite(im, capa)
    grano = rng.normal(0, {'claro': 4, 'oscuro': 5, 'color': 9}[T['id']], (H, W, 1))
    arr = np.clip(np.asarray(im.convert('RGB'), np.float32) + grano, 0, 255).astype(np.uint8)
    Image.fromarray(arr).save(ruta, quality=88, optimize=True)
    return ruta

# ── Utilidades de maquetación ────────────────────────────────────────────
def E(px): return Emu(int(round(px * 914400 / 144)))
ANCHO_LETRA = {TITULOS: 0.6, TEXTO: 0.56, CODIGO: 0.6}

def lineas(texto, px, ancho, fam):
    """Reparto aproximado en líneas: cuántas ocupa un texto a un tamaño en un ancho."""
    cw = px * ANCHO_LETRA[fam]; n = 0
    for parrafo in str(texto).split('\n'):
        actual = 0; n += 1
        for palabra in parrafo.split(' '):
            w = len(palabra) * cw
            if w > ancho: return 99                     # una palabra que no cabe en el ancho: hay que bajar el tamaño
            if actual and actual + cw + w > ancho: n += 1; actual = w
            else: actual += (cw if actual else 0) + w
    return n

def ajustar(texto, maximo, minimo, ancho, max_lineas, fam=TITULOS):
    px = maximo
    while px > minimo and lineas(texto, px, ancho, fam) > max_lineas: px -= 2
    return px

def caja(sl, x, y, w, h, texto, px, color, fam=TEXTO, negrita=False, alinear='izq', inter=1.15, ancla='arriba', track=None):
    tb = sl.shapes.add_textbox(E(x), E(y), E(w), E(h)); tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {'arriba': MSO_ANCHOR.TOP, 'centro': MSO_ANCHOR.MIDDLE, 'abajo': MSO_ANCHOR.BOTTOM}[ancla]
    for i, par in enumerate(str(texto).split('\n')):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {'izq': PP_ALIGN.LEFT, 'centro': PP_ALIGN.CENTER, 'der': PP_ALIGN.RIGHT}[alinear]
        p.line_spacing = Pt(px * inter / 2)          # interlineado fijo: así el alto calculado es el real
        r = p.add_run(); r.text = par
        f = r.font; f.size = Pt(px / 2); f.name = fam; f.bold = negrita; f.color.rgb = RGBColor(*hx(color))
        if track is not None:
            rPr = r._r.get_or_add_rPr(); rPr.set('spc', str(int(track * px / 2 * 100)))
    return tb

def pila(sl, x, y, w, h, bloques, ancla='arriba', alinear='izq'):
    """Varios textos seguidos en UNA caja (un párrafo por bloque): la app reparte el espacio, sin huecos ni solapes.
    Cada bloque: dict(t, px, color, fam=TEXTO, b=False, inter=1.2, antes=0 (px de aire encima), track=None)."""
    tb = sl.shapes.add_textbox(E(x), E(y), E(w), E(h)); tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {'arriba': MSO_ANCHOR.TOP, 'centro': MSO_ANCHOR.MIDDLE, 'abajo': MSO_ANCHOR.BOTTOM}[ancla]
    primero = True
    for bq in bloques:
        if not bq.get('t'): continue
        for j, par in enumerate(str(bq['t']).split('\n')):
            p = tf.paragraphs[0] if primero else tf.add_paragraph(); primero = False
            p.alignment = {'izq': PP_ALIGN.LEFT, 'centro': PP_ALIGN.CENTER, 'der': PP_ALIGN.RIGHT}[alinear]
            p.line_spacing = Pt(bq['px'] * bq.get('inter', 1.2) / 2)
            if j == 0 and bq.get('antes'): p.space_before = Pt(bq['antes'] / 2)
            if bq.get('marca'):
                m = p.add_run(); m.text = '•  '; m.font.size = Pt(bq['px'] / 2); m.font.name = TEXTO; m.font.bold = True; m.font.color.rgb = RGBColor(*hx(bq['marca']))
            # `entre comillas invertidas` = código: en monoespaciada, un punto más pequeña
            for k, trozo in enumerate(re.split(r'`([^`]+)`', par) if bq.get('fam', TEXTO) == TEXTO else [par]):
                if not trozo: continue
                es_cod = k % 2 == 1
                r = p.add_run(); r.text = trozo; f = r.font
                f.size = Pt(bq['px'] * (0.9 if es_cod else 1) / 2); f.name = CODIGO if es_cod else bq.get('fam', TEXTO)
                f.bold = bq.get('b', False) and not es_cod; f.color.rgb = RGBColor(*hx(bq['color']))
                if bq.get('track') is not None and not es_cod: r._r.get_or_add_rPr().set('spc', str(int(bq['track'] * bq['px'] / 2 * 100)))
    return tb

def alto(texto, px, ancho, fam, inter=1.15): return lineas(texto, px, ancho, fam) * px * inter

def rect(sl, x, y, w, h, color, radio=0, borde=None):
    sh = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radio else MSO_SHAPE.RECTANGLE, E(x), E(y), E(w), E(h))
    if radio: sh.adjustments[0] = min(0.5, radio / min(w, h))
    sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor(*hx(color))
    if borde: sh.line.color.rgb = RGBColor(*hx(borde)); sh.line.width = Pt(1)
    else: sh.line.fill.background()
    sh.shadow.inherit = False
    return sh

def circulo(sl, x, y, d, color):
    sh = sl.shapes.add_shape(MSO_SHAPE.OVAL, E(x), E(y), E(d), E(d))
    sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor(*hx(color)); sh.line.fill.background(); sh.shadow.inherit = False
    return sh

def imagen(sl, ruta, x, y, w=None, h=None):
    if w and h: pic = sl.shapes.add_picture(ruta, E(x), E(y), E(w), E(h))
    elif w: pic = sl.shapes.add_picture(ruta, E(x), E(y), width=E(w))
    else: pic = sl.shapes.add_picture(ruta, E(x), E(y), height=E(h))
    if os.path.basename(ruta).startswith('hola-swift'):   # texto alternativo del logo: la marca, no el nombre del archivo
        pic._element.nvPicPr.cNvPr.set('descr', 'hola Swift')
    return pic

def tam(ruta): return Image.open(ruta).size
def asset(*p): return os.path.join(ASSETS, *p)

def foto_cubre(sl, ruta, x, y, w, h, radio=0):
    """Foto recortada para llenar la caja (como object-fit: cover), con esquinas redondas opcionales."""
    iw, ih = tam(ruta); pic = sl.shapes.add_picture(ruta, E(x), E(y), E(w), E(h))
    caja_r, img_r = w / h, iw / ih
    if img_r > caja_r: c = (1 - caja_r / img_r) / 2; pic.crop_left = pic.crop_right = c
    else: c = (1 - img_r / caja_r) / 2; pic.crop_top = pic.crop_bottom = c
    if radio:
        pic.auto_shape_type = MSO_SHAPE.ROUNDED_RECTANGLE
        pic._element.spPr.prstGeom.avLst.clear()
        gd = pic._element.spPr.prstGeom.avLst.makeelement('{http://schemas.openxmlformats.org/drawingml/2006/main}gd', {'name': 'adj', 'fmla': f'val {int(min(50000, radio / min(w, h) * 100000))}'})
        pic._element.spPr.prstGeom.avLst.append(gd)
    return pic

def logo(sl, T, x=M, y=88, h=56):
    ruta = asset('logo', T['logo'] + '.png'); imagen(sl, ruta, x, y, h=h)

def tubo_hola(sl, T, x, y, h, excl=False):
    """El "hola" en tubo (con "¡" opcional). Devuelve el ancho total."""
    hola = asset('tubo', T['tubo'] + '.png'); hw, hh = tam(hola); ancho_h = hw * h / hh
    dx = 0
    if excl:
        ex = asset('tubo', T['excl'] + '.png'); ew, eh = tam(ex); he = h * 0.86
        imagen(sl, ex, x, y + h * 0.1, h=he); dx = ew * he / eh * 0.95 + h * 0.04
    imagen(sl, hola, x + dx, y, h=h)
    return dx + ancho_h

def ratio_hola(T, excl):
    hw, hh = tam(asset('tubo', T['tubo'] + '.png')); r = hw / hh
    if excl: ew, eh = tam(asset('tubo', T['excl'] + '.png')); r += ew / eh * 0.86 * 0.95 + 0.04
    return r

# ── Código: resaltado sencillo de Swift con colores del espectro ─────────
CLAVES = set('let var func if else guard return struct class enum protocol extension import for in while switch case default break continue true false nil self Self some any async await throws try catch do where init deinit static private public internal fileprivate final override mutating inout typealias weak lazy defer repeat'.split())
def tokens(linea, oscuro):
    col = {'clave': '#FF4F8B', 'cadena': '#FF7039', 'numero': '#FFB823', 'tipo': '#7586EC', 'llamada': '#33C468',
           'comentario': '#8C8C96', 'normal': '#FFFFFF', 'signo': '#B8B8C2'}
    if not oscuro: col = {k: (mezcla(v, '#000000', 0.42) if k not in ('normal', 'signo', 'comentario') else {'normal': '#111111', 'signo': '#55555F', 'comentario': '#8C8C96'}[k]) for k, v in col.items()}
    out = []
    for m in re.finditer(r'(//.*$)|("(?:[^"\\]|\\.)*"?)|(\b\d+(?:\.\d+)?\b)|([A-Za-zÁÉÍÓÚáéíóúñÑ_][\wÁÉÍÓÚáéíóúñÑ]*)|(\s+)|(.)', linea):
        t, com, cad, num, ide, esp, _ = m.group(0), *m.groups()
        k = 'signo'
        if com: k = 'comentario'
        elif cad: k = 'cadena'
        elif num: k = 'numero'
        elif esp: k = 'normal'
        elif ide:
            sig = linea[m.end():].lstrip()[:1]
            k = 'clave' if ide in CLAVES else 'tipo' if ide[0].isupper() else 'llamada' if sig == '(' else 'normal'
        out.append((t, col[k]))
    return out

# ── Tipos de diapositiva ─────────────────────────────────────────────────
def d_portada(sl, T, d):
    logo(sl, T)
    ex = d.get('exclamacion', False); r = ratio_hola(T, ex); h = min(540, (W - 2 * M - 120) / r)
    tubo_hola(sl, T, (W - r * h) / 2, 190 + (540 - h) / 2, h, ex)
    t = d.get('titulo', ''); px = ajustar(t, 96, 56, 1180, 2)
    pila(sl, M, 780, 1180, H - M - 780, [dict(t=t, px=px, color=T['texto'], fam=TITULOS, b=True, inter=1.04, track=-0.025)], ancla='abajo')
    if d.get('subtitulo'):
        pila(sl, W - M - 460, 780, 460, H - M - 780 - px * 0.12, [dict(t=d['subtitulo'], px=30, color=T['texto2'], inter=1.35)], ancla='abajo', alinear='der')

def d_hola(sl, T, d):
    """¡hola + palabra enorme (tema, ciudad, año) e información abajo: el gesto de la marca."""
    logo(sl, T)
    excl = d.get('exclamacion', True); pal = d.get('palabra', '')
    info = [dict(t=d.get('titulo'), px=48, color=T['texto'], fam=TITULOS, b=True, inter=1.15, track=-0.01),
            dict(t=d.get('texto'), px=32, color=T['texto2'], inter=1.35, antes=14)]
    alto_info = sum(alto(b['t'], b['px'], 1300, b.get('fam', TEXTO), b['inter']) + b.get('antes', 0) for b in info if b['t'])
    y0, y1 = 190, H - M - alto_info - 56
    r = ratio_hola(T, excl); px = ajustar(pal, 280, 120, W - 2 * M, 1)
    h = min((W - 2 * M) * 0.62 / r, (y1 - y0 - px * 0.95))
    tubo_hola(sl, T, M - 6, y0, h, excl)
    caja(sl, M - px * 0.04, y0 + h + px * 0.08, W - M, px * 1.05, pal, px, T['texto'], TITULOS, True, inter=0.9, track=-0.035)
    pila(sl, M, y1, 1400, H - M - y1, info, ancla='abajo')

def d_frase(sl, T, d):
    f = d.get('frase', ''); px = ajustar(f, 150, 72, 1560, 3)
    pila(sl, M, M, 1600, H - 2 * M, [
        dict(t=d.get('antetitulo'), px=32, color=T['texto3'], inter=1.3),
        dict(t=f, px=px, color=T['texto'], fam=TITULOS, b=True, inter=1.0, track=-0.03, antes=24),
        dict(t=d.get('texto'), px=40, color=T['texto2'], inter=1.35, antes=48)], ancla='centro')

def titular(sl, T, t, ancho=W - 2 * M):
    px = ajustar(t, 72, 52, ancho, 2); a = alto(t, px, ancho, TITULOS, 1.08)
    caja(sl, M, M, ancho, a + 10, t, px, T['texto'], TITULOS, True, inter=1.08, track=-0.02)
    return M + a + 56

def d_texto(sl, T, d):
    """Titular y párrafos o puntos, en una sola caja de texto: el espacio entre puntos lo reparte la propia app."""
    y = titular(sl, T, d.get('titulo', ''))
    ancho = 1300; puntos = d.get('puntos')
    items = puntos or d.get('parrafos') or ([d['texto']] if d.get('texto') else [])
    s = 44 if sum(alto(x, 44, ancho, TEXTO, 1.35) + 30 for x in items) < H - M - y else 36
    marca = '#FFFFFF' if T['id'] == 'color' else ESPECTRO.get(d.get('color', ''), T['texto3'])
    pila(sl, M, y, ancho + 60, H - M - y, [dict(t=x, px=s, color=T['texto'] if puntos else T['texto2'], inter=1.35,
         antes=0 if i == 0 else s * 0.75, marca=marca if puntos else None) for i, x in enumerate(items)])

def d_tarjetas(sl, T, d):
    y = titular(sl, T, d.get('titulo', ''))
    ts = d.get('tarjetas', [])[:4]
    if not ts: return
    n = len(ts); cols, filas = (2, 2) if n == 4 else (n, 1)
    gap = 24; cw = (W - 2 * M - gap * (cols - 1)) / cols; inner = cw - 112
    tp = min(ajustar(t.get('titulo', ''), 48, 32, inner, 2) for t in ts)          # mismo tamaño de título en todas
    xp = 32 if n < 4 else 30
    alto_c = max(alto(t.get('titulo', ''), tp, inner, TITULOS, 1.1) + (alto(t.get('texto', ''), xp, inner, TEXTO, 1.4) + 24 if t.get('texto') else 0) for t in ts) + 112
    disponible = (H - M - y - gap * (filas - 1)) / filas
    ch = min(disponible, max(alto_c, 420 if filas == 1 else 260))
    y0 = H - M - (filas * ch + gap * (filas - 1))                                   # las tarjetas se apoyan abajo, con aire bajo el titular
    for i, t in enumerate(ts):
        x, yy = M + (i % cols) * (cw + gap), y0 + (i // cols) * (ch + gap)
        rect(sl, x, yy, cw, ch, T['superficie'], radio=28)
        pila(sl, x + 56, yy + 56, inner, ch - 112, [
            dict(t=t.get('titulo', ''), px=tp, color=T['texto'], fam=TITULOS, b=True, inter=1.1, track=-0.01),
            dict(t=t.get('texto'), px=xp, color=T['texto2'], inter=1.4, antes=20)])

def d_cifras(sl, T, d):
    y = titular(sl, T, d.get('titulo', ''))
    cs = d.get('cifras', [])[:4]
    if not cs: return
    n = len(cs); gap = 64; cw = (W - 2 * M - gap * (n - 1)) / n
    px = min(ajustar(str(c.get('valor', '')), 200, 80, cw, 1) for c in cs)          # mismo tamaño para todas: alinean
    yc = y + (H - M - y - px - 140) / 2
    for i, c in enumerate(cs):
        pila(sl, M + i * (cw + gap), yc, cw, px + 180, [
            dict(t=str(c.get('valor', '')), px=px, color=T['texto'], fam=TITULOS, b=True, inter=1.0, track=-0.03),
            dict(t=c.get('texto'), px=32, color=T['texto2'], inter=1.35, antes=20)])

def d_imagen(sl, T, d):
    y = titular(sl, T, d.get('titulo', '')) if d.get('titulo') else M
    pie = d.get('pie'); hp = 60 if pie else 0
    ruta = d.get('imagen')
    caja_h = H - M - y - hp
    if ruta and os.path.exists(ruta):
        iw, ih = tam(ruta)
        if d.get('ajuste', 'cubrir') == 'cubrir': foto_cubre(sl, ruta, M, y, W - 2 * M, caja_h, radio=28)
        else:
            k = min((W - 2 * M) / iw, caja_h / ih); w, h = iw * k, ih * k
            imagen(sl, ruta, (W - w) / 2, y + (caja_h - h) / 2, w, h)
    else:
        rect(sl, M, y, W - 2 * M, caja_h, T['superficie'], radio=28)
        caja(sl, M, y, W - 2 * M, caja_h, '[Imagen: ' + (os.path.basename(str(ruta)) if ruta else 'falta el archivo') + ']', 30, T['texto3'], alinear='centro', ancla='centro')
    if pie: caja(sl, M, H - M - 40, W - 2 * M, 44, pie, 30, T['texto2'])

def d_codigo(sl, T, d):
    logo(sl, T)
    f = d.get('titulo', ''); px = ajustar(f, 104, 60, 1500, 2); a = alto(f, px, 1500, TITULOS, 1.0)
    caja(sl, M, 210, 1500, a + 10, f, px, T['texto'], TITULOS, True, inter=1.0, track=-0.03)
    lins = str(d.get('codigo', '')).replace('\t', '    ').split('\n')[:12]
    vy = 210 + a + 80; vx = M
    s = 40
    # el código baja de tamaño hasta 28 px como mucho; una línea más larga se sale por la derecha, como la ventana
    while s > 28 and (max(len(l) for l in lins) * s * 0.6 + s * 4 > W - vx - 60 or len(lins) * s * 1.6 + s * 4 > H - vy - 40): s -= 2
    osc = T['id'] == 'oscuro'
    sup = '#1C1C20' if osc else '#FFFFFF'; borde = '#2E2E34' if osc else '#E3E3E8'
    rect(sl, vx, vy, W - vx + 200, H - vy + 200, sup, radio=30, borde=borde)
    for i, c in enumerate(['#FF5F57', '#FEBC2E', '#28C840']): circulo(sl, vx + s * 1.2 + i * s * 0.95, vy + s * 0.95, s * 0.5, c)
    if d.get('archivo'): caja(sl, vx + s * 4.4, vy + s * 0.6, 800, s, d['archivo'], s * 0.62, T['texto3'] if osc else '#6E6E78')
    tb = sl.shapes.add_textbox(E(vx + s * 1.2), E(vy + s * 2.6), E(W - vx - s * 2), E(len(lins) * s * 1.6 + 20)); tf = tb.text_frame
    tf.word_wrap = False; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, l in enumerate(lins):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.line_spacing = Pt(s * 1.45 / 2)
        num = p.add_run(); num.text = f'{i + 1:>2}   '; num.font.size = Pt(s / 2); num.font.name = CODIGO; num.font.color.rgb = RGBColor(*hx('#5C5C66' if osc else '#B0B0B8'))
        for t, c in tokens(l, osc) or [(' ', '#000000')]:
            r = p.add_run(); r.text = t; r.font.size = Pt(s / 2); r.font.name = CODIGO; r.font.color.rgb = RGBColor(*hx(c))

def d_pregunta(sl, T, d):
    hola = asset('tubo', T['tubo'] + '.png'); h = H * 0.7
    imagen(sl, hola, W * 0.42, H - h * 0.62, h=h)                 # el "hola" en macro, saliéndose por abajo y la derecha
    logo(sl, T)
    q = d.get('pregunta', ''); px = ajustar(q, 120, 64, 1150, 4)
    pila(sl, M, 220, 1180, H - 220 - M, [
        dict(t=q, px=px, color=T['texto'], fam=TITULOS, b=True, inter=1.0, track=-0.03),
        dict(t=d.get('texto'), px=44, color=T['texto2'], inter=1.3, antes=40)])

def d_persona(sl, T, d):
    logo(sl, T)
    fw = 640; fy = 200; fh = H - M - fy
    if d.get('foto') and os.path.exists(d['foto']): foto_cubre(sl, d['foto'], M, fy, fw, fh, radio=28)
    else:
        rect(sl, M, fy, fw, fh, T['superficie'], radio=28)
        ini = (re.search(r'\w', d.get('nombre', '')) or re.search('.', '¡')).group(0).upper()
        circulo(sl, M + fw / 2 - 150, fy + fh / 2 - 150, 300, ESPECTRO['verde'])
        caja(sl, M + fw / 2 - 150, fy + fh / 2 - 150, 300, 300, ini, 150, '#111111', TITULOS, True, alinear='centro', ancla='centro', inter=1.0)
    x = M + fw + 96; ancho = W - M - x
    n = d.get('nombre', ''); px = ajustar(n, 120, 64, ancho, 2)
    pila(sl, x, fy, ancho, fh * 0.6, [
        dict(t=d.get('etiqueta'), px=30, color=T['texto3'], inter=1.3),
        dict(t=n, px=px, color=T['texto'], fam=TITULOS, b=True, inter=0.98, track=-0.035, antes=12),
        dict(t=d.get('rol'), px=34, color=T['texto2'], inter=1.3, antes=24)])
    if d.get('frase'):
        fr = '“' + d['frase'] + '”'; s = ajustar(fr, 48, 32, ancho, 4, TEXTO)
        pila(sl, x, fy + fh * 0.6, ancho, fh * 0.4, [dict(t=fr, px=s, color=T['texto'], b=True, inter=1.3)], ancla='abajo')

def d_cierre(sl, T, d):
    """Logotipo, una frase y, si se da, el contacto (nombre, email, web…) en una línea debajo."""
    ruta = asset('logo', T['logo'] + '.png'); lw, lh = tam(ruta); w = 1000; h = w * lh / lw
    contacto = d.get('contacto'); extra = 90 if contacto else 0
    y = (H - h) / 2 - 80 - extra / 2
    imagen(sl, ruta, (W - w) / 2, y, w, h)
    caja(sl, M, y + h + 90, W - 2 * M, 100, d.get('frase', 'Ya no estáis solos.'), 56, T['texto'], TITULOS, True, alinear='centro', track=-0.02)
    if contacto:
        if isinstance(contacto, list): contacto = '   ·   '.join(contacto)
        caja(sl, M, y + h + 90 + 110, W - 2 * M, 60, contacto, 32, T['texto2'], alinear='centro')

def d_espera(sl, T, d):
    """Pantalla de espera, pausa o final: el "¡hola" centrado y un mensaje grande. Para dejarla puesta mientras entra la gente."""
    ex = d.get('exclamacion', True); r = ratio_hola(T, ex); h = min(400, (W - 2 * M) * 0.6 / r)
    tubo_hola(sl, T, (W - r * h) / 2, 170, h, ex)
    t = d.get('titulo', ''); px = ajustar(t, 120, 64, 1500, 2)
    pila(sl, M, 170 + h + 50, W - 2 * M, H - M - (170 + h + 50), [
        dict(t=t, px=px, color=T['texto'], fam=TITULOS, b=True, inter=1.02, track=-0.03),
        dict(t=d.get('texto'), px=40, color=T['texto2'], inter=1.35, antes=28)], alinear='centro')
    ruta = asset('logo', T['logo'] + '.png'); lw, lh = tam(ruta); lh2 = 48
    imagen(sl, ruta, (W - lw * lh2 / lh) / 2, H - 96 - lh2, h=lh2)

def d_agenda(sl, T, d):
    """Programa: hora a la izquierda, charla y ponente a la derecha. `actual` (índice desde 1) resalta la que está en curso."""
    y = titular(sl, T, d.get('titulo', 'Programa'))
    its = d.get('items', [])[:12]
    if not its: return
    cols = 1 if len(its) <= 6 else 2
    por = -(-len(its) // cols); gap = 64; cw = (W - 2 * M - gap * (cols - 1)) / cols
    fila = min(150, (H - M - y) / por)
    s_t = 40 if fila >= 130 else 34; s_d = 28 if fila >= 130 else 24
    acento = '#FFFFFF' if T['id'] == 'color' else ESPECTRO.get(T.get('acento') or 'azul', ESPECTRO['azul'])
    act = d.get('actual')
    for i, it in enumerate(its):
        x = M + (i // por) * (cw + gap); yy = y + (i % por) * fila
        rect(sl, x, yy, cw, 2, T['linea'])
        es = act == i + 1
        if es: rect(sl, x, yy + 22, 8, fila - 44, acento, radio=4)
        caja(sl, x + (28 if es else 0), yy + 24, 220, s_t * 1.2, it.get('hora', ''), s_t, T['texto'] if es else T['texto3'], TITULOS, True, inter=1.1)
        pila(sl, x + 250, yy + 24, cw - 250, fila - 30, [
            dict(t=it.get('titulo', ''), px=s_t, color=T['texto'], fam=TITULOS, b=True, inter=1.1, track=-0.01),
            dict(t=it.get('detalle'), px=s_d, color=T['texto2'], inter=1.3, antes=6)])

def d_logos(sl, T, d):
    """Patrocinadores o colaboradores: logos en tarjetas blancas (los logos ajenos siempre sobre blanco), agrupados por nivel."""
    y = titular(sl, T, d.get('titulo', 'Gracias a'))
    grupos = d.get('niveles') or [{'nivel': None, 'logos': d.get('logos', [])}]
    gap = 24; yy = y
    alto_total = H - M - y
    n_grupos = len(grupos); etq = 52
    for gi, g in enumerate(grupos):
        logos = g.get('logos', [])
        if not logos: continue
        n = len(logos); cols = min(n, 4 if gi == 0 and n_grupos > 1 else 5); filas = -(-n // cols)
        disp = alto_total / n_grupos - (etq if g.get('nivel') else 0) - gap
        ch = min(260 if gi == 0 else 200, (disp - gap * (filas - 1)) / filas)
        cw = (W - 2 * M - gap * (cols - 1)) / cols
        if n_grupos == 1 and not g.get('nivel'):                                     # un solo grupo: centrado en vertical
            yy = y + (alto_total - (filas * ch + (filas - 1) * gap)) * 0.4
        if g.get('nivel'): caja(sl, M, yy, 800, 40, g['nivel'], 30, T['texto3']); yy += etq
        for i, lg in enumerate(logos):
            x = M + (i % cols) * (cw + gap); y2 = yy + (i // cols) * (ch + gap)
            rect(sl, x, y2, cw, ch, '#FFFFFF', radio=24, borde=None if T['id'] != 'claro' else '#E3E3E8')
            ruta = lg if isinstance(lg, str) else lg.get('imagen', '')
            nombre = ((lg.get('nombre') if isinstance(lg, dict) else None) or os.path.splitext(os.path.basename(ruta))[0]).strip('[]')
            if ruta and os.path.exists(ruta):
                iw, ih = tam(ruta); k = min((cw - 96) / iw, (ch - 72) / ih); w2, h2 = iw * k, ih * k
                imagen(sl, ruta, x + (cw - w2) / 2, y2 + (ch - h2) / 2, w2, h2)
            else:
                caja(sl, x, y2, cw, ch, '[' + (nombre or 'logo') + ']', 28, '#6E6E78', alinear='centro', ancla='centro')
        yy += filas * ch + (filas - 1) * gap + gap * 2

TIPOS = {'portada': d_portada, 'hola': d_hola, 'frase': d_frase, 'texto': d_texto, 'tarjetas': d_tarjetas, 'cifras': d_cifras,
         'imagen': d_imagen, 'codigo': d_codigo, 'pregunta': d_pregunta, 'persona': d_persona, 'cierre': d_cierre,
         'espera': d_espera, 'agenda': d_agenda, 'logos': d_logos}

def registrar_notas(prs):
    """python-pptx crea la plantilla de notas pero no la apunta en presentation.xml; Keynote rechaza el archivo sin ese índice.
    También quita el tipo "screen4x3" del tamaño de diapositiva, que no corresponde a 16:9."""
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    from pptx.oxml.ns import qn
    p = prs.part._element
    sz = p.find(qn('p:sldSz'))
    if sz is not None and 'type' in sz.attrib: del sz.attrib['type']
    rid = next((r.rId for r in prs.part.rels.values() if r.reltype == RT.NOTES_MASTER), None)
    if not rid or p.find(qn('p:notesMasterIdLst')) is not None: return
    lst = p.makeelement(qn('p:notesMasterIdLst'), {}); nm = lst.makeelement(qn('p:notesMasterId'), {qn('r:id'): rid}); lst.append(nm)
    p.find(qn('p:sldMasterIdLst')).addnext(lst)

def construir(guion, salida, base=None):
    prs = Presentation(); prs.slide_width, prs.slide_height = E(W), E(H)
    vacio = prs.slide_layouts[6]
    tema_def = guion.get('tema', 'claro'); color_def = guion.get('color') or CONTENIDO.get(str(guion.get('contenido', '')).lower())
    for d in guion['diapositivas']:
        sl = prs.slides.add_slide(vacio)
        acento = d.get('color') or color_def or 'azul'
        acento = CONTENIDO.get(acento, acento)
        T = tema(d.get('tema', tema_def), acento)
        imagen(sl, fondo_png(T), 0, 0, W, H)
        if base and d.get('imagen') and not os.path.isabs(d['imagen']): d['imagen'] = os.path.join(base, d['imagen'])
        if base and d.get('foto') and not os.path.isabs(d['foto']): d['foto'] = os.path.join(base, d['foto'])
        if base:
            def abs_(l): return (os.path.join(base, l) if isinstance(l, str) and not os.path.isabs(l) else
                                 dict(l, imagen=os.path.join(base, l['imagen'])) if isinstance(l, dict) and l.get('imagen') and not os.path.isabs(l['imagen']) else l)
            if d.get('logos'): d['logos'] = [abs_(l) for l in d['logos']]
            for g in d.get('niveles') or []: g['logos'] = [abs_(l) for l in g.get('logos', [])]
        if d.get('tipo') not in TIPOS: print(f"aviso: tipo desconocido '{d.get('tipo')}', se maqueta como texto", file=sys.stderr)
        TIPOS.get(d.get('tipo'), d_texto)(sl, T, d)
        if d.get('notas'): sl.notes_slide.notes_text_frame.text = d['notas']
    prs.core_properties.title = guion.get('titulo', 'hola Swift')
    registrar_notas(prs)
    prs.save(salida)
    return len(guion['diapositivas'])

if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(__doc__)
    g = json.load(open(sys.argv[1], encoding='utf-8'))
    n = construir(g, sys.argv[2], base=os.path.dirname(os.path.abspath(sys.argv[1])))
    print(f'ok · {n} diapositivas → {sys.argv[2]}')
