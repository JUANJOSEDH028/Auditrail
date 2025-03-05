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

    # Identificar el encabezado que contenga 'Timestamp' y 'Nodo'
    header_row = None
    for i, line in enumerate(processed_data):
        if 'Marca de tiempo' in line and 'Nodo' in line:
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
    data = pd.DataFrame(data_rows, columns=header)

    # Convertir 'Timestamp' a formato datetime
    data['Marca de tiempo'] = pd.to_datetime(data['Marca de tiempo'], errors='coerce')

    # Filtrar registros que no tengan un 'Usuario' válido
    if "Usuario" in data.columns:
        data = data[
            data["Usuario"].notna() &
            (data["Usuario"].str.strip() != "") &
            (data["Usuario"].str.lower() != "none")
        ]
    else:
        st.warning("La columna 'Usuario' no se encontró en los datos.")

    # --- Interfaz del dashboard ---
    # Filtros de fecha y hora en la barra lateral
    st.sidebar.header("Filtros de Fecha y Hora")
    start_date = st.sidebar.date_input("Fecha inicio", data['Marca de tiempo'].min().date())
    end_date = st.sidebar.date_input("Fecha fin", data['Marca de tiempo'].max().date())
    start_time = st.sidebar.time_input("Hora inicio", data['Marca de tiempo'].min().time())
    end_time = st.sidebar.time_input("Hora fin", data['Marca de tiempo'].max().time())

    # Filtrar datos según el rango seleccionado
    filtered_data = data[
        (data['Marca de tiempo'] >= pd.Timestamp.combine(start_date, start_time)) &
        (data['Marca de tiempo'] <= pd.Timestamp.combine(end_date, end_time))
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
    change_types = {
        'Analógico': analog_changes.shape[0],
        'Digital': digital_changes.shape[0]
    }
    st.header("Comparativa de Cambios Analógicos y Digitales")
    plt.figure(figsize=(6, 4))
    plt.bar(change_types.keys(), change_types.values())
    plt.title("Cambios Analógicos vs Digitales")
    st.pyplot(plt)

    # Crear columnas 'Date' y 'Hour' para análisis adicionales
    data['Date'] = data['Marca de tiempo'].dt.date
    data['Hour'] = data['Marca de tiempo'].dt.hour
    
    # Cambios representativos durante el proceso
    
    representative_changes = filtered_data.groupby('Texto').size().sort_values(ascending=False).head(10)
   

    # Gráficos adicionales: Barras de cambios más frecuentes
    st.header("Gráficos de Cambios")
    plt.figure(figsize=(10, 5))
    plt.bar(representative_changes.index, representative_changes.values)
    plt.title("Cambios Más Frecuentes")
    plt.xticks(rotation=45, ha='right')
    st.pyplot(plt)

  

    # Cambios por usuario (Distribución)
    user_changes = filtered_data['Usuario'].value_counts()
    st.header("Distribución de Cambios por Usuario")
    plt.figure(figsize=(6, 6))
    plt.pie(user_changes, labels=user_changes.index, autopct='%1.1f%%', startangle=140)
    plt.title("Cambios por Usuario")
    st.pyplot(plt)

    

    # Filtro interactivo para el Mapa de Calor en la barra lateral
    st.sidebar.header("Filtro de Fechas (Mapa de Calor)")
    min_date = data['Date'].min()
    max_date = data['Date'].max()
    start_date_heat, end_date_heat = st.sidebar.date_input(
        "Seleccione el rango de fechas para el Mapa de Calor",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date,
        key="heatmap_date"
    )

    filtered_range_data = data[
        (data['Date'] >= start_date_heat) & (data['Date'] <= end_date_heat)
    ]

    all_hours = list(range(24))
    heatmap_data = filtered_range_data.pivot_table(
        index='Date', columns='Hour', aggfunc='size', fill_value=0
    )
    heatmap_data = heatmap_data.reindex(columns=all_hours, fill_value=0)

    if not heatmap_data.empty:
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
        plt.xticks(ticks=np.arange(0.5, 24.5, 1), labels=[f"{hour}:00" for hour in all_hours], rotation=45)
        st.pyplot(plt)
    else:
        st.warning("No hay datos disponibles para el rango de fechas seleccionado en el mapa de calor.")

    # Sección de alertas
    st.header("Alertas del Sistema")
    

# --- SECCIÓN: Configuración del Horario de Trabajo ---
    st.header("Configuración del Horario de Trabajo")
    st.sidebar.header("Definir Lote de Trabajo")

    # Selección de la fecha de inicio y fin del lote
    start_date = st.sidebar.date_input("Fecha de inicio del lote", data['Marca de tiempo'].min().date())
    end_date = st.sidebar.date_input("Fecha de fin del lote", data['Marca de tiempo'].max().date())

    # Ingreso manual de la hora y minutos
    start_hour = st.sidebar.number_input("Hora de inicio (0-23)", min_value=0, max_value=23, value=15, step=1)
    start_minute = st.sidebar.number_input("Minuto de inicio (0-59)", min_value=0, max_value=59, value=0, step=1)

    end_hour = st.sidebar.number_input("Hora de fin (0-23)", min_value=0, max_value=23, value=13, step=1)
    end_minute = st.sidebar.number_input("Minuto de fin (0-59)", min_value=0, max_value=59, value=0, step=1)

    # Convertir la selección del usuario a objetos datetime
    start_datetime = datetime.combine(start_date, datetime.min.time()) + timedelta(hours=start_hour, minutes=start_minute)
    end_datetime = datetime.combine(end_date, datetime.min.time()) + timedelta(hours=end_hour, minutes=end_minute)

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

    
        # 2. Usuarios con alta frecuencia de cambios
        user_activity = filtered_data['Usuario'].value_counts()
        high_activity_users = user_activity[user_activity > user_activity.mean() + 2 * user_activity.std()]
        if not high_activity_users.empty:
            st.warning("⚠️ Usuarios con actividad inusualmente alta:")
            st.write(high_activity_users)

    # 3. Acciones críticas
    critical_keywords = ['error', 'fallo', 'alarma', 'crítico']
    critical_changes = filtered_data[
        filtered_data['Texto'].str.contains('|'.join(critical_keywords), case=False, na=False)
    ]
    if not critical_changes.empty:
        st.error("❗ Acciones críticas detectadas:")
        st.write(critical_changes)

    # 4. Cambios fuera de rango (si existen las columnas 'Antiguo' y 'Nuevo')
    if 'Antiguo' in filtered_data.columns and 'Nuevo' in filtered_data.columns:
        try:
            filtered_data['Antiguo'] = pd.to_numeric(filtered_data['Antiguo'], errors='coerce')
            filtered_data['Nuevo'] = pd.to_numeric(filtered_data['Nuevo'], errors='coerce')
            out_of_range = filtered_data[
                (filtered_data['Nuevo'] < 0) | (filtered_data['Nuevo'] > 100)
            ]
            if not out_of_range.empty:
                st.error("❗ Cambios fuera de rango detectados (0-100):")
                st.write(out_of_range)
        except Exception as e:
            st.info("No se pudieron analizar los cambios fuera de rango debido a datos no numéricos.")
else:
    st.info("Cargue un archivo CSV para comenzar el análisis.")


