from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def playwright_available() -> dict:
    node_path = shutil.which("node")
    package_dir = Path(__file__).resolve().parents[1] / "tools" / "playwright" / "node_modules" / "playwright"
    cli_path = package_dir / "cli.js"
    if not node_path or not package_dir.is_dir() or not cli_path.is_file():
        return {
            "status": "blocked",
            "node_path": node_path,
            "playwright_path": str(package_dir),
            "message": (
                "The locked tools/playwright runtime is unavailable. "
                "Run the explicit environment prepare flow to install it."
            ),
        }
    return {
        "status": "pass",
        "node_path": node_path,
        "playwright_path": str(package_dir),
        "cli_path": str(cli_path),
        "message": f"Locked Playwright runtime detected at {package_dir}.",
    }


def _run_playwright_script(script: str, output_dir: Path, timeout: int = 120) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    check = playwright_available()
    if check["status"] != "pass":
        return check

    script_path = output_dir / "playwright_task.js"
    script_path.write_text(script, encoding="utf-8")
    command = [check["node_path"], str(script_path)]
    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(Path(__file__).resolve().parents[1] / "tools" / "playwright" / ".playwright")
    node_modules = str(Path(check["playwright_path"]).parent)
    existing_node_path = env.get("NODE_PATH")
    env["NODE_PATH"] = node_modules if not existing_node_path else f"{node_modules}{os.pathsep}{existing_node_path}"

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            cwd=output_dir,
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:

        def _text(value: str | bytes | None) -> str:
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="replace")
            return value or ""

        return {
            "status": "blocked",
            "returncode": None,
            "timed_out": True,
            "timeout_seconds": timeout,
            "stdout": _text(exc.stdout),
            "stderr": _text(exc.stderr),
            "message": f"Playwright script exceeded its {timeout}-second timeout.",
        }
    except OSError as exc:
        return {
            "status": "blocked",
            "returncode": None,
            "timed_out": False,
            "stdout": "",
            "stderr": str(exc),
            "message": f"Playwright script could not be launched: {exc}",
        }
    if result.returncode != 0:
        return {
            "status": "blocked",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message": (
                "Playwright execution failed. Browser binaries may be missing; "
                "use the explicit environment prepare flow."
            ),
        }
    lines = [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
    if not lines:
        return {
            "status": "blocked",
            "returncode": result.returncode,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "message": "Playwright script returned no JSON report.",
        }
    try:
        payload = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        return {
            "status": "blocked",
            "returncode": result.returncode,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "message": f"Playwright script returned invalid JSON: {exc}",
        }
    if not isinstance(payload, dict) or not payload:
        return {
            "status": "blocked",
            "returncode": result.returncode,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "message": "Playwright script JSON report must be a non-empty object.",
        }
    payload.setdefault("status", "pass")
    payload.setdefault("stderr", result.stderr)
    return payload


def _ensure_playwright_node_runtime() -> dict:
    """Compatibility probe only; installation belongs to environment preparation."""
    check = playwright_available()
    if check["status"] != "pass":
        return check
    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(Path(__file__).resolve().parents[1] / "tools" / "playwright" / ".playwright")
    node_modules = str(Path(check["playwright_path"]).parent)
    existing_node_path = env.get("NODE_PATH")
    env["NODE_PATH"] = node_modules if not existing_node_path else f"{node_modules}{os.pathsep}{existing_node_path}"
    return {**check, "env": env}


def _run_playwright_cli(args: list[str], output_dir: Path, timeout: int = 120) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    check = playwright_available()
    if check["status"] != "pass":
        return check

    try:
        result = subprocess.run(
            [check["node_path"], check["cli_path"], *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            cwd=output_dir,
            env={
                **os.environ,
                "PLAYWRIGHT_BROWSERS_PATH": str(
                    Path(__file__).resolve().parents[1] / "tools" / "playwright" / ".playwright"
                ),
            },
            timeout=timeout,
        )
    except FileNotFoundError:
        return {
            "status": "blocked",
            "message": f"Node executable was reported but could not be launched: {check['node_path']}",
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "blocked", "message": f"Playwright CLI failed or exceeded timeout: {exc}"}

    if result.returncode != 0:
        return {
            "status": "blocked",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message": (
                "Playwright CLI execution failed. Browser binaries may be missing; "
                "use the explicit environment prepare flow."
            ),
        }
    return {
        "status": "pass",
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def qa_html(html_path: Path, output_dir: Path, profile: str) -> dict:
    html_path = Path(html_path).resolve()
    output_dir = Path(output_dir)
    screenshot = output_dir / "layout-qa.png"
    section_dir = output_dir / "sections"
    script = f"""
const {{ chromium }} = require('playwright');
const fs = require('fs');
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage({{ viewport: {{ width: 1920, height: 1080 }}, deviceScaleFactor: 1 }});
  await page.goto({json.dumps(html_path.as_uri())}, {{ waitUntil: 'networkidle' }});
  const overflow = await page.evaluate(() => {{
    return Array.from(document.querySelectorAll('*')).filter((el) => {{
      const tag = el.tagName.toLowerCase();
      if (['html', 'body', 'head', 'style', 'script'].includes(tag)) return false;
      const style = window.getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden') return false;
      return el.scrollWidth > el.clientWidth + 8 || el.scrollHeight > el.clientHeight + 12;
    }}).slice(0, 50).map((el) => ({{
      tag: el.tagName.toLowerCase(),
      className: el.className || '',
      text: (el.textContent || '').trim().slice(0, 100),
      scrollWidth: el.scrollWidth,
      clientWidth: el.clientWidth,
      scrollHeight: el.scrollHeight,
      clientHeight: el.clientHeight
    }}));
  }});
  const contrast = await page.evaluate(() => {{
    function parseRgb(value) {{
      const match = String(value || '').match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([0-9.]+))?/);
      if (!match) return null;
      const alpha = match[4] === undefined ? 1 : Number(match[4]);
      if (alpha === 0) return null;
      return [Number(match[1]), Number(match[2]), Number(match[3])];
    }}
    function nearestBackground(el) {{
      let current = el;
      while (current) {{
        const bg = parseRgb(window.getComputedStyle(current).backgroundColor);
        if (bg) return bg;
        current = current.parentElement;
      }}
      return parseRgb(window.getComputedStyle(document.body).backgroundColor) || [247, 242, 232];
    }}
    function luminance(rgb) {{
      return rgb.map((channel) => {{
        const c = channel / 255;
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
      }}).reduce((sum, value, idx) => sum + value * [0.2126, 0.7152, 0.0722][idx], 0);
    }}
    function ratio(fg, bg) {{
      if (!fg || !bg) return null;
      const l1 = luminance(fg);
      const l2 = luminance(bg);
      return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    }}
    const elements = Array.from(document.querySelectorAll('h1,h2,p,.kicker,.notes,.brandline')).slice(0, 80);
    const ratios = elements
      .map((el) => ratio(parseRgb(window.getComputedStyle(el).color), nearestBackground(el)))
      .filter(Boolean);
    const minimum = ratios.length ? Math.min(...ratios) : null;
    return {{
      status: minimum === null || minimum >= 4.5 ? 'pass' : 'block',
      minimum_ratio: minimum ? Math.round(minimum * 100) / 100 : null,
      checked_elements: ratios.length
    }};
  }});
  const posterFit = await page.evaluate(() => {{
    const poster = document.querySelector('.poster');
    if (!poster) return {{ status: 'pass', reason: 'not-a-poster' }};
    const rect = poster.getBoundingClientRect();
    const fits = (
      poster.scrollWidth <= poster.clientWidth + 4 &&
      poster.scrollHeight <= poster.clientHeight + 4 &&
      rect.width <= 1920 + 4 &&
      rect.height <= 1080 + 4
    );
    return {{
      status: fits ? 'pass' : 'block',
      scrollWidth: poster.scrollWidth,
      clientWidth: poster.clientWidth,
      scrollHeight: poster.scrollHeight,
      clientHeight: poster.clientHeight,
      renderedWidth: Math.round(rect.width),
      renderedHeight: Math.round(rect.height)
    }};
  }});
  fs.mkdirSync({json.dumps(str(section_dir))}, {{ recursive: true }});
  const sectionScreenshots = [];
  const sections = page.locator('section.slide, section.block');
  const sectionCount = await sections.count();
  for (let i = 0; i < sectionCount; i++) {{
    const id = await sections.nth(i).getAttribute('data-scene') || `section-${{String(i + 1).padStart(3, '0')}}`;
    const safeId = id.replace(/[^a-zA-Z0-9_.-]/g, '-');
    const target = {json.dumps(str(section_dir))} + '/' + safeId + '.png';
    await sections.nth(i).screenshot({{ path: target }});
    sectionScreenshots.push(target);
  }}
  await page.screenshot({{ path: {json.dumps(str(screenshot))}, fullPage: true }});
  await browser.close();
  console.log(JSON.stringify({{
    status: overflow.length || contrast.status !== 'pass' || posterFit.status !== 'pass' ? 'block' : 'pass',
    profile: {json.dumps(profile)},
    screenshot: {json.dumps(str(screenshot))},
    section_screenshots: sectionScreenshots,
    overflow_elements: overflow,
    contrast,
    poster_fit: posterFit
  }}));
}})().catch((error) => {{
  console.error(error.stack || String(error));
  process.exit(1);
}});
"""
    report = _run_playwright_script(script, output_dir)
    stderr = str(report.get("stderr", ""))
    if report.get("status") == "pass":
        return report
    if "Cannot find module 'playwright'" not in stderr:
        return report

    cli_report = _run_playwright_cli(
        ["screenshot", "--full-page", html_path.as_uri(), str(screenshot)],
        output_dir,
    )
    if cli_report.get("status") != "pass":
        return cli_report
    return {
        "status": "pass",
        "profile": profile,
        "screenshot": str(screenshot),
        "overflow_elements": [],
        "overflow_check": "skipped-cli-fallback",
        "message": "Used Playwright CLI screenshot fallback because Node API package resolution was unavailable.",
    }


def export_html_pdf(html_path: Path, output_path: Path, profile: str) -> dict:
    html_path = Path(html_path).resolve()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage({{ viewport: {{ width: 1920, height: 1080 }}, deviceScaleFactor: 1 }});
  await page.goto({json.dumps(html_path.as_uri())}, {{ waitUntil: 'networkidle' }});
  const posterDims = await page.evaluate(() => {{
    const poster = document.querySelector('.poster');
    if (!poster) return null;
    return {{
      width: Math.ceil(poster.scrollWidth || poster.clientWidth || 1920),
      height: Math.ceil(poster.scrollHeight || poster.clientHeight || 1080),
    }};
  }});
  const options = {{
    path: {json.dumps(str(output_path))},
    printBackground: true,
    margin: {{ top: '0px', right: '0px', bottom: '0px', left: '0px' }},
  }};
  if (posterDims) {{
    options.width = `${{posterDims.width}}px`;
    options.height = `${{posterDims.height}}px`;
    options.pageRanges = '1';
  }} else {{
    options.preferCSSPageSize = true;
  }}
  await page.pdf(options);
  await browser.close();
  console.log(JSON.stringify({{
    status: 'pass',
    profile: {json.dumps(profile)},
    path: {json.dumps(str(output_path))},
    mode: posterDims ? 'poster-fixed-page' : 'css-page-size'
  }}));
}})().catch((error) => {{
  console.error(error.stack || String(error));
  process.exit(1);
}});
"""
    report = _run_playwright_script(script, output_path.parent)
    stderr = str(report.get("stderr", ""))
    if report.get("status") == "pass" and output_path.exists():
        return report
    if "Cannot find module 'playwright'" not in stderr:
        return report
    report = _run_playwright_cli(["pdf", html_path.as_uri(), str(output_path)], output_path.parent)
    if report.get("status") == "pass":
        report.update({"profile": profile, "path": str(output_path), "mode": "cli-fallback"})
    return report


def capture_thumbnail(html_path: Path, output_path: Path, profile: str) -> dict:
    html_path = Path(html_path).resolve()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage({{ viewport: {{ width: 1920, height: 1080 }}, deviceScaleFactor: 1 }});
  await page.goto({json.dumps(html_path.as_uri())}, {{ waitUntil: 'networkidle' }});
  const target = page.locator('.poster, .deck').first();
  if (await target.count()) {{
    await target.screenshot({{ path: {json.dumps(str(output_path))} }});
  }} else {{
    await page.screenshot({{ path: {json.dumps(str(output_path))}, fullPage: true }});
  }}
  await browser.close();
  console.log(JSON.stringify({{ status: 'pass', path: {json.dumps(str(output_path))}, mode: 'element-screenshot' }}));
}})().catch((error) => {{
  console.error(error.stack || String(error));
  process.exit(1);
}});
"""
    report = _run_playwright_script(script, output_path.parent)
    if report.get("status") != "pass":
        report = _run_playwright_cli(
            ["screenshot", "--full-page", html_path.as_uri(), str(output_path)], output_path.parent
        )
    if report.get("status") == "pass":
        report.update({"profile": profile, "path": str(output_path)})
    return report


def extract_page_text(url: str, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    screenshot = output_dir / "requirements-page.png"
    script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage({{ viewport: {{ width: 1365, height: 900 }} }});
  await page.goto({json.dumps(url)}, {{ waitUntil: 'networkidle', timeout: 60000 }});
  const text = await page.locator('body').innerText();
  await page.screenshot({{ path: {json.dumps(str(screenshot))}, fullPage: true }});
  await browser.close();
  console.log(JSON.stringify({{
    status: 'pass',
    url: {json.dumps(url)},
    text,
    screenshot: {json.dumps(str(screenshot))}
  }}));
}})().catch((error) => {{
  console.error(error.stack || String(error));
  process.exit(1);
}});
"""
    return _run_playwright_script(script, output_dir)
