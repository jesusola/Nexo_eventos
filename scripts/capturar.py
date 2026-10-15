"""Capturas del navegador: instalar requirements-dev y un navegador Chromium."""
import argparse
from pathlib import Path
import requests

from playwright.sync_api import sync_playwright

from scripts.casos import CASOS

ROOT = Path(__file__).resolve().parents[1]


def esperar(page):
    page.wait_for_timeout(500)
    page.locator('[data-testid="stStatusWidget"]').wait_for(state="hidden", timeout=30000)


def seleccionar(page, posicion, texto):
    entrada = page.get_by_role("combobox").nth(posicion)
    entrada.click()
    entrada.fill(texto)
    page.get_by_role("option", name=texto, exact=True).click()
    esperar(page)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--front", default="http://localhost:8501")
    p.add_argument("--api", help="Cambiar la dirección de API en la barra lateral.")
    p.add_argument("--navegador", help="Ruta a Edge o Chrome; si se omite, usa Chromium de Playwright.")
    p.add_argument("--modo", choices=["reportes", "reglas"], required=True)
    args = p.parse_args()
    destino = ROOT / "docs" / "capturas"
    destino.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=args.navegador,
                                     ignore_default_args=["--headless=old"], args=["--headless=new"])
        page = browser.new_page(viewport={"width": 1550, "height": 1500}, device_scale_factor=1)
        page.goto(args.front)
        page.get_by_text("Próximos eventos", exact=True).wait_for()
        esperar(page)
        if args.api:
            page.get_by_label("Dirección de la API").fill(args.api)
            page.get_by_label("Dirección de la API").press("Enter")
            esperar(page)
        if args.modo == "reportes":
            page.screenshot(path=str(destino / "streamlit_inicio.png"))
            page.get_by_text("Reportes", exact=True).click()
            esperar(page)
            for n, reporte in enumerate(["Organigrama", "Escalamiento", "Ranking de clientes", "Ocupación de salones"], 1):
                seleccionar(page, 0, reporte)
                if reporte == "Escalamiento":
                    api = page.get_by_label("Dirección de la API").input_value()
                    empleado = requests.get(api + "/staff/12", timeout=10).json()
                    seleccionar(page, 1, empleado["nombre"])
                page.locator('[data-testid="stDataFrame"]').first.wait_for()
                esperar(page)
                page.screenshot(path=str(destino / f"streamlit_B{n}.png"))
        else:
            for caso in CASOS:
                archivo = caso.replace(" ", "_")
                page.goto((ROOT / "docs" / f"{archivo}.html").as_uri())
                page.screenshot(path=str(destino / f"api_{archivo}.png"), full_page=True)
            page.goto(args.front)
            page.get_by_text("Próximos eventos", exact=True).wait_for()
            esperar(page)
            page.get_by_text("Pruebas de entrega", exact=True).click()
            page.get_by_text("Verificación de reglas", exact=True).wait_for()
            for caso, definicion in CASOS.items():
                seleccionar(page, 0, caso)
                page.get_by_role("button", name="Ejecutar caso", exact=True).click()
                page.get_by_text(f"HTTP {definicion['status']}", exact=True).wait_for(timeout=30000)
                esperar(page)
                assert page.locator('[data-testid="stException"]').count() == 0
                page.screenshot(path=str(destino / f"streamlit_{caso.replace(' ', '_')}.png"))
        browser.close()
    print(f"Capturas de {args.modo} guardadas.")
