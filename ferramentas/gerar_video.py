"""Gera um Short vertical (1080x1920, 30fps) de um produto do Achados do Litoral.
Uso: python3 gerar_video.py produto.json saida.mp4  (prévia: --quadros [--zonas mostra a área coberta pelo YouTube])
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

# Área segura dos Shorts: o YouTube cobre a coluna de botões à direita (x > ~900 a partir de y ~880)
# e a faixa de baixo (canal, título, botões) a partir de y ~1480. Todo texto/foto fica dentro disso.
SAFE_W = 700          # largura máxima de texto centralizado (x 190–890)
SAFE_BOTTOM = 1440    # nada importante abaixo disso

def ctext(d, y, txt, font, fill, x=W // 2, maxw=SAFE_W):
    w = d.textlength(txt, font=font)
    if w > maxw:  # diminui a fonte até caber na área segura
        sz = font.size
        while w > maxw and sz > 20:
            sz -= 2; font = font.font_variant(size=sz); w = d.textlength(txt, font=font)
    d.text((x - w / 2, y), txt, font=font, fill=fill)

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

def rodape(d, y=1390):
    ctext(d, y, "achadosdolitoral.com.br", F(40, "SemiBold"), MUTED)

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
        cola(im, card, W / 2, 740, .5 + .28 * e)
        if off:
            a = ease((t - .7) / .3); r = int(125 * a)
            if r > 4:
                d.ellipse((W / 2 + 250 - r, 450 - r, W / 2 + 250 + r, 450 + r), fill=DEAL)
                ctext(d, 450 - 42, f"-{off}%", F(int(70 * a) or 1, "Black"), WHITE, x=W / 2 + 250, maxw=220)
        a = ease((t - 1.0) / .4)
        ctext(d, 1130 + (1 - a) * 60, "ACHADO DO DIA", F(104, "Black"), tuple(int(c * a + b * (1 - a)) for c, b in zip(WHITE, BG)))
        rodape(d, 1300); return im.convert("RGB")

    def c2(t, dur):  # produto + nome
        im = fundo(t + 3); d = ImageDraw.Draw(im)
        cola(im, card, W / 2, 640, .8 + .03 * t / dur)
        for k, linha in enumerate([cfg["linha1"], cfg["linha2"]]):
            a = ease((t - .2 - k * .25) / .4)
            ctext(d, 1040 + k * 100 + (1 - a) * 40, linha, F(78 if k == 0 else 62, "ExtraBold" if k == 0 else "SemiBold"),
                  tuple(int(c * a + b * (1 - a)) for c, b in zip(WHITE if k == 0 else ACC2, BG)))
        if cfg.get("nota"):
            a = ease((t - .8) / .4)
            txt = f"★ {str(cfg['nota']).replace('.', ',')}   ·   {cfg.get('vendidos','')} vendidos"
            ctext(d, 1250, txt, F(54, "Bold"), tuple(int(c * a + b * (1 - a)) for c, b in zip(GOLD, BG)))
        rodape(d); return im.convert("RGB")

    def c3(t, dur):  # detalhes
        im = fundo(t + 7); d = ImageDraw.Draw(im)
        cola(im, card, W / 2, 440, .5)
        ctext(d, 700, "Por que vale a pena", F(70, "Black"), WHITE)
        n = max(1, len(cfg["detalhes"])); passo = min(150, (SAFE_BOTTOM - 810) // n); alt = passo - 22
        for k, txt in enumerate(cfg["detalhes"]):
            a = ease((t - .3 - k * .7) / .4); y = 810 + k * passo
            if a <= 0: continue
            x0 = 160 + (1 - a) * -80; bw = 730  # caixa de x 160 a 890, longe dos botões
            d.rounded_rectangle((x0, y, x0 + bw, y + alt), 32, fill=SURF)
            cy = y + alt / 2
            d.ellipse((x0 + 28, cy - 28, x0 + 84, cy + 28), fill=ACC)
            d.line((x0 + 42, cy, x0 + 52, cy + 11, x0 + 70, cy - 11), fill=WHITE, width=8)
            f = F(48, "Bold"); sz = 48
            while d.textlength(txt, font=f) > bw - 140 and sz > 24: sz -= 2; f = f.font_variant(size=sz)
            d.text((x0 + 110, cy - sz * .62), txt, font=f, fill=WHITE)
        return im.convert("RGB")

    def c4(t, dur):  # preço
        im = fundo(t + 13); d = ImageDraw.Draw(im); selo(d, t, selo_txt)
        cola(im, card, W / 2, 590, .6)
        if cfg.get("de"):
            a = ease((t - .2) / .3); txt = "De " + brl(cfg["de"]); f = F(66, "SemiBold")
            ctext(d, 900, txt, f, tuple(int(c * a + b * (1 - a)) for c, b in zip(MUTED, BG)))
            w = d.textlength(txt, font=f); s = ease((t - .6) / .3)
            if s > 0: d.line((W / 2 - w / 2 - 10, 940, W / 2 - w / 2 - 10 + (w + 20) * s, 940), fill=DEAL, width=8)
        a = ease((t - .9) / .35); esc = .7 + .3 * a + .04 * math.sin(max(0, t - 1.3) * 5) * (t > 1.3)
        f = F(max(1, int(150 * esc)), "Black"); txt = brl(cfg["preco"])
        ctext(d, 985 + (150 - 150 * esc) / 2, txt, f, tuple(int(c * a + b * (1 - a)) for c, b in zip(GOLD, BG)))
        if cfg.get("pix"):
            ctext(d, 1165, "no Pix", F(56, "Bold"), tuple(int(c * a + b * (1 - a)) for c, b in zip(WHITE, BG)))
        if off:
            a2 = ease((t - 1.4) / .3)
            if a2 > 0:
                txt = f"Economia de {brl(cfg['de'] - cfg['preco'])}"; w = d.textlength(txt, font=F(52, "ExtraBold")) + 70
                w = min(w, SAFE_W)
                d.rounded_rectangle((W / 2 - w / 2, 1255, W / 2 + w / 2, 1345), 45, fill=DEAL)
                ctext(d, 1270, txt, F(52, "ExtraBold"), WHITE, maxw=SAFE_W - 70)
        rodape(d, 1385); return im.convert("RGB")

    def c5(t, dur):  # chamada
        im = fundo(t + 18); d = ImageDraw.Draw(im)
        cola(im, card, W / 2, 430, .46)
        a = ease(t / .4)
        ctext(d, 700, "Corre que o preço", F(84, "Black"), WHITE); ctext(d, 800, "pode mudar!", F(84, "Black"), GOLD)
        p = .5 + .5 * math.sin(t * 6)
        bw = 680; by = 950
        d.rounded_rectangle((W / 2 - bw / 2 - 6 * p, by - 6 * p, W / 2 + bw / 2 + 6 * p, by + 150 + 6 * p), 75, fill=ACC)
        ctext(d, by + 38, "👉 LINK NA DESCRIÇÃO".replace("👉 ", ""), F(66, "Black"), WHITE)
        ctext(d, 1160, "Mais achados em", F(50, "SemiBold"), MUTED)
        ctext(d, 1225, "achadosdolitoral.com.br", F(62, "ExtraBold"), ACC2)
        ctext(d, 1340, "Sou afiliado do Mercado Livre · preço pode mudar", F(34, "SemiBold"), MUTED)
        return im.convert("RGB")

    cenas = [("c1", 3.0, c1), ("c2", 4.0, c2), ("c3", 1.2 + .7 * len(cfg["detalhes"]) + 2.0, c3), ("c4", 4.5, c4), ("c5", 3.5, c5)]
    pasta = saida + "_cenas"; os.makedirs(pasta, exist_ok=True)
    if so_quadros:
        for nome, dur, fn in cenas:
            q = fn(dur * .85, dur)
            if "--zonas" in sys.argv:  # mostra em vermelho onde o YouTube põe botões/título
                z = Image.new("RGBA", q.size, (0, 0, 0, 0)); zd = ImageDraw.Draw(z)
                zd.rectangle((900, 880, W, H), fill=(255, 0, 0, 90)); zd.rectangle((0, 1480, W, H), fill=(255, 0, 0, 90))
                zd.rectangle((0, 0, W, 90), fill=(255, 0, 0, 90))
                q = Image.alpha_composite(q.convert("RGBA"), z).convert("RGB")
            q.save(f"{pasta}/{nome}.jpg", quality=88)
        return
    arqs = []
    for nome, dur, fn in cenas:
        o = f"{pasta}/{nome}.mp4"; cena(nome, dur, fn, o); arqs.append(o)
    with open(f"{pasta}/lista.txt", "w") as fl: fl.writelines(f"file '{os.path.abspath(a)}'\n" for a in arqs)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{pasta}/lista.txt", "-c", "copy", "-movflags", "+faststart", saida], check=True)

if __name__ == "__main__":
    principal(json.load(open(sys.argv[1])), sys.argv[2], so_quadros="--quadros" in sys.argv)
