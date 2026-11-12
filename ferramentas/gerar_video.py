"""Gera um Short vertical (1080x1920, 30fps) de um produto do Achados do Litoral.
Uso: python3 gerar_video.py produto.json saida.mp4
produto.json: {"nome","linha1","linha2","foto","preco","de","pix","nota","vendidos","detalhes":[...],"selo"}
"""
import json, os, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BG = (14, 23, 25); SURF = (21, 34, 37); ACC = (11, 122, 117); ACC2 = (40, 190, 180)
DEAL = (226, 85, 61); GOLD = (255, 200, 61); WHITE = (255, 255, 255); MUTED = (160, 178, 182)
FD = "/usr/share/fonts/opentype/inter/"
def F(sz, w="ExtraBold"): return ImageFont.truetype(f"{FD}Inter-{w}.otf", sz)

def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def brl(v): return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def ctext(d, y, txt, font, fill, x=W // 2):
    w = d.textlength(txt, font=font); d.text((x - w / 2, y), txt, font=font, fill=fill)

def fundo(t):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    # faixas diagonais suaves que se movem
    for i in range(-3, 8):
        x = (i * 260 + t * 40) % (W + 520) - 260
        d.polygon([(x, 0), (x + 90, 0), (x - 500, H), (x - 590, H)], fill=(17, 29, 32))
    return im

def cartao_foto(foto, lado):
    card = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    m = Image.new("L", (lado, lado), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, lado, lado), 48, fill=255)
    base = Image.new("RGB", (lado, lado), WHITE)
    f = foto.copy(); f.thumbnail((int(lado * .9), int(lado * .9)), Image.LANCZOS)
    f = foto.resize((int(lado * .9), int(lado * .9)), Image.LANCZOS) if foto.width < lado * .9 else f
    base.paste(f, ((lado - f.width) // 2, (lado - f.height) // 2), f if f.mode == "RGBA" else None)
    card.paste(base, (0, 0), m); return card

def cola(im, card, cx, cy, esc=1.0, sombra=True):
    if esc != 1.0: card = card.resize((max(1, int(card.width * esc)), max(1, int(card.height * esc))), Image.LANCZOS)
    x, y = int(cx - card.width / 2), int(cy - card.height / 2)
    if sombra:
        s = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(s).rounded_rectangle((x + 10, y + 30, x + card.width + 10, y + card.height + 30), 48, fill=(0, 0, 0, 140))
        im.paste(s.filter(ImageFilter.GaussianBlur(30)), (0, 0), s.filter(ImageFilter.GaussianBlur(30)))
    im.paste(card, (x, y), card)

def selo(d, t, txt):
    a = ease(t / .4); y = int(-120 + 230 * a)
    w = d.textlength(txt, font=F(64, "Black")) + 80
    d.rounded_rectangle((W / 2 - w / 2, y, W / 2 + w / 2, y + 100), 50, fill=GOLD)
    ctext(d, y + 14, txt, F(64, "Black"), BG)

def rodape(d):
    ctext(d, H - 110, "achadosdolitoral.com.br", F(40, "SemiBold"), MUTED)

def cena(nome, dur, desenha, out):
    tmp = out + ".tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    n = int(dur * FPS)
    for i in range(n): p.stdin.write(desenha(i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)
    else: sys.exit(f"falhou cena {nome}")

def principal(cfg, saida, so_quadros=False):
    foto = Image.open(cfg["foto"]).convert("RGBA")
    card = cartao_foto(foto, 820)
    selo_txt = cfg.get("selo", "BLACK FRIDAY")
    off = round((1 - cfg["preco"] / cfg["de"]) * 100) if cfg.get("de") else 0
    wrap = lambda s: [s]  # linhas já vêm separadas no json

    def c1(t, dur):  # gancho
        im = fundo(t); d = ImageDraw.Draw(im); selo(d, t, selo_txt)
        e = ease((t - .2) / .6)
        cola(im, card, W / 2, 900, .6 + .4 * e)
        if off:
            a = ease((t - .7) / .3); r = int(140 * a)
            if r > 4:
                d.ellipse((W / 2 + 280 - r, 520 - r, W / 2 + 280 + r, 520 + r), fill=DEAL)
                ctext(d, 520 - 46, f"-{off}%", F(int(76 * a) or 1, "Black"), WHITE, x=W / 2 + 280)
        a = ease((t - 1.0) / .4)
        ctext(d, 1400 + (1 - a) * 60, "ACHADO DO DIA", F(110, "Black"), tuple(int(c * a + b * (1 - a)) for c, b in zip(WHITE, BG)))
        rodape(d); return im.convert("RGB")

    def c2(t, dur):  # produto + nome
        im = fundo(t + 3); d = ImageDraw.Draw(im)
        cola(im, card, W / 2, 760, 1.0 + .04 * t / dur)
        for k, linha in enumerate([cfg["linha1"], cfg["linha2"]]):
            a = ease((t - .2 - k * .25) / .4)
            ctext(d, 1270 + k * 100 + (1 - a) * 40, linha, F(78 if k == 0 else 62, "ExtraBold" if k == 0 else "SemiBold"),
                  tuple(int(c * a + b * (1 - a)) for c, b in zip(WHITE if k == 0 else ACC2, BG)))
        if cfg.get("nota"):
            a = ease((t - .8) / .4)
            txt = f"★ {str(cfg['nota']).replace('.', ',')}   ·   {cfg.get('vendidos','')} vendidos"
            ctext(d, 1520, txt, F(54, "Bold"), tuple(int(c * a + b * (1 - a)) for c, b in zip(GOLD, BG)))
        rodape(d); return im.convert("RGB")

    def c3(t, dur):  # detalhes
        im = fundo(t + 7); d = ImageDraw.Draw(im)
        cola(im, card, W / 2, 520, .62)
        ctext(d, 930, "Por que vale a pena", F(70, "Black"), WHITE)
        for k, txt in enumerate(cfg["detalhes"]):
            a = ease((t - .3 - k * .7) / .4); y = 1080 + k * 170
            if a <= 0: continue
            x0 = 90 + (1 - a) * -80
            d.rounded_rectangle((x0, y, x0 + W - 180, y + 140), 32, fill=SURF)
            d.ellipse((x0 + 34, y + 40, x0 + 94, y + 100), fill=ACC)
            d.line((x0 + 50, y + 70, x0 + 61, y + 82, x0 + 80, y + 58), fill=WHITE, width=8)
            d.text((x0 + 124, y + 42), txt, font=F(52, "Bold"), fill=WHITE)
        rodape(d); return im.convert("RGB")

    def c4(t, dur):  # preço
        im = fundo(t + 13); d = ImageDraw.Draw(im); selo(d, t, selo_txt)
        cola(im, card, W / 2, 680, .7)
        if cfg.get("de"):
            a = ease((t - .2) / .3); txt = "De " + brl(cfg["de"]); f = F(66, "SemiBold")
            ctext(d, 1110, txt, f, tuple(int(c * a + b * (1 - a)) for c, b in zip(MUTED, BG)))
            w = d.textlength(txt, font=f); s = ease((t - .6) / .3)
            if s > 0: d.line((W / 2 - w / 2 - 10, 1150, W / 2 - w / 2 - 10 + (w + 20) * s, 1150), fill=DEAL, width=8)
        a = ease((t - .9) / .35); esc = .7 + .3 * a + .04 * math.sin(max(0, t - 1.3) * 5) * (t > 1.3)
        f = F(max(1, int(150 * esc)), "Black"); txt = brl(cfg["preco"])
        ctext(d, 1215 + (150 - 150 * esc) / 2, txt, f, tuple(int(c * a + b * (1 - a)) for c, b in zip(GOLD, BG)))
        if cfg.get("pix"):
            ctext(d, 1400, "no Pix", F(56, "Bold"), tuple(int(c * a + b * (1 - a)) for c, b in zip(WHITE, BG)))
        if off:
            a2 = ease((t - 1.4) / .3)
            if a2 > 0:
                txt = f"Economia de {brl(cfg['de'] - cfg['preco'])}"; w = d.textlength(txt, font=F(52, "ExtraBold")) + 70
                d.rounded_rectangle((W / 2 - w / 2, 1510, W / 2 + w / 2, 1600), 45, fill=DEAL)
                ctext(d, 1525, txt, F(52, "ExtraBold"), WHITE)
        rodape(d); return im.convert("RGB")

    def c5(t, dur):  # chamada
        im = fundo(t + 18); d = ImageDraw.Draw(im)
        cola(im, card, W / 2, 600, .55)
        a = ease(t / .4)
        ctext(d, 940, "Corre que o preço", F(84, "Black"), WHITE); ctext(d, 1040, "pode mudar!", F(84, "Black"), GOLD)
        p = .5 + .5 * math.sin(t * 6)
        bw = 820; by = 1250
        d.rounded_rectangle((W / 2 - bw / 2 - 6 * p, by - 6 * p, W / 2 + bw / 2 + 6 * p, by + 150 + 6 * p), 75, fill=ACC)
        ctext(d, by + 38, "👉 LINK NA DESCRIÇÃO".replace("👉 ", ""), F(66, "Black"), WHITE)
        ctext(d, 1470, "Mais achados em", F(50, "SemiBold"), MUTED)
        ctext(d, 1535, "achadosdolitoral.com.br", F(62, "ExtraBold"), ACC2)
        ctext(d, 1720, "Sou afiliado do Mercado Livre · preço pode mudar", F(34, "SemiBold"), MUTED)
        return im.convert("RGB")

    cenas = [("c1", 3.0, c1), ("c2", 4.0, c2), ("c3", 1.2 + .7 * len(cfg["detalhes"]) + 2.0, c3), ("c4", 4.5, c4), ("c5", 3.5, c5)]
    pasta = saida + "_cenas"; os.makedirs(pasta, exist_ok=True)
    if so_quadros:
        for nome, dur, fn in cenas: fn(dur * .85, dur).save(f"{pasta}/{nome}.jpg", quality=88)
        return
    arqs = []
    for nome, dur, fn in cenas:
        o = f"{pasta}/{nome}.mp4"; cena(nome, dur, fn, o); arqs.append(o)
    with open(f"{pasta}/lista.txt", "w") as fl: fl.writelines(f"file '{os.path.abspath(a)}'\n" for a in arqs)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{pasta}/lista.txt", "-c", "copy", "-movflags", "+faststart", saida], check=True)

if __name__ == "__main__":
    principal(json.load(open(sys.argv[1])), sys.argv[2], so_quadros="--quadros" in sys.argv)
