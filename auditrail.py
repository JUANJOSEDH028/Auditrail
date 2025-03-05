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
    # Cargar los datos correctamente
    try:
        data = pd.read_csv(uploaded_file, encoding='latin1', delimiter=',', quotechar="'")
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    # Convertir la columna 'Marca de tiempo' a formato datetime
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

    # Mostrar usuarios activos
    st.header("Usuarios del Sistema")
    users = filtered_data['Usuario'].unique()
    st.write("Usuarios activos:", users)

    # Cambios analógicos y digitales
    st.header("Cambios Analógicos y Digitales")
    analog_changes = filtered_data[filtered_data['Texto'].str.contains("analógico", case=False, na=False)]
    digital_changes = filtered_data[filtered_data['Texto'].str.contains("digital", case=False, na=False)]

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

    # Agregar columnas auxiliares para análisis adicionales
    data['Date'] = data['Marca de tiempo'].dt.date
    data['Hour'] = data['Marca de tiempo'].dt.hour

    # Cambios más frecuentes
    representative_changes = filtered_data.groupby('Texto').size().sort_values(ascending=False).head(10)

    # Gráfico de cambios más frecuentes
    st.header("Cambios Más Frecuentes")
    plt.figure(figsize=(10, 5))
    plt.bar(representative_changes.index, representative_changes.values)
    plt.title("Cambios Más Frecuentes")
    plt.xticks(rotation=45, ha='right')
    st.pyplot(plt)

    # Distribución de cambios por usuario
    user_changes = filtered_data['Usuario'].value_counts()
    st.header("Distribución de Cambios por Usuario")
    plt.figure(figsize=(6, 6))
    plt.pie(user_changes, labels=user_changes.index, autopct='%1.1f%%', startangle=140)
    plt.title("Cambios por Usuario")
    st.pyplot(plt)

    # Filtro para el mapa de calor
    st.sidebar.header("Filtro de Fechas (Mapa de Calor)")
    min_date = data['Date'].min()
    max_date = data['Date'].max()
    start_date_heat, end_date_heat = st.sidebar.date_input(
        "Seleccione el rango de fechas para el Mapa de Calor",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    filtered_range_data = data[(data['Date'] >= start_date_heat) & (data['Date'] <= end_date_heat)]
    all_hours = list(range(24))
    heatmap_data = filtered_range_data.pivot_table(index='Date', columns='Hour', aggfunc='size', fill_value=0)
    heatmap_data = heatmap_data.reindex(columns=all_hours, fill_value=0)

    if not heatmap_data.empty:
        st.header("Mapa de Calor: Actividad por Hora y Día")
        plt.figure(figsize=(14, 6))
        sns.heatmap(heatmap_data, cmap='coolwarm', annot=True, fmt="d", cbar_kws={'label': 'Número de Cambios'})
        plt.xlabel("Hora del Día")
        plt.ylabel("Fecha")
        plt.xticks(rotation=45)
        st.pyplot(plt)
    else:
        st.warning("No hay datos disponibles para el rango seleccionado.")

    # Sección de alertas
    st.header("Alertas del Sistema")
    st.sidebar.header("Filtro de Franja Horaria")
    start_hour = st.sidebar.slider("Hora de inicio (fuera de horario)", 0, 23, 22)
    end_hour = st.sidebar.slider("Hora de fin (fuera de horario)", 0, 23, 6)

    # Manejo correcto del rango horario
    if start_hour <= end_hour:
        night_changes = filtered_data[
            (filtered_data['Marca de tiempo'].dt.hour >= start_hour) &
            (filtered_data['Marca de tiempo'].dt.hour <= end_hour)
        ]
    else:
        night_changes = filtered_data[
            (filtered_data['Marca de tiempo'].dt.hour >= start_hour) |
            (filtered_data['Marca de tiempo'].dt.hour <= end_hour)
        ]

    if not night_changes.empty:
        st.warning(f"⚠️ Cambios realizados fuera de horario ({start_hour}:00 - {end_hour}:00):")
        st.write(night_changes)

    # Usuarios con alta frecuencia de cambios
    high_activity_users = user_changes[user_changes > user_changes.mean() + 2 * user_changes.std()]
    if not high_activity_users.empty:
        st.warning("⚠️ Usuarios con actividad inusualmente alta:")
        st.write(high_activity_users)

    # Acciones críticas
    critical_keywords = ['error', 'fallo', 'alarma', 'crítico']
    critical_changes = filtered_data[filtered_data['Texto'].str.contains('|'.join(critical_keywords), case=False, na=False)]
    if not critical_changes.empty:
        st.error("❗ Acciones críticas detectadas:")
        st.write(critical_changes)

else:
    st.info("Cargue un archivo CSV para comenzar el análisis.")
