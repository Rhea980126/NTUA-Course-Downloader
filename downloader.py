"""
NTUA e-Learning 課程截圖下載工具
自動截圖台灣藝術大學網路學園的課程 PDF 教材

使用方式：
1. 開啟可控制的 Chrome：
   Mac:   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
   Win:   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

2. 在 Chrome 裡登入 NTUA 網路學園，進入你想下載的課程頁面

3. 執行腳本：
   python3 downloader.py
"""

import asyncio
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright


# ── 輸出資料夾 ──
OUTPUT_DIR = Path("./downloads")


# ────────────────────────────────────────────
# 工具函式
# ────────────────────────────────────────────

def prompt(msg, default=None):
    """互動式輸入，支援預設值"""
    if default is not None:
        result = input(f"{msg} [{default}]: ").strip()
        return result if result else default
    return input(f"{msg}: ").strip()


def print_header():
    print("=" * 55)
    print("  NTUA 網路學園 課程截圖下載工具")
    print("=" * 55)


async def get_total_pages(page):
    """取得目前章節的總頁數，最多等 30 秒"""
    for attempt in range(15):
        try:
            labels = page.locator("span.toolbarLabel")
            count = await labels.count()
            for j in range(count):
                t = await labels.nth(j).text_content()
                m = re.search(r'/\s*(\d+)', t)
                if m:
                    total = int(m.group(1))
                    if total > 0:
                        return total
        except Exception:
            pass
        print(f"   ⏳ 等待頁數載入... ({attempt + 1}/15)")
        await asyncio.sleep(2)
    return 0


async def get_viewer_rect(page):
    """取得 PDF viewer 的精確座標（排除右側章節列表）"""
    return await page.evaluate("""
        () => {
            const viewer = document.querySelector('#viewerContainer');
            const sidebar = document.querySelector('app-learning-sidebar, [class*="syllabus"]');
            if (!viewer) return null;
            const vr = viewer.getBoundingClientRect();
            const sr = sidebar ? sidebar.getBoundingClientRect() : null;
            return {
                x: vr.x,
                y: vr.y,
                width: sr ? sr.x - vr.x : vr.width,
                height: vr.height
            };
        }
    """)


async def screenshot_page(page, rect, save_path):
    """截圖 PDF viewer 區域"""
    try:
        await page.screenshot(
            path=str(save_path),
            clip={
                'x': rect['x'],
                'y': rect['y'],
                'width': rect['width'],
                'height': rect['height']
            }
        )
    except Exception as e:
        print(f"   ⚠️  截圖失敗，改用全頁截圖：{e}")
        await page.screenshot(path=str(save_path))


# ────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────

async def main():
    print_header()

    # ── 步驟 1：連接 Chrome ──
    print("\n步驟 1：連接 Chrome")
    print("請確認你已用以下指令開啟 Chrome：")
    print("  Mac: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
    print("  Win: \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222")
    input("\n按 Enter 繼續連接...")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception:
            print("\n❌ 無法連接 Chrome！請確認已正確開啟。")
            sys.exit(1)

        context = browser.contexts[0]
        page = context.pages[0]
        print(f"✅ 連接成功！")

        # ── 步驟 2：等待進入課程頁面 ──
        print("\n步驟 2：進入課程頁面")
        if "/learning/" not in page.url:
            print("請在 Chrome 裡：登入 → 我的課表 → 選擇課程")
            print("腳本會自動偵測，不需要操作終端機...")
            while "/learning/" not in page.url:
                await asyncio.sleep(1)

        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

        # 取得課程名稱
        try:
            course_name = await page.locator("h2, .course-title, [class*='course-name']").first.text_content()
            course_name = course_name.strip()
        except Exception:
            course_name = "課程"
        print(f"✅ 偵測到課程：{course_name}")

        # ── 步驟 3：選擇輸出資料夾 ──
        print("\n步驟 3：設定輸出資料夾")
        safe_name = "".join(c for c in course_name if c not in r'\/:*?"<>|')[:40]
        default_dir = str(OUTPUT_DIR / safe_name)
        out_dir_str = prompt("下載資料夾", default=default_dir)
        out_dir = Path(out_dir_str)
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 將儲存至：{out_dir.resolve()}")

        # ── 步驟 4：列出章節，讓使用者選擇 ──
        print("\n步驟 4：選擇要下載的章節")
        chapters = page.locator("mat-expansion-panel")
        chapter_count = await chapters.count()

        chapter_names = []
        for i in range(chapter_count):
            header = chapters.nth(i).locator(".mat-expansion-panel-header")
            name = (await header.text_content()).strip()
            chapter_names.append(name)
            print(f"  {i + 1}. {name}")

        print(f"\n輸入要下載的章節編號（用逗號分隔，例如 2,3,4）")
        print(f"或輸入 all 下載全部，輸入 all-skip 下載全部但跳過說明類章節")
        selection = prompt("你的選擇", default="all").strip().lower()

        if selection == "all":
            selected_indices = list(range(chapter_count))
        elif selection == "all-skip":
            skip_keywords = ["說明", "考說明", "公告"]
            selected_indices = [
                i for i, name in enumerate(chapter_names)
                if not any(kw in name for kw in skip_keywords)
            ]
        else:
            try:
                selected_indices = [int(x.strip()) - 1 for x in selection.split(",")]
                selected_indices = [i for i in selected_indices if 0 <= i < chapter_count]
            except ValueError:
                print("❌ 輸入格式錯誤，下載全部章節")
                selected_indices = list(range(chapter_count))

        print(f"\n將下載以下 {len(selected_indices)} 個章節：")
        for i in selected_indices:
            print(f"  ✓ {chapter_names[i]}")

        input("\n確認後按 Enter 開始下載，或 Ctrl+C 取消...")

        # ── 步驟 5：測試截圖 ──
        print("\n🔍 測試截圖中...")
        rect = await get_viewer_rect(page)
        if rect:
            test_path = out_dir / "test_screenshot.png"
            await screenshot_page(page, rect, test_path)
            print(f"   測試截圖已存到：{test_path}")
            confirm = prompt("截圖效果正確嗎？(y/n)", default="y").lower()
            if confirm != "y":
                print("請調整瀏覽器視窗後重新執行。")
                return
        else:
            print("   ⚠️  無法取得 viewer 座標，將用全頁截圖")

        # ── 步驟 6：逐章節截圖 ──
        print(f"\n🚀 開始下載...\n")

        for idx, i in enumerate(selected_indices):
            chapter = chapters.nth(i)
            header = chapter.locator(".mat-expansion-panel-header")
            chapter_text = chapter_names[i]
            chapter_text_clean = "".join(c for c in chapter_text if c not in r'\/:*?"<>|')

            print(f"📖 [{idx + 1}/{len(selected_indices)}] {chapter_text}")

            chapter_dir = out_dir / f"{idx + 1:02d}_{chapter_text_clean[:40]}"
            chapter_dir.mkdir(exist_ok=True)

            await header.click()
            await asyncio.sleep(6)
            await page.wait_for_load_state("networkidle")

            total_pages = await get_total_pages(page)
            if total_pages == 0:
                print(f"   ⚠️  無法取得頁數，跳過此章節")
                continue

            print(f"   📄 共 {total_pages} 頁，開始截圖...")

            # 回到第一頁
            try:
                first_btn = page.locator("button#first")
                if await first_btn.count() > 0:
                    await first_btn.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

            rect = await get_viewer_rect(page)

            for page_num in range(1, total_pages + 1):
                await asyncio.sleep(1.5)
                screenshot_path = chapter_dir / f"page_{page_num:03d}.png"

                if rect:
                    await screenshot_page(page, rect, screenshot_path)
                else:
                    await page.screenshot(path=str(screenshot_path))

                print(f"   📸 第 {page_num}/{total_pages} 頁", end="\r")

                if page_num < total_pages:
                    try:
                        await page.locator("button#next").click()
                    except Exception:
                        await page.keyboard.press("ArrowDown")

            print(f"\n   ✅ 完成！共 {total_pages} 頁")

        print(f"\n🎉 全部完成！所有截圖儲存於：{out_dir.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
