#!/usr/bin/env python3
import json
import re
import textwrap


EMBED_START = "// WATERMARK_EMBED_START (auto-generated)"
EMBED_END = "// WATERMARK_EMBED_END"


def main():
    with open('assets/processed/watermark-config.json') as f:
        config = json.load(f)

    with open('assets/processed/watermark-base64.json') as f:
        base64_data = json.load(f)

    for key in config:
        if key in base64_data:
            config[key]['dataUrl'] = base64_data[key]

    watermark_js = f"window.WATERMARK_DATA = window.WATERMARK_DATA || {json.dumps(config)};"

    catalog_js = """
window.WATERMARK_CATALOG = window.WATERMARK_CATALOG || {
  google: {
    name: 'Google',
    products: {
      gemini: {
        name: 'Gemini',
        variants: [
          { id: 'current', label: '当前版 (白色芒星)', watermarkKey: 'gemini-current' },
          { id: 'v1', label: '旧版1 (彩色, 2025.3)', watermarkKey: 'gemini-v1' },
          { id: 'v3', label: '旧版2 (AI字样, 2025.5)', watermarkKey: 'gemini-v3' }
        ]
      }
    }
  },

  bytedance: {
    name: '字节跳动',
    products: {
      doubao: {
        name: '豆包',
        mainWatermark: 'doubao-main',
        topLeftWatermark: 'doubao-topleft',
        hasTopLeftOption: true
      },
      jimeng: {
        name: '即梦',
        mainWatermark: 'jimeng-main',
        topLeftWatermark: 'jimeng-topleft',
        hasTopLeftOption: true
      },
      dreamina: {
        name: 'Dreamina',
        mainWatermark: 'dreamina-main',
        topLeftWatermark: 'dreamina-topleft',
        hasTopLeftOption: true
      }
    }
  },

  alibaba: {
    name: '阿里',
    products: {
      qwen: {
        name: '千问',
        mainWatermark: 'qwen'
      },
      wan: {
        name: '通义万相',
        mainWatermark: 'wan-main',
        topLeftWatermark: 'wan-topleft',
        hasTopLeftOption: true,
        defaultTopLeftEnabled: true
      },
      quark: {
        name: '夸克造点',
        mainWatermark: 'quark'
      }
    }
  },

  baidu: {
    name: '百度',
    products: {
      baidu: {
        name: '百度',
        mainWatermark: 'baidu'
      },
      wenxin: {
        name: '文心',
        mainWatermark: 'wenxin'
      }
    }
  },

  zhipu: {
    name: '智谱',
    products: {
      glm: {
        name: '智谱清言',
        mainWatermark: 'glm'
      },
      zai: {
        name: 'ZAI',
        mainWatermark: 'zai'
      }
    }
  },

  tencent: {
    name: '腾讯',
    products: {
      hunyuan: {
        name: '混元',
        mainWatermark: 'hunyuan'
      }
    }
  }
};
""".strip()

    embed_block = "\n".join(
        [
            EMBED_START,
            watermark_js,
            "",
            catalog_js,
            "",
            "const WATERMARK_DATA = window.WATERMARK_DATA;",
            "const WATERMARK_CATALOG = window.WATERMARK_CATALOG;",
            EMBED_END,
        ]
    )
    embed_block = textwrap.indent(embed_block, "    ")

    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Remove existing embed block if present (idempotent regeneration)
    embed_re = re.compile(
        r"\n[ \t]*" + re.escape(EMBED_START) + r"[\s\S]*?" + re.escape(EMBED_END) + r"\n",
        re.M,
    )
    html = re.sub(embed_re, "\n", html, count=1)

    m = re.search(r"<script>", html)
    if not m:
        raise SystemExit("Error: Could not find <script> tag")
    script_end = m.end()

    insert_point = html.find('const state = {')
    if insert_point == -1:
        raise SystemExit("Error: Could not find insertion point: const state = {")

    new_html = html[:script_end] + "\n" + embed_block + "\n\n" + html[insert_point:]

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f"Embedded watermark data into index.html ({len(watermark_js)} chars)")


if __name__ == "__main__":
    main()
