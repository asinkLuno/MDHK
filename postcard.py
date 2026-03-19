"""
明信片生成工具

用法：
  python postcard.py          # 生成两张明信片
  python postcard.py 1        # 只生成版本1（手写文字版）
  python postcard.py 2        # 只生成版本2（独角兽版）
"""

import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1800, 1200


# ── 公共工具函数 ──────────────────────────────────────────────────────────────


def make_white_transparent(img: Image.Image, threshold: int = 210) -> Image.Image:
    img = img.convert("RGBA")
    data = np.array(img, dtype=np.uint8)
    r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
    white_mask = (r > threshold) & (g > threshold) & (b > threshold)
    data[:, :, 3] = np.where(white_mask, 0, a)
    return Image.fromarray(data, "RGBA")


def draw_dashed_rect(draw, x, y, w, h, dash=10, gap=10, color="black", width=3):
    for side in ["top", "bottom", "left", "right"]:
        if side in ("top", "bottom"):
            yy = y if side == "top" else y + h
            pos = x
            while pos < x + w:
                draw.line(
                    [(pos, yy), (min(pos + dash, x + w), yy)], fill=color, width=width
                )
                pos += dash + gap
        else:
            xx = x if side == "left" else x + w
            pos = y
            while pos < y + h:
                draw.line(
                    [(xx, pos), (xx, min(pos + dash, y + h))], fill=color, width=width
                )
                pos += dash + gap


def draw_postal_code(
    card: Image.Image,
    draw: ImageDraw.ImageDraw,
    postal_code: str = "999077",
    cell_xs: list = None,
    cell_y: int = 100,
    cell_size: int = 60,
):
    """在邮编格子里绘制手写风格数字"""
    if cell_xs is None:
        cell_xs = [1000, 1080, 1160, 1240, 1320, 1400]

    try:
        font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Oblique.ttf", 40)
    except Exception:
        font = ImageFont.load_default()

    rng = random.Random(42)

    for x in cell_xs:
        draw.rectangle(
            [x, cell_y, x + cell_size, cell_y + cell_size], outline="black", width=3
        )

    for i, x in enumerate(cell_xs):
        digit = postal_code[i]
        tmp = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
        tmp_draw = ImageDraw.Draw(tmp)
        bbox = tmp_draw.textbbox((0, 0), digit, font=font)
        dw, dh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tmp_draw.text(
            ((80 - dw) // 2, (80 - dh) // 2), digit, fill=(20, 20, 80, 255), font=font
        )
        angle = rng.uniform(-12, 12)
        tmp = tmp.rotate(angle, resample=Image.BICUBIC, expand=False)
        tmp = tmp.filter(ImageFilter.GaussianBlur(radius=0.6))
        dx = rng.randint(-4, 4)
        dy = rng.randint(-4, 4)
        px = x + (cell_size - 80) // 2 + dx
        py = cell_y + (cell_size - 80) // 2 + dy
        card.paste(tmp, (px, py), tmp)


# ── 版本1：手写文字版 ──────────────────────────────────────────────────────────


def build_v1():
    card = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(card)

    draw.rectangle([0, 0, W - 1, H - 1], outline="black", width=4)
    draw.line([(900, 150), (900, 1050)], fill="black", width=3)
    draw_dashed_rect(draw, 1450, 100, 240, 270)
    draw_postal_code(card, draw)

    for y in [600, 750, 900]:
        draw.line([(1000, y), (1650, y)], fill="black", width=3)

    # 左侧：手写文字
    text_img = Image.open("letter_text.png").convert("RGBA")
    tw, th = text_img.size
    scale = min(840 / tw, 1020 / th)
    text_img = text_img.resize((int(tw * scale), int(th * scale)), Image.LANCZOS)
    text_img = make_white_transparent(text_img, threshold=230)
    card.paste(
        text_img, ((900 - text_img.width) // 2, (H - text_img.height) // 2), text_img
    )

    # 邮票
    stamp = Image.open("stamp_photo.jpg").convert("RGBA")
    stamp = stamp.resize((236, 266), Image.LANCZOS)
    card.paste(stamp, (1452, 102), stamp)

    # 广州邮戳
    gz = Image.open("postmark_guangzhou.png").convert("RGBA")
    gz = gz.resize((300, 300), Image.LANCZOS)
    gz = make_white_transparent(gz, threshold=200)
    card.paste(gz, (1350, 230), gz)

    # 香港邮戳
    hk = Image.open("postmark_hongkong.png").convert("RGBA")
    hk_w, hk_h = hk.size
    hk = hk.resize((int(hk_w * 340 / hk_h), 340), Image.LANCZOS)
    hk = make_white_transparent(hk, threshold=200)
    card.paste(hk, (930, 370), hk)

    # 线稿人物
    fans = Image.open("fans.png").convert("RGBA")
    fans_w, fans_h = fans.size
    fans = fans.resize((int(fans_w * 320 / fans_h), 320), Image.LANCZOS)
    card.paste(fans, (W - fans.width - 50, H - fans.height - 50), fans)

    card.save("postcard_final_1.png", "PNG")
    print(f"已保存：postcard_final_1.png  ({W}×{H})")

    # 拼接封面（调整封面宽度与明信片一致）
    cover = Image.open("cover_1.jpg").convert("RGB")
    cover = cover.resize((W, int(cover.height * W / cover.width)), Image.LANCZOS)
    final = Image.new("RGB", (W, H + cover.height), "white")
    final.paste(cover, (0, 0))
    final.paste(card, (0, cover.height))
    final.save("postcard_final_1_with_cover.png", "PNG")
    print("已保存：postcard_final_1_with_cover.png（已拼接封面）")


# ── 版本2：独角兽版 ───────────────────────────────────────────────────────────


def build_v2():
    card = Image.new("RGBA", (W, H), (255, 255, 255, 255))

    # 独角兽线稿（75% 高度，贴底）
    unicorn = Image.open("unicorn.png").convert("RGBA")
    uw, uh = unicorn.size
    target_h = int(H * 0.75)
    unicorn = unicorn.resize((int(uw * target_h / uh), target_h), Image.LANCZOS)
    card.paste(unicorn, (0, H - target_h), unicorn)

    draw = ImageDraw.Draw(card)
    draw.rectangle([0, 0, W - 1, H - 1], outline="black", width=4)
    draw.line([(900, 150), (900, 1050)], fill="black", width=3)
    draw_dashed_rect(draw, 1450, 100, 240, 270, color="black", width=3)

    for y in [600, 750, 900]:
        draw.line([(1000, y), (1650, y)], fill="black", width=3)

    draw_postal_code(card, draw)

    # 任意门邮票
    stamp_x, stamp_y, stamp_w, stamp_h = 1450, 100, 240, 270
    anywhere_door = Image.open("stamp_anywhere_door.jpg").convert("RGBA")
    anywhere_door = anywhere_door.resize((stamp_w, stamp_h), Image.LANCZOS)
    card.paste(anywhere_door, (stamp_x, stamp_y), anywhere_door)

    # 广州邮戳
    gz = Image.open("postmark_guangzhou.png").convert("RGBA")
    gz = gz.resize((300, 300), Image.LANCZOS)
    gz = make_white_transparent(gz, threshold=210)
    card.paste(gz, (stamp_x - 80, stamp_y + stamp_h - 100), gz)

    # 香港邮戳
    hk = Image.open("postmark_hongkong.png").convert("RGBA")
    hk_w, hk_h = hk.size
    target_h = 300
    hk = hk.resize((int(hk_w * target_h / hk_h), target_h), Image.LANCZOS)
    hk = make_white_transparent(hk, threshold=210)
    card.paste(hk, (W - hk.width - 60, H - target_h - 60), hk)

    card.convert("RGB").save("postcard_final_2.png", "PNG")
    print(f"已保存：postcard_final_2.png  ({W}×{H})")

    # 拼接封面（调整封面宽度与明信片一致）
    cover = Image.open("cover_2.jpg").convert("RGB")
    cover = cover.resize((W, int(cover.height * W / cover.width)), Image.LANCZOS)
    final = Image.new("RGB", (W, H + cover.height), "white")
    final.paste(cover, (0, 0))
    final.paste(card, (0, cover.height))
    final.save("postcard_final_2_with_cover.png", "PNG")
    print("已保存：postcard_final_2_with_cover.png（已拼接封面）")


# ── 入口 ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "1":
        build_v1()
    elif arg == "2":
        build_v2()
    else:
        build_v1()
        build_v2()
