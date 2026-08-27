"""Genera el dataset sintetico de ventas retail usado por el dashboard.

Se versiona el CSV resultante para que el contenedor no dependa de internet.
Uso: python data/generar_dataset.py
"""
import numpy as np
import pandas as pd

SEMILLA = 42
N = 12000
INICIO = "2023-01-01"
FIN = "2025-12-31"

CATEGORIAS = {
    "Tecnologia":   {"peso": 0.22, "ticket": (350, 140), "margen": 0.18},
    "Electrodomesticos": {"peso": 0.14, "ticket": (520, 200), "margen": 0.22},
    "Moda":         {"peso": 0.24, "ticket": (95, 40), "margen": 0.45},
    "Hogar":        {"peso": 0.18, "ticket": (140, 60), "margen": 0.33},
    "Deportes":     {"peso": 0.12, "ticket": (180, 70), "margen": 0.30},
    "Belleza":      {"peso": 0.10, "ticket": (70, 28), "margen": 0.50},
}

PRODUCTOS = {
    "Tecnologia": ["Laptop Pro 14", "Smartphone X", "Tablet Air", "Monitor 27\"", "Audifonos ANC"],
    "Electrodomesticos": ["Refrigeradora 400L", "Lavadora 12kg", "Microondas 30L", "Aspiradora Robot"],
    "Moda": ["Casaca Denim", "Zapatillas Urbanas", "Polo Basico", "Jean Slim", "Vestido Casual"],
    "Hogar": ["Juego de Sabanas", "Set de Ollas", "Lampara LED", "Organizador Modular"],
    "Deportes": ["Bicicleta MTB", "Mancuernas 10kg", "Colchoneta Yoga", "Balon Pro"],
    "Belleza": ["Serum Facial", "Perfume 100ml", "Kit Skincare", "Secadora de Cabello"],
}

CIUDADES = {
    "Lima": ("Costa", 0.38), "Arequipa": ("Sur", 0.12), "Trujillo": ("Norte", 0.11),
    "Chiclayo": ("Norte", 0.08), "Piura": ("Norte", 0.07), "Cusco": ("Sur", 0.09),
    "Huancayo": ("Centro", 0.06), "Iquitos": ("Oriente", 0.05), "Tacna": ("Sur", 0.04),
}

CANALES = {"Tienda fisica": 0.45, "Web": 0.33, "App movil": 0.15, "Marketplace": 0.07}
SEGMENTOS = {"Nuevo": 0.30, "Recurrente": 0.52, "VIP": 0.18}
PAGOS = {"Tarjeta credito": 0.34, "Tarjeta debito": 0.26, "Efectivo": 0.21, "Billetera digital": 0.19}


def main() -> None:
    rng = np.random.default_rng(SEMILLA)
    dias = pd.date_range(INICIO, FIN, freq="D")

    # Estacionalidad: tendencia + ciclo anual + pico de campanas (jul y nov-dic) + fin de semana
    t = np.arange(len(dias))
    base = 1.0 + 0.00035 * t
    anual = 0.18 * np.sin(2 * np.pi * (t / 365.25) - 1.1)
    campana = np.where(dias.month.isin([11, 12]), 0.45, 0.0) + np.where(dias.month == 7, 0.20, 0.0)
    finde = np.where(dias.dayofweek >= 5, 0.22, 0.0)
    intensidad = np.clip(base + anual + campana + finde, 0.15, None)
    p_dia = intensidad / intensidad.sum()

    fechas = rng.choice(dias, size=N, p=p_dia)

    cats = list(CATEGORIAS)
    categoria = rng.choice(cats, size=N, p=[CATEGORIAS[c]["peso"] for c in cats])
    ciudad = rng.choice(list(CIUDADES), size=N, p=[v[1] for v in CIUDADES.values()])
    canal = rng.choice(list(CANALES), size=N, p=list(CANALES.values()))
    segmento = rng.choice(list(SEGMENTOS), size=N, p=list(SEGMENTOS.values()))
    pago = rng.choice(list(PAGOS), size=N, p=list(PAGOS.values()))

    producto = np.array([rng.choice(PRODUCTOS[c]) for c in categoria])
    mu = np.array([CATEGORIAS[c]["ticket"][0] for c in categoria])
    sd = np.array([CATEGORIAS[c]["ticket"][1] for c in categoria])
    precio = np.round(np.clip(rng.normal(mu, sd), 12, None), 2)

    cantidad = rng.integers(1, 6, size=N)
    cantidad = np.where(precio > 400, 1, cantidad)

    desc_base = np.where(np.isin(pd.DatetimeIndex(fechas).month, [7, 11, 12]), 0.12, 0.04)
    desc_vip = np.where(segmento == "VIP", 0.06, 0.0)
    descuento = np.round(np.clip(rng.normal(desc_base + desc_vip, 0.05), 0, 0.45), 3)

    ingreso = np.round(precio * cantidad * (1 - descuento), 2)
    margen_pct = np.array([CATEGORIAS[c]["margen"] for c in categoria])
    costo = np.round(precio * cantidad * (1 - margen_pct), 2)
    utilidad = np.round(ingreso - costo, 2)

    satisfaccion = np.clip(np.round(rng.normal(np.where(utilidad > 0, 4.2, 3.4), 0.7) * 2) / 2, 1, 5)
    envio_dias = np.where(canal == "Tienda fisica", 0, rng.integers(1, 9, size=N))
    devuelto = rng.random(N) < np.where(canal == "Marketplace", 0.09, 0.04)

    df = pd.DataFrame({
        "id_venta": [f"V{100000 + i}" for i in range(N)],
        "fecha": pd.DatetimeIndex(fechas).normalize(),
        "ciudad": ciudad,
        "region": [CIUDADES[c][0] for c in ciudad],
        "canal": canal,
        "categoria": categoria,
        "producto": producto,
        "segmento_cliente": segmento,
        "metodo_pago": pago,
        "precio_unitario": precio,
        "cantidad": cantidad,
        "descuento": descuento,
        "ingreso": ingreso,
        "costo": costo,
        "utilidad": utilidad,
        "satisfaccion": satisfaccion,
        "dias_envio": envio_dias,
        "devuelto": devuelto,
    }).sort_values("fecha").reset_index(drop=True)

    df.to_csv("data/ventas_retail.csv", index=False)
    print(f"OK: {len(df)} filas -> data/ventas_retail.csv")
    print(df.head())


if __name__ == "__main__":
    main()
