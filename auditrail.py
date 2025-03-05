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
    try:
        # Detectar delimitador automáticamente
        import csv
        sample = uploaded_file.read(5000).decode("latin1")
        uploaded_file.seek(0)  # Resetear la posición del archivo para leerlo después
        dialect = csv.Sniffer().sniff(sample)

        # Cargar el CSV con el delimitador detectado
        data = pd.read_csv(uploaded_file, encoding='latin1', delimiter=dialect.delimiter, quotechar="'", on_bad_lines="skip")

    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    # Convertir 'Marca de tiempo' a formato datetime
    if "Marca de tiempo" in data.columns:
        data['Marca de tiempo'] = pd.to_datetime(data['Marca de tiempo'], errors='coerce')
    else:
        st.error("El archivo no contiene la columna 'Marca de tiempo'.")
        st.stop()

    # Filtrar registros sin usuario válido
    if "Usuario" in data.columns:
        data = data[
            data["Usuario"].notna() &
            (data["Usuario"].str.strip() != "") &
            (data["Usuario"].str.lower() != "none")
        ]
    else:
        st.warning("La columna 'Usuario' no se encontró en los datos.")

    # --- SECCIÓN: Configuración del Horario de Trabajo ---
    st.header("Configuración del Horario de Trabajo")
    st.sidebar.header("Definir Lote de Trabajo")

    # Selección de la fecha y hora de inicio del lote
    start_date = st.sidebar.date_input("Fecha de inicio del lote", data['Marca de tiempo'].min().date())

    # Generar opciones de tiempo en pasos de 30 minutos
    time_options = [i / 2 for i in range(0, 48)]  # 0:00 a 23:30 en intervalos de 30 minutos
    time_labels = [f"{int(h)}:{'30' if h % 1 == 0.5 else '00'}" for h in time_options]

    start_time_index = st.sidebar.slider(
        "Hora de inicio del lote",
        min_value=0,
        max_value=len(time_options) - 1,
        value=30,  # 15:00 (3:00 PM) por defecto
        step=1
    )
    start_hour = time_options[start_time_index]

    # Selección de la fecha y hora de fin del lote
    end_date = st.sidebar.date_input("Fecha de fin del lote", data['Marca de tiempo'].max().date())

    end_time_index = st.sidebar.slider(
        "Hora de fin del lote",
        min_value=0,
        max_value=len(time_options) - 1,
        value=26,  # 13:00 (1:00 PM) por defecto
        step=1
    )
    end_hour = time_options[end_time_index]

    # Convertir la selección del usuario a objetos datetime
    start_datetime = datetime.combine(
        start_date,
        datetime.min.time()
    ) + timedelta(hours=int(start_hour), minutes=int((start_hour % 1) * 60))

    end_datetime = datetime.combine(
        end_date,
        datetime.min.time()
    ) + timedelta(hours=int(end_hour), minutes=int((end_hour % 1) * 60))

    st.sidebar.text(f"Inicio del lote: {start_datetime.strftime('%Y-%m-%d %H:%M')} hrs")
    st.sidebar.text(f"Fin del lote: {end_datetime.strftime('%Y-%m-%d %H:%M')} hrs")

    # Filtrar eventos dentro del horario de trabajo correctamente
    work_time_data = data[
        (data['Marca de tiempo'] >= start_datetime) & 
        (data['Marca de tiempo'] <= end_datetime)
    ]

    # Filtrar eventos fuera del horario de trabajo correctamente
    out_of_work_data = data[
        (data['Marca de tiempo'] < start_datetime) | 
        (data['Marca de tiempo'] > end_datetime)
    ]

    # Mostrar advertencias solo si hay eventos fuera del horario establecido
    if not out_of_work_data.empty:
        st.warning(f"⚠️ Eventos ocurridos fuera del horario de trabajo ({start_datetime.strftime('%Y-%m-%d %H:%M')} - {end_datetime.strftime('%Y-%m-%d %H:%M')}):")
        st.write(out_of_work_data)
    else:
        st.success("✅ No se detectaron eventos fuera del horario de trabajo.")

    # --- GRÁFICOS Y ANÁLISIS ---
    st.header("Análisis de Auditoría")

    # Cambios analógicos y digitales
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

    # Filtro para el mapa de calor
    st.sidebar.header("Filtro de Fechas (Mapa de Calor)")
    min_date = data['Marca de tiempo'].min().date()
    max_date = data['Marca de tiempo'].max().date()
    start_date_heat, end_date_heat = st.sidebar.date_input(
        "Seleccione el rango de fechas para el Mapa de Calor",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    filtered_range_data = data[(data['Marca de tiempo'].dt.date >= start_date_heat) & (data['Marca de tiempo'].dt.date <= end_date_heat)]
    
    if not filtered_range_data.empty:
        st.header("Mapa de Calor: Actividad por Hora y Día")
        heatmap_data = filtered_range_data.pivot_table(index=filtered_range_data['Marca de tiempo'].dt.date, columns=filtered_range_data['Marca de tiempo'].dt.hour, aggfunc='size', fill_value=0)

        plt.figure(figsize=(14, 6))
        sns.heatmap(heatmap_data, cmap='coolwarm', annot=True, fmt="d", cbar_kws={'label': 'Número de Cambios'})
        plt.xlabel("Hora del Día")
        plt.ylabel("Fecha")
        plt.xticks(rotation=45)
        st.pyplot(plt)
    else:
        st.warning("No hay datos disponibles para el rango seleccionado.")

else:
    st.info("Cargue un archivo CSV para comenzar el análisis.")
