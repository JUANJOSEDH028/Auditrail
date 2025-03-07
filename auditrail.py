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

    # --- GRÁFICO DE EVENTOS FUERA DEL HORARIO ---
    if not out_of_work_data.empty:
        # Asegurar que 'Marca de tiempo' está en formato datetime
        out_of_work_data['Hora'] = out_of_work_data['Marca de tiempo'].dt.hour

        # Contar la cantidad de eventos por hora
        event_counts = out_of_work_data['Hora'].value_counts().sort_index()

        # Obtener los textos de los eventos ocurridos en cada hora
        event_labels = out_of_work_data.groupby('Hora')['Texto'].apply(lambda x: '\n'.join(x.unique()))

        # Crear el gráfico de barras
        plt.figure(figsize=(12, 6))
        ax = sns.barplot(x=event_counts.index, y=event_counts.values, palette="Blues")
        plt.xlabel("Hora del día")
        plt.ylabel("Cantidad de eventos fuera del horario")
        plt.title("Eventos fuera del horario de trabajo")
        plt.xticks(range(0, 24))

        # Agregar etiquetas de texto encima de cada barra con los nombres de los eventos
        for i, (hour, count) in enumerate(zip(event_counts.index, event_counts.values)):
            ax.text(i, count + 0.5, event_labels[hour], ha='center', fontsize=8, rotation=90)

        # Mostrar el gráfico en Streamlit
        st.header("Eventos fuera del horario de trabajo")
        st.pyplot(plt)

    else:
        st.info("No hay eventos fuera del horario de trabajo para graficar.")

    # --- OTRAS SECCIONES DEL DASHBOARD ---
    # Mostrar usuarios activos
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


