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
    try:
        # Detectar el delimitador automáticamente
        import csv
        import io

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

    # --- Interfaz del dashboard ---
    st.sidebar.header("Filtros de Fecha y Hora")
    start_date = st.sidebar.date_input("Fecha inicio", data['Marca de tiempo'].min().date())
    end_date = st.sidebar.date_input("Fecha fin", data['Marca de tiempo'].max().date())
    start_time = st.sidebar.time_input("Hora inicio", data['Marca de tiempo'].min().time())
    end_time = st.sidebar.time_input("Hora fin", data['Marca de tiempo'].max().time())

    # Convertir fecha y hora a formato datetime
    start_datetime = pd.Timestamp.combine(start_date, start_time)
    end_datetime = pd.Timestamp.combine(end_date, end_time)

    # Filtrar datos en el rango seleccionado
    filtered_data = data[
        (data['Marca de tiempo'] >= start_datetime) & (data['Marca de tiempo'] <= end_datetime)
    ]

    st.write("Datos cargados correctamente:", filtered_data.head())  # Muestra una vista previa de los datos

else:
    st.info("Cargue un archivo CSV para comenzar el análisis.")

