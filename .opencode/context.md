# 项目上下文

## 项目名称
AI水印工具箱 (AI Watermark Toolbox)

## 项目目的
帮助创作者快速/批量给AI生成图片添加合规的厂商水印标识。

**注意**：这是**加水印**工具，不是去水印工具。

## 背景
各大AI图像生成平台（Google Gemini、豆包、即梦、百度、腾讯混元等）生成的图片通常带有水印标识。本工具允许用户将这些水印添加到自己的图片上，使其看起来像是由对应AI平台生成的。

## 技术栈
- **框架**: 纯 HTML + CSS + JavaScript（单文件）
- **CSS框架**: Pico.css (CDN)
- **图像处理**: 原生 Canvas API
- **批量打包**: JSZip (CDN)
- **部署**: 静态托管（Vercel/GitHub Pages/Cloudflare Pages）

## 关键决策
1. **单HTML文件**: 便于分享和部署
2. **纯客户端处理**: 无需服务器，保护用户隐私
3. **水印内嵌Base64**: 预处理后的RGBA水印直接嵌入HTML
4. **扩展性设计**: 通过配置对象支持新增厂商

## 文件结构
```
add-watermark/
├── index.html              # 主应用（单文件）
├── 加水印对话.txt           # 原始需求对话记录
├── assets/                 # 原始水印素材
│   ├── 谷歌显水印2048.png
│   ├── 豆包水印2048.png
│   ├── 豆包左上角水印2048.png
│   ├── 即梦AI水印1328.png
│   ├── 百度水印1024.png
│   ├── 腾讯混元水印1024.png
│   ├── AI studio水印v1.png
│   ├── AI studio水印v3.png
│   └── ...
├── assets/processed/       # 预处理后的水印素材
│   ├── gemini-current.png
│   ├── gemini-v1.png
│   ├── gemini-v3.png
│   ├── doubao-main.png
│   ├── doubao-topleft.png
│   ├── jimeng-main.png
│   ├── jimeng-topleft.png
│   ├── baidu.png
│   └── hunyuan.png
└── .opencode/              # 开发规划文档
    ├── plans/
    │   └── agent.md
    └── context.md
```

## 当前状态
- [x] 需求分析完成
- [x] 规划文档创建
- [ ] 素材预处理
- [ ] M0: 项目骨架
- [ ] M1: 输入系统
- [ ] M2: 水印模板系统
- [ ] M3: 水印尺寸匹配
- [ ] M4: Resize功能
- [ ] M5: 批量导出
