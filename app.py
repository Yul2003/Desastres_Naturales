
# Instalar automáticamente las dependencias si no están presentes
import subprocess
import sys

required_packages = ['dash', 'dash-bootstrap-components', 'plotly', 'pandas', 'openpyxl']

for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

## Codigo de los graficos

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc

# Carga de datos
file_path = "REPORTE_DE_EVENTOS_POR_DESASTRES_NATURALES_Y_ANTR_PICOS__Hist_rico__20250401.xlsx"
df = pd.read_excel(file_path, sheet_name="Hoja1")

# Preprocesamiento
df["FECHA DE OCURRENCIA"] = pd.to_datetime(df["FECHA DE OCURRENCIA"], errors='coerce')
df["AÑO"] = df["FECHA DE OCURRENCIA"].dt.year
df["TRIMESTRE"] = df["FECHA DE OCURRENCIA"].dt.to_period("Q").astype(str)
df["BIMESTRE"] = df["FECHA DE OCURRENCIA"].dt.month.map(lambda m: f"Bim-{(m - 1) // 2 + 1}")

df["HERIDOS"] = pd.to_numeric(df["HERIDOS"], errors='coerce').fillna(0).astype(int)
df["FALLECIDOS"] = pd.to_numeric(df["FALLECIDOS"], errors='coerce').fillna(0).astype(int)
df["DESAPARECIDOS"] = pd.to_numeric(df["DESAPARECIDOS"], errors='coerce').fillna(0).astype(int)

infra_cols = [
    "VIVIENDAS AFECTADAS", "VIVIENDAS DESTRUIDAS", "INSTITUCIONES EDUCATIVAS",
    "INSTITUCIONES SALUD", "ACUEDUCTO", "ALCANTARILLADO", "ENERGIA", "VIAS", "PUENTES"
]
infra_cols = [col for col in infra_cols if col in df.columns]
df["INFRAESTRUCTURA_AFECTADA"] = df[infra_cols].fillna(0).sum(axis=1)

# App
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H2("Dashboard de Eventos por Desastres", className="text-center my-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Categoría Afectada"),
            dcc.Dropdown(
                id="categoria",
                options=[
                    {"label": "Heridos", "value": "HERIDOS"},
                    {"label": "Fallecidos", "value": "FALLECIDOS"},
                    {"label": "Desaparecidos", "value": "DESAPARECIDOS"}
                ],
                value="HERIDOS"
            )
        ], md=4),

        dbc.Col([
            html.Label("Período de Tiempo"),
            dcc.Dropdown(
                id="periodo",
                options=[
                    {"label": "Anual", "value": "AÑO"},
                    {"label": "Trimestral", "value": "TRIMESTRE"},
                    {"label": "Bimestral", "value": "BIMESTRE"}
                ],
                value="AÑO"
            )
        ], md=4),

        dbc.Col([
            html.Label("Tipo de Evento"),
            dcc.Dropdown(
                id="evento",
                options=[{"label": e, "value": e} for e in sorted(df["TIPO DE EVENTO"].dropna().unique())],
                value=sorted(df["TIPO DE EVENTO"].dropna().unique())[0]
            )
        ], md=4),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Cambiar Fondo"),
            dcc.Checklist(
                id="fondo",
                options=[{"label": "Modo oscuro", "value": "dark"}],
                value=[]
            )
        ])
    ], className="mb-2"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico-afectados"), md=6),
        dbc.Col(dcc.Graph(id="grafico-infraestructura"), md=6),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico-eventos-municipio"), md=6),
        dbc.Col(dcc.Graph(id="grafico-causa"), md=6),
    ])
], fluid=True)

@app.callback(
    Output("grafico-afectados", "figure"),
    Input("categoria", "value"),
    Input("fondo", "value")
)
def actualizar_grafico_afectados(cat, fondo):
    fig = px.bar(df, x="TIPO DE EVENTO", y=cat, title=f"{cat.title()} por Tipo de Evento", color="TIPO DE EVENTO")
    if "dark" in fondo:
        fig.update_layout(template="plotly_dark")
    return fig

@app.callback(
    Output("grafico-infraestructura", "figure"),
    Input("periodo", "value"),
    Input("evento", "value"),
    Input("fondo", "value")
)
def actualizar_infraestructura(periodo, evento, fondo):
    filtro = df[df["TIPO DE EVENTO"] == evento]
    resumen = filtro.groupby(periodo)["INFRAESTRUCTURA_AFECTADA"].sum().reset_index()
    fig = px.line(resumen, x=periodo, y="INFRAESTRUCTURA_AFECTADA", title=f"Infraestructura Afectada ({evento})")
    if "dark" in fondo:
        fig.update_layout(template="plotly_dark")
    return fig

@app.callback(
    Output("grafico-eventos-municipio", "figure"),
    Input("fondo", "value")
)
def eventos_por_municipio(fondo):
    top_muni = df["MUNICIPIO"].value_counts().nlargest(10).reset_index()
    top_muni.columns = ["MUNICIPIO", "EVENTOS"]
    fig = px.bar(top_muni, x="EVENTOS", y="MUNICIPIO", orientation="h", title="Top 10 Municipios por Nº de Eventos")
    if "dark" in fondo:
        fig.update_layout(template="plotly_dark")
    return fig

@app.callback(
    Output("grafico-causa", "figure"),
    Input("fondo", "value")
)
def causas_probables(fondo):
    causas = df["CAUSA PROBABLE"].value_counts().nlargest(10).reset_index()
    causas.columns = ["CAUSA", "CUENTA"]
    fig = px.pie(causas, names="CAUSA", values="CUENTA", title="Principales Causas Probables")
    if "dark" in fondo:
        fig.update_layout(template="plotly_dark")
    return fig

if __name__ == '__main__':
    app.run(debug=True)
