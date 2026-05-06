# NTUA-Course-Downloader
自動截圖下載台灣藝術大學網路學園課程 PDF 教材的工具。

## 功能

- 互動式選擇要下載的課程章節
- 自動翻頁截圖每一頁 PDF 內容
- 每個章節儲存在獨立資料夾
- 支援跳過說明/考試類章節

## 安裝

**需求：Python 3.8+**

```bash
git clone https://github.com/你的帳號/ntua-course-downloader.git
cd ntua-course-downloader
pip install -r requirements.txt
playwright install chromium
```

## 使用方式

### 步驟 1：用特殊模式開啟 Chrome

**Mac：**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**Windows：**
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

### 步驟 2：在 Chrome 裡登入並進入課程頁面

1. 登入 NTUA 網路學園
2. 點右上角名字 → 我的課表
3. 點選想下載的課程

### 步驟 3：執行腳本

開另一個終端機視窗：
```bash
python3 downloader.py
```

腳本會引導你完成剩下的步驟。

## 下載結果

截圖會儲存在 `downloads/課程名稱/` 資料夾下，每個章節一個子資料夾：

```
downloads/
└── 114-2_西方藝術史/
    ├── 01_Renaissance背景/
    │   ├── page_001.png
    │   ├── page_002.png
    │   └── ...
    ├── 02_Renaissance特徵/
    │   └── ...
    └── ...
```

## 注意事項

- 本工具僅供個人學習使用，請勿散布課程內容
- 需要有效的 NTUA 帳號才能使用
- 請確保你有該課程的存取權限

## 系統需求

| 項目 | 需求 |
|------|------|
| Python | 3.8 以上 |
| 作業系統 | macOS / Windows / Linux |
| 瀏覽器 | Google Chrome |
