# AI水印工具箱 - 开发规划

## 项目概述

纯浏览器端的单页面水印添加工具，帮助创作者快速/批量给AI生成图片添加合规的厂商水印标识。

### 技术定位
- 单 HTML 文件部署（可部署到 Vercel/GitHub Pages/Cloudflare Pages）
- 100% 客户端处理，无需服务器
- 现代、简约、响应式 UI，支持暗色主题

---

## 水印资源配置

### 厂商分类

| 厂商 | 产品/版本 | 素材文件 | 位置 | 状态 |
|------|----------|---------|------|------|
| **Google** | Gemini 当前版 | gemini-current.png | 右下角 | 默认 |
| **Google** | Gemini 旧版1 (2025.3) | gemini-v1.png | 左下角 | 可选 |
| **Google** | Gemini 旧版2 (2025.5) | gemini-v3.png | 右下角 | 可选 |
| **字节** | 豆包 - 主水印 | doubao-main.png | 右下角 | 默认 |
| **字节** | 豆包 - AI标识 | doubao-topleft.png | 左上角 | 可选勾选 |
| **字节** | 即梦 - 主水印 | jimeng-main.png | 右下角 | 默认 |
| **字节** | 即梦 - AI标识 | jimeng-topleft.png | 左上角 | 可选勾选 |
| **百度** | 百度AI | baidu.png | 右下角 | - |
| **腾讯** | 混元 | hunyuan.png | 右下角 | - |

### 不使用的素材
- `32px-Google-gemini-icon.svg.png` - 无用
- `AI studio水印.png` - 与谷歌显水印重复
- `AI studio水印v2.png` - 来源不明

### 扩展性设计
新增厂商只需在 `watermarkCatalog` 配置对象中添加条目：
```javascript
const watermarkCatalog = {
  // 新厂商只需添加此结构
  newVendor: {
    name: '新厂商名',
    products: {
      productA: {
        name: '产品A',
        variants: [
          { id: 'default', label: '默认版', anchor: 'bottom-right', ... }
        ],
        options: [
          { id: 'topLeft', label: '添加左上角标识', default: false }
        ]
      }
    }
  }
}
```

---

## 水印尺寸缩放逻辑

### 核心原则
水印在不同分辨率图片上的**视觉占比保持一致**

### 计算规则
```
图片尺寸判断 (取短边):
  - 短边 ≤ 1280px  → 1K级别 → 水印缩放 0.5x
  - 短边 1281-2560px → 2K级别 → 水印缩放 1.0x (基准)
  - 短边 > 2560px → 4K级别 → 水印缩放 2.0x
```

### 用户控制
- ☑ 自动匹配水印尺寸（默认开启）
- 关闭后使用固定尺寸水印

---

## UI 布局设计

```
┌─────────────────────────────────────────────────────────────┐
│  [🌙]                    AI水印工具箱                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────── 左侧 ───────────┐  ┌────── 右侧 ──────────┐  │
│  │      📷 预览区域            │  │  ● Step 1  导入图片   │  │
│  │     (实时预览结果)          │  │  ○ Step 2  调整尺寸   │  │
│  │                            │  │  ○ Step 3  添加水印   │  │
│  │                            │  │  ○ Step 4  导出保存   │  │
│  ├────────────────────────────┤  │  ┌─────────────────┐  │  │
│  │  缩略图: [1][2][3][+]      │  │  │  控制面板       │  │  │
│  └────────────────────────────┘  │  └─────────────────┘  │  │
│                                  │  [上一步]  [下一步]   │  │
└─────────────────────────────────────────────────────────────┘
```

### 响应式断点
- Desktop (>1024px): 左右分栏
- Tablet/Mobile (<1024px): 上下堆叠

### 设计风格
- Pico.css 为基础
- 灰白色系浅色主题 / 深灰色系暗色主题
- 简约现代，无过度动效
- 适度圆角和阴影

---

## 技术架构

```
index.html (单文件)
├── <head>
│   ├── Pico.css (CDN)
│   └── 内联 CSS (暗色主题 + 响应式 + 自定义样式)
├── <body>
│   ├── 左侧面板 (预览 + 缩略图)
│   └── 右侧面板 (步骤 + 控制)
└── <script type="module">
    ├── 水印资源 (Base64 RGBA，预处理后内嵌)
    ├── watermarkCatalog (配置表)
    ├── 状态管理 (简单对象 + 事件驱动)
    ├── 输入模块 (upload/drag/paste)
    ├── Resize模块 (Canvas cover裁剪)
    ├── 水印模块 (drawImage叠加)
    └── 导出模块 (toBlob + JSZip CDN)
```

### 核心数据结构
```javascript
const state = {
  files: [
    {
      id: 'uuid-1',
      original: ImageBitmap,
      filename: 'photo1.jpg',
      resized: null,        // resize后的结果
      watermarked: null     // 加水印后的结果
    }
  ],
  currentIndex: 0,
  currentStep: 1,
  settings: {
    vendor: 'google',
    product: 'gemini',
    variant: 'current',
    topLeftEnabled: false,
    autoScale: true,
    resizeEnabled: false,
    targetWidth: 2048,
    targetHeight: 2048,
    aspectRatio: '1:1',
    format: 'png',
    quality: 0.85
  }
}
```

---

## 开发里程碑

| 里程碑 | 内容 | 预计时间 | 优先级 |
|--------|------|----------|--------|
| **M0** | 项目骨架 + 暗色主题 + 响应式布局 | 1-2h | P0 |
| **M1** | 输入系统 (上传/拖拽/粘贴/批量) | 2-3h | P0 |
| **M2** | 水印模板系统 (核心功能) | 4-5h | P0 |
| **M3** | 水印尺寸自动匹配逻辑 | 1-2h | P1 |
| **M4** | Resize & 裁剪 (可选步骤) | 3-4h | P2 |
| **M5** | 批量导出 (单张/ZIP) | 2-3h | P1 |
| **M6** | 体验打磨 (动效/反馈/边界处理) | 2h | P2 |

**MVP = M0 + M1 + M2 + M5**

---

## 预处理任务

### 素材处理流程
1. **即梦水印分割**：将 `即梦AI水印1328.png` 分割为两张
2. **黑底转RGBA**：所有水印转为透明背景白色水印
3. **裁切边界框**：移除多余透明区域，减小体积
4. **生成Base64**：转为 Data URL 内嵌

### 黑底转RGBA算法
```javascript
function blackToRGBA(imageData) {
  const data = imageData.data;
  for (let i = 0; i < data.length; i += 4) {
    const brightness = Math.max(data[i], data[i+1], data[i+2]);
    data[i] = 255;      // R = 白色
    data[i+1] = 255;    // G = 白色
    data[i+2] = 255;    // B = 白色
    data[i+3] = brightness; // A = 原亮度
  }
  return imageData;
}
```

---

## 验收标准

### MVP 完成标准
- [ ] 页面可正常打开，布局响应式
- [ ] 支持拖拽/粘贴/选择文件导入图片
- [ ] 可选择厂商/产品/版本
- [ ] 水印正确叠加到预览图
- [ ] 可导出单张或批量ZIP

### 质量标准
- 无控制台错误
- 图片处理无明显延迟（<500ms/张）
- 移动端可正常使用
