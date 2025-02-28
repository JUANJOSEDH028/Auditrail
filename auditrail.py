import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Título del dashboard
st.title("Dashboard de Auditoría")

# Cargador de archivo CSV
uploaded_file = st.file_uploader("Seleccione el archivo CSV de Auditoría", type=["csv"])

if uploaded_file is not None:
    # Procesar el archivo cargado línea por línea
    processed_data = []
    for line in uploaded_file.read().decode('latin1').splitlines():
        if line.strip():  # Ignorar líneas vacías
            processed_data.append(line.strip())

    # Identificar el encabezado que contenga 'Timestamp' y 'Nodo'
    header_row = None
    for i, line in enumerate(processed_data):
        if 'Timestamp' in line and 'Nodo' in line:
            header_row = i
            break

    # Verificar si se encontró el encabezado adecuado
    if header_row is None:
        st.error("No se encontró el encabezado adecuado en el archivo. Verifica que el archivo contenga los campos 'Timestamp' y 'Nodo'.")
        st.stop()

    # Extraer el encabezado y las filas de datos
    header = processed_data[header_row].split(',')
    data_rows = [
        row.split(',') for row in processed_data[header_row + 1:]
        if len(row.split(',')) == len(header)
    ]

    # Crear el DataFrame
    data = pd.DataFram

