import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from datetime import datetime, timedelta

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

    # Identificar el encabezado que contenga 'Marca de tiempo' y 'Nodo'
    header_row = None
    for i, line in enumerate(processed_data):
        if 'Marca de tiempo' in line and 'Nodo' in line:
            header_row = i
            break

    # Verificar si se encontró el encabezado adecuado
    if header_row is None:
        st.error("No se encontró el encabezado adecuado en el archivo. Verifica que el archivo contenga los campos 'Marca de tiempo' y 'Nodo'.")
        st.stop()

    # Extraer el encabezado y las filas de datos
    header = processed_data[header_row].split(',')
    data_rows = [
        row.split(',') for row in processed_data[header_row + 1:]
        if len(row.split(',')) == len(header)
    ]

    # Crear el DataFrame
    data = pd.DataFrame(data_rows, columns=header)

    # Convertir 'Marca de tiempo' a formato datetime
    data['Marca de tiempo'] = pd.to_datetime(data['Marca de tiempo'], errors='coerce')

    # Filtrar registros sin usuario válido
    if "Usuario" in data.columns:
        data = data[
            data["Usuario"].notna() &
            (data["Usuario"].str.strip() != "") &
            (data["Usuario"].str.lower() != "none")
        ]
    else:
        st.warning("La columna 'Usuario' no se encontró en los datos.")

    # --- Filtros de Fecha y Hora en la barra lateral ---
    st.sidebar.header("Filtros de Fecha y Hora")

    # Selección de la fecha y hora de inicio
    start_date = st.sidebar.date_input("Fecha inicio", data['Marca de tiempo'].min().date())
    start_time = st.sidebar.time_input("Hora inicio", data['Marca de tiempo'].min().time())

    # Selección de la fecha y hora de fin
    end_date = st.sidebar.date_input("Fecha fin", data['Marca de tiempo'].max().date())
    end_time = st.sidebar.time_input("Hora fin", data['Marca de tiempo'].max().time())

    # Convertir fecha y hora seleccionadas a formato datetime
    start_datetime = datetime.combine(start_date, start_time)
    end_datetime = datetime.combine(end_date, end_time)

    # Filtrar eventos dentro del horario de trabajo
    work_time_data = data[
        (data['Marca de tiempo'] >= start_datetime) & 
        (data['Marca de tiempo'] <= end_datetime)
    ]

    # Filtrar eventos fuera del horario de trabajo
    out_of_work_data = data[
        (data['Marca de tiempo'] < start_datetime) | 
        (data['Marca de tiempo'] > end_datetime)
    ]

    # Mostrar advertencias solo si hay eventos fuera del horario establecido
    if not out_of_work_data.empty:
        st.warning(f"⚠️ Eventos fuera del horario de trabajo ({start_datetime.strftime('%Y-%m-%d %H:%M')} - {end_datetime.strftime('%Y-%m-%d %H:%M')}):")
        st.write(out_of_work_data)
    else:
        st.success("✅ No se detectaron eventos fuera del horario de trabajo.")

    # --- MAPA DE CALOR ---
    st.sidebar.header("Filtro de Fechas (Mapa de Calor)")
    min_date = data['Marca de tiempo'].min().date()
    max_date = data['Marca de tiempo'].max().date()

    start_date_heat, end_date_heat = st.sidebar.date_input(
        "Seleccione el rango de fechas para el Mapa de Calor",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Filtrar los datos dentro del rango seleccionado
    filtered_range_data = data[
        (data['Marca de tiempo'].dt.date >= start_date_heat) &
        (data['Marca de tiempo'].dt.date <= end_date_heat)
    ]

    if not filtered_range_data.empty:
        # Crear columnas 'Date' y 'Hour' para análisis en el mapa de calor
        filtered_range_data['Date'] = filtered_range_data['Marca de tiempo'].dt.date
        filtered_range_data['Hour'] = filtered_range_data['Marca de tiempo'].dt.hour

        all_hours = list(range(24))
        heatmap_data = filtered_range_data.pivot_table(
            index='Date', columns='Hour', aggfunc='size', fill_value=0
        )
        heatmap_data = heatmap_data.reindex(columns=all_hours, fill_value=0)

        st.header(f"Actividad por Hora ({start_date_heat} a {end_date_heat})")
        plt.figure(figsize=(14, 6))
        sns.heatmap(
            heatmap_data,
            cmap='coolwarm',
            annot=True,
            fmt="d",
            cbar_kws={'label': 'Número de Cambios'}
        )
        plt.title("Mapa de Calor: Actividad por Hora y Día")
        plt.xlabel("Hora del Día")
        plt.ylabel("Fecha")
        plt.xticks(rotation=45)
        st.pyplot(plt)
    else:
        st.warning("No hay datos disponibles para el rango de fechas seleccionado en el mapa de calor.")

    # --- OTRAS SECCIONES DEL DASHBOARD ---
    st.header("Usuarios del Sistema")
    users = work_time_data['Usuario'].unique()
    st.write("Usuarios activos:", users)

    # Cambios analógicos y digitales
    st.header("Cambios Analógicos y Digitales")
    analog_changes = work_time_data[work_time_data['Texto'].str.contains("analógico", case=False, na=False)]
    digital_changes = work_time_data[work_time_data['Texto'].str.contains("digital", case=False, na=False)]

    st.subheader("Cambios Analógicos")
    st.write(analog_changes)

    st.subheader("Cambios Digitales")
    st.write(digital_changes)

    # Comparativa analógico vs digital
    st.header("Comparativa de Cambios Analógicos y Digitales")
    change_types = {
        'Analógico': analog_changes.shape[0],
        'Digital': digital_changes.shape[0]
    }
    plt.figure(figsize=(6, 4))
    plt.bar(change_types.keys(), change_types.values())
    plt.title("Cambios Analógicos vs Digitales")
    st.pyplot(plt)

else:
    st.info("Cargue un archivo CSV para comenzar el análisis.")


