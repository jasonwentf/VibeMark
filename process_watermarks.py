#!/usr/bin/env python3
import os
import json
from PIL import Image
import numpy as np

ASSETS_DIR = "assets"
OUTPUT_DIR = "assets/processed"

def black_to_rgba(img):
    arr = np.array(img.convert('RGBA'))
    brightness = np.maximum(np.maximum(arr[:,:,0], arr[:,:,1]), arr[:,:,2])
    arr[:,:,0] = 255
    arr[:,:,1] = 255
    arr[:,:,2] = 255
    arr[:,:,3] = brightness
    return Image.fromarray(arr)

def colored_to_rgba(img):
    arr = np.array(img.convert('RGBA'))
    # If the source already has meaningful alpha (common for colored PNG watermarks),
    # preserve it. Deriving alpha from RGB can accidentally resurrect hidden RGB in
    # fully-transparent pixels and create smear/block artifacts.
    alpha = arr[:, :, 3]
    if np.any(alpha < 255):
        return Image.fromarray(arr)

    brightness = np.maximum(np.maximum(arr[:, :, 0], arr[:, :, 1]), arr[:, :, 2])
    arr[:, :, 3] = brightness
    return Image.fromarray(arr)


def to_rgba(img, colored=False):
    """Convert to RGBA suitable for watermark extraction.

    If the source image already has meaningful alpha, preserve it.
    Otherwise treat it as a black-background watermark and derive alpha from brightness.
    """
    rgba = img.convert('RGBA')
    alpha = np.array(rgba)[:, :, 3]
    if np.any(alpha < 255):
        return rgba
    return colored_to_rgba(img) if colored else black_to_rgba(img)

def find_content_bounds(img, alpha_threshold=10):
    arr = np.array(img)
    if arr.shape[2] < 4:
        return None
    alpha = arr[:,:,3]
    rows = np.any(alpha > alpha_threshold, axis=1)  # 阈值避免噪点/暗纹
    cols = np.any(alpha > alpha_threshold, axis=0)
    if not np.any(rows) or not np.any(cols):
        return None
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    return (cmin, rmin, cmax + 1, rmax + 1)  # (left, top, right, bottom)

def extract_watermark(input_path, output_name, template_size, padding=5, colored=False, force_anchor=None, alpha_threshold=10):
    print(f"处理: {input_path}")
    img = Image.open(input_path)
    orig_w, orig_h = img.size
    
    rgba = to_rgba(img, colored=colored)
    bounds = find_content_bounds(rgba, alpha_threshold=alpha_threshold)
    
    if bounds is None:
        print(f"  警告: 未找到内容")
        return None
    
    left, top, right, bottom = bounds

    # Expand bounds by padding and use the padded box consistently for
    # both the saved PNG size and the config width/height/margins.
    pad_left = max(0, left - padding)
    pad_top = max(0, top - padding)
    pad_right = min(orig_w, right + padding)
    pad_bottom = min(orig_h, bottom + padding)
    
    # 裁切水印图标
    cropped = rgba.crop((pad_left, pad_top, pad_right, pad_bottom))
    
    # 计算位置信息（相对于模板尺寸的比例）
    wm_w = pad_right - pad_left
    wm_h = pad_bottom - pad_top
    
    # 判断锚点位置
    center_x = (pad_left + pad_right) / 2
    center_y = (pad_top + pad_bottom) / 2
    
    if center_x < orig_w / 3:
        anchor_x = 'left'
        margin_x = pad_left
    elif center_x > orig_w * 2 / 3:
        anchor_x = 'right'
        margin_x = orig_w - pad_right
    else:
        anchor_x = 'center'
        margin_x = 0
    
    if center_y < orig_h / 3:
        anchor_y = 'top'
        margin_y = pad_top
    elif center_y > orig_h * 2 / 3:
        anchor_y = 'bottom'
        margin_y = orig_h - pad_bottom
    else:
        anchor_y = 'center'
        margin_y = 0
    
    if force_anchor:
        parts = force_anchor.split('-')
        if len(parts) != 2:
            raise ValueError(f"Invalid force_anchor: {force_anchor}")
        anchor_y, anchor_x = parts[0], parts[1]

        if anchor_x == 'left':
            margin_x = pad_left
        elif anchor_x == 'right':
            margin_x = orig_w - pad_right
        else:
            margin_x = 0

        if anchor_y == 'top':
            margin_y = pad_top
        elif anchor_y == 'bottom':
            margin_y = orig_h - pad_bottom
        else:
            margin_y = 0

    anchor = f"{anchor_y}-{anchor_x}"
    
    # 保存
    output_path = os.path.join(OUTPUT_DIR, output_name)
    cropped.save(output_path, 'PNG')
    
    config = {
        'file': output_name,
        'templateSize': template_size,
        'anchor': anchor,
        'width': int(wm_w),
        'height': int(wm_h),
        'marginX': int(margin_x),
        'marginY': int(margin_y),
        'marginXRatio': float(margin_x / orig_w),
        'marginYRatio': float(margin_y / orig_h),
        'widthRatio': float(wm_w / orig_w),
        'heightRatio': float(wm_h / orig_h),
    }
    
    print(f"  保存: {output_path} ({cropped.size[0]}x{cropped.size[1]})")
    print(f"  位置: {anchor}, 边距: ({margin_x}, {margin_y}), 尺寸: {wm_w}x{wm_h}")
    
    return config

def extract_jimeng_dual(input_path, template_size):
    """分割即梦双水印"""
    print(f"处理即梦双水印: {input_path}")
    img = Image.open(input_path)
    orig_w, orig_h = img.size
    rgba = to_rgba(img, colored=False)
    
    configs = []
    
    # 左上角区域 (上半部分左半)
    topleft_region = rgba.crop((0, 0, orig_w // 2, orig_h // 2))
    bounds = find_content_bounds(topleft_region)
    if bounds:
        left, top, right, bottom = bounds
        padding = 5
        cropped = topleft_region.crop((
            max(0, left - padding),
            max(0, top - padding),
            min(orig_w // 2, right + padding),
            min(orig_h // 2, bottom + padding)
        ))
        cropped.save(os.path.join(OUTPUT_DIR, "jimeng-topleft.png"), 'PNG')
        configs.append({
            'file': 'jimeng-topleft.png',
            'templateSize': template_size,
            'anchor': 'top-left',
            'width': int(right - left),
            'height': int(bottom - top),
            'marginX': int(left),
            'marginY': int(top),
            'marginXRatio': float(left / orig_w),
            'marginYRatio': float(top / orig_h),
            'widthRatio': float((right - left) / orig_w),
            'heightRatio': float((bottom - top) / orig_h),
        })
        print(f"  左上角: jimeng-topleft.png ({cropped.size[0]}x{cropped.size[1]})")
    
    # 右下角区域 (下半部分右半)
    bottomright_region = rgba.crop((orig_w // 2, orig_h // 2, orig_w, orig_h))
    bounds = find_content_bounds(bottomright_region)
    if bounds:
        left, top, right, bottom = bounds
        # 转换为全图坐标
        abs_left = left + orig_w // 2
        abs_top = top + orig_h // 2
        abs_right = right + orig_w // 2
        abs_bottom = bottom + orig_h // 2
        
        padding = 5
        cropped = bottomright_region.crop((
            max(0, left - padding),
            max(0, top - padding),
            min(orig_w // 2, right + padding),
            min(orig_h // 2, bottom + padding)
        ))
        cropped.save(os.path.join(OUTPUT_DIR, "jimeng-main.png"), 'PNG')
        configs.append({
            'file': 'jimeng-main.png',
            'templateSize': template_size,
            'anchor': 'bottom-right',
            'width': int(right - left),
            'height': int(bottom - top),
            'marginX': int(orig_w - abs_right),
            'marginY': int(orig_h - abs_bottom),
            'marginXRatio': float((orig_w - abs_right) / orig_w),
            'marginYRatio': float((orig_h - abs_bottom) / orig_h),
            'widthRatio': float((right - left) / orig_w),
            'heightRatio': float((bottom - top) / orig_h),
        })
        print(f"  右下角: jimeng-main.png ({cropped.size[0]}x{cropped.size[1]})")
    
    return configs


def extract_dual_corners(input_path, template_size, main_output, topleft_output, colored=False):
    """Split an image that contains two watermarks: top-left marker and bottom-right main."""
    print(f"处理双水印: {input_path}")
    img = Image.open(input_path)
    orig_w, orig_h = img.size
    rgba = to_rgba(img, colored=colored)

    configs = []

    # Top-left region (top half, left half)
    topleft_region = rgba.crop((0, 0, orig_w // 2, orig_h // 2))
    bounds = find_content_bounds(topleft_region)
    if bounds:
        left, top, right, bottom = bounds
        padding = 5
        cropped = topleft_region.crop((
            max(0, left - padding),
            max(0, top - padding),
            min(orig_w // 2, right + padding),
            min(orig_h // 2, bottom + padding)
        ))
        cropped.save(os.path.join(OUTPUT_DIR, topleft_output), 'PNG')
        configs.append({
            'file': topleft_output,
            'templateSize': template_size,
            'anchor': 'top-left',
            'width': int(right - left),
            'height': int(bottom - top),
            'marginX': int(left),
            'marginY': int(top),
            'marginXRatio': float(left / orig_w),
            'marginYRatio': float(top / orig_h),
            'widthRatio': float((right - left) / orig_w),
            'heightRatio': float((bottom - top) / orig_h),
        })
        print(f"  左上角: {topleft_output} ({cropped.size[0]}x{cropped.size[1]})")

    # Bottom-right region (bottom half, right half)
    bottomright_region = rgba.crop((orig_w // 2, orig_h // 2, orig_w, orig_h))
    bounds = find_content_bounds(bottomright_region)
    if bounds:
        left, top, right, bottom = bounds
        abs_right = right + orig_w // 2
        abs_bottom = bottom + orig_h // 2

        padding = 5
        cropped = bottomright_region.crop((
            max(0, left - padding),
            max(0, top - padding),
            min(orig_w // 2, right + padding),
            min(orig_h // 2, bottom + padding)
        ))
        cropped.save(os.path.join(OUTPUT_DIR, main_output), 'PNG')
        configs.append({
            'file': main_output,
            'templateSize': template_size,
            'anchor': 'bottom-right',
            'width': int(right - left),
            'height': int(bottom - top),
            'marginX': int(orig_w - abs_right),
            'marginY': int(orig_h - abs_bottom),
            'marginXRatio': float((orig_w - abs_right) / orig_w),
            'marginYRatio': float((orig_h - abs_bottom) / orig_h),
            'widthRatio': float((right - left) / orig_w),
            'heightRatio': float((bottom - top) / orig_h),
        })
        print(f"  右下角: {main_output} ({cropped.size[0]}x{cropped.size[1]})")

    return configs

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_configs = {}
    
    # 标准水印处理
    watermarks = [
        ("谷歌显水印2048.png", "gemini-current.png", 2048, False, None),
        # Gemini legacy variants are applied like 2048 templates (per index-v1 behavior)
        ("AI studio水印v1.png", "gemini-v1.png", 2048, True, "bottom-left"),
        ("AI studio水印v3.png", "gemini-v3.png", 2048, False, "bottom-right"),
        ("豆包水印2048.png", "doubao-main.png", 2048, False, None),
        ("豆包左上角水印2048.png", "doubao-topleft.png", 2048, False, None),
        ("百度水印1024.png", "baidu.png", 1024, False, None),
        ("腾讯混元水印1024.png", "hunyuan.png", 1024, False, "bottom-right"),

        # Alibaba
        ("千问水印1024.png", "qwen.png", 1024, False, "bottom-right"),
        ("夸克造点AI水印1024.png", "quark.png", 1024, False, "bottom-right"),

        # Baidu (Wenxin)
        ("文心AI水印1024.png", "wenxin.png", 1024, False, "bottom-right"),

        # Zhipu
        ("智谱清言GLM水印1024.png", "glm.png", 1024, False, "bottom-right"),
    ]
    
    for input_name, output_name, template_size, colored, force_anchor in watermarks:
        input_path = os.path.join(ASSETS_DIR, input_name)
        if os.path.exists(input_path):
            config = extract_watermark(input_path, output_name, template_size, colored=colored, force_anchor=force_anchor)
            if config:
                # Override Gemini legacy watermark placement to match the original v1 page.
                # These assets are standalone watermark PNGs (not full 2048 canvases), so
                # content-bound detection would always center them.
                if output_name == "gemini-v1.png":
                    ts = 2048
                    config.update({
                        'templateSize': ts,
                        'anchor': 'bottom-left',
                        'width': 96,
                        'height': 96,
                        'marginX': 64,
                        'marginY': 64,
                        'marginXRatio': 64 / ts,
                        'marginYRatio': 64 / ts,
                        'widthRatio': 96 / ts,
                        'heightRatio': 96 / ts,
                    })
                elif output_name == "gemini-v3.png":
                    ts = 2048
                    config.update({
                        'templateSize': ts,
                        'anchor': 'bottom-right',
                        'width': 96,
                        'height': 70,
                        'marginX': 48,
                        'marginY': 48,
                        'marginXRatio': 48 / ts,
                        'marginYRatio': 48 / ts,
                        'widthRatio': 96 / ts,
                        'heightRatio': 70 / ts,
                    })

                key = output_name.replace('.png', '')
                all_configs[key] = config

    # ZAI watermark is very small; crop only the bottom-right quarter to avoid
    # accidentally including other faint shapes in the image.
    zai_path = os.path.join(ASSETS_DIR, "ZAI水印2048.png")
    if os.path.exists(zai_path):
        print(f"处理: {zai_path}")
        img = Image.open(zai_path)
        orig_w, orig_h = img.size
        rgba = to_rgba(img, colored=False)

        region_size = 512
        x0 = max(0, orig_w - region_size)
        y0 = max(0, orig_h - region_size)
        region = rgba.crop((x0, y0, orig_w, orig_h))

        # ZAI has a dark decorative shape near the corner; threshold alpha to
        # isolate only the bright watermark pixels.
        arr = np.array(region)
        alpha = arr[:, :, 3]

        bounds = None
        for thr in (100, 60, 30, 10):
            m = alpha > thr
            if not np.any(m):
                continue
            ys, xs = np.where(m)
            bounds = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
            break

        if bounds is None:
            print("  警告: 未找到内容")
        else:
            left, top, right, bottom = bounds
            abs_left = left + x0
            abs_top = top + y0
            abs_right = right + x0
            abs_bottom = bottom + y0

            padding = 5
            cropped = region.crop((
                max(0, left - padding),
                max(0, top - padding),
                min(orig_w - x0, right + padding),
                min(orig_h - y0, bottom + padding)
            ))
            output_path = os.path.join(OUTPUT_DIR, "zai.png")
            cropped.save(output_path, 'PNG')

            wm_w = abs_right - abs_left
            wm_h = abs_bottom - abs_top
            margin_x = orig_w - abs_right
            margin_y = orig_h - abs_bottom

            all_configs["zai"] = {
                'file': 'zai.png',
                'templateSize': 2048,
                'anchor': 'bottom-right',
                'width': int(wm_w),
                'height': int(wm_h),
                'marginX': int(margin_x),
                'marginY': int(margin_y),
                'marginXRatio': float(margin_x / orig_w),
                'marginYRatio': float(margin_y / orig_h),
                'widthRatio': float(wm_w / orig_w),
                'heightRatio': float(wm_h / orig_h),
            }

            print(f"  保存: {output_path} ({cropped.size[0]}x{cropped.size[1]})")
            print(f"  位置: bottom-right, 边距: ({margin_x}, {margin_y}), 尺寸: {wm_w}x{wm_h}")
    
    # 即梦双水印
    jimeng_path = os.path.join(ASSETS_DIR, "即梦AI水印1328.png")
    if os.path.exists(jimeng_path):
        jimeng_configs = extract_jimeng_dual(jimeng_path, 1328)
        for cfg in jimeng_configs:
            key = cfg['file'].replace('.png', '')
            all_configs[key] = cfg

    # Wan / Dreamina dual-corner watermarks
    wan_path = os.path.join(ASSETS_DIR, "Wan通义万相水印1280.png")
    if os.path.exists(wan_path):
        wan_configs = extract_dual_corners(wan_path, 1280, "wan-main.png", "wan-topleft.png", colored=False)
        for cfg in wan_configs:
            key = cfg['file'].replace('.png', '')
            all_configs[key] = cfg

    dreamina_path = os.path.join(ASSETS_DIR, "Dreamina水印2048.png")
    if os.path.exists(dreamina_path):
        dreamina_configs = extract_dual_corners(dreamina_path, 2048, "dreamina-main.png", "dreamina-topleft.png", colored=False)
        for cfg in dreamina_configs:
            key = cfg['file'].replace('.png', '')
            all_configs[key] = cfg
    
    # 保存配置文件
    config_path = os.path.join(OUTPUT_DIR, "watermark-config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(all_configs, f, indent=2, ensure_ascii=False)
    print(f"\n配置文件: {config_path}")
    
    # 打印汇总
    print("\n=== 处理汇总 ===")
    for key, cfg in all_configs.items():
        print(f"{key}: {cfg['anchor']}, size={cfg['width']}x{cfg['height']}, margin=({cfg['marginX']:.0f},{cfg['marginY']:.0f})")

if __name__ == "__main__":
    main()
