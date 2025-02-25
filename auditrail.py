
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Tratamiento de los datos
#file_path = r"\\servernas\Validaciones-Metrología\COORVSC-CALIFICACIONES\CALIFICACIONES\EQUIPOS\Secador de Lecho Fluido Glatt 600 kg N°4\calificación 2025\VSC\audit.csv" # Reemplaza con la ruta del archivo cargado

# Leer el archivo original y procesar las líneas
processed_data = []
with open("Audit1.csv", 'r', encoding='latin1') as file:
    for line in file:
        if line.strip():  # Ignorar líneas vacías
            processed_data.append(line.strip())

# Identificar el encabezado y estructurar los datos
header_row = None
for i, line in enumerate(processed_data):
    if 'Timestamp' in line and 'Nodo' in line:
        header_row = i
        break

header = processed_data[header_row].split(',')
data_rows = [
    row.split(',') for row in processed_data[header_row + 1:]
    if len(row.split(',')) == len(header)
]

# Crear un DataFrame con los datos estructurados
data = pd.DataFrame(data_rows, columns=header)

# Convertir el campo 'Timestamp' a formato datetime
data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')

# Interfaz del dashboard
st.title("Dashboard de Auditoría")

# Filtros de fecha y hora
st.sidebar.header("Filtros de Fecha y Hora")
start_date = st.sidebar.date_input("Fecha inicio", data['Timestamp'].min().date())
end_date = st.sidebar.date_input("Fecha fin", data['Timestamp'].max().date())
start_time = st.sidebar.time_input("Hora inicio", data['Timestamp'].min().time())
end_time = st.sidebar.time_input("Hora fin", data['Timestamp'].max().time())

# Filtrar datos
filtered_data = data[
    (data['Timestamp'] >= pd.Timestamp.combine(start_date, start_time)) &
    (data['Timestamp'] <= pd.Timestamp.combine(end_date, end_time))
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

# Cambios representativos durante el proceso
st.header("Cambios Representativos")
representative_changes = filtered_data.groupby('Texto').size().sort_values(ascending=False).head(10)
st.bar_chart(representative_changes)

# Gráficos adicionales
st.header("Gráficos de Cambios")
plt.figure(figsize=(10, 5))
plt.bar(representative_changes.index, representative_changes.values)
plt.title("Cambios Más Frecuentes")
plt.xticks(rotation=45, ha='right')
st.pyplot(plt)



# Cambios a lo largo del tiempo
time_series = filtered_data.set_index('Timestamp').resample('D').size()

st.header("Cambios a lo Largo del Tiempo")
st.line_chart(time_series)

# Cambios por usuario
user_changes = filtered_data['Usuario'].value_counts()

st.header("Distribución de Cambios por Usuario")
plt.figure(figsize=(6, 6))
plt.pie(user_changes, labels=user_changes.index, autopct='%1.1f%%', startangle=140)
plt.title("Cambios por Usuario")
st.pyplot(plt)




# Comparación analógico vs digital
change_types = {
    'Analógico': analog_changes.shape[0],
    'Digital': digital_changes.shape[0]
}

st.header("Comparativa de Cambios Analógicos y Digitales")
plt.figure(figsize=(6, 4))
plt.bar(change_types.keys(), change_types.values())
plt.title("Cambios Analógicos vs Digitales")
st.pyplot(plt)



import numpy as np
import seaborn as sns

# Asegurar que 'Timestamp' esté en formato datetime
data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')

# Crear columnas 'Date' y 'Hour' en el DataFrame original
data['Date'] = data['Timestamp'].dt.date
data['Hour'] = data['Timestamp'].dt.hour

# Crear un filtro interactivo para seleccionar el rango de fechas
st.sidebar.header("Filtro de Fechas")
min_date = data['Date'].min()
max_date = data['Date'].max()
start_date, end_date = st.sidebar.date_input(
    "Seleccione el rango de fechas",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date,
)

# Filtrar los datos según el rango de fechas seleccionado
filtered_range_data = data[
    (data['Date'] >= start_date) & (data['Date'] <= end_date)
]

# Crear un rango fijo de horas para el eje X
all_hours = list(range(24))  # De 0 a 23 horas
heatmap_data = filtered_range_data.pivot_table(
    index='Date', columns='Hour', aggfunc='size', fill_value=0
)

# Asegurar que todas las horas estén presentes
heatmap_data = heatmap_data.reindex(columns=all_hours, fill_value=0)

# Mostrar el gráfico solo si hay datos
if not heatmap_data.empty:
    st.header(f"Actividad por Hora ({start_date} a {end_date})")
    plt.figure(figsize=(14, 6))
    sns.heatmap(
        heatmap_data,
        cmap='coolwarm',
        annot=True,  # Mostrar valores en celdas
        fmt="d",  # Formato de números enteros
        cbar_kws={'label': 'Número de Cambios'}
    )
    plt.title("Mapa de Calor: Actividad por Hora y Día")
    plt.xlabel("Hora del Día")
    plt.ylabel("Fecha")
    plt.xticks(ticks=np.arange(0.5, 24.5, 1), labels=[f"{hour}:00" for hour in all_hours], rotation=45)
    st.pyplot(plt)
else:
    st.warning("No hay datos disponibles para el rango de fechas seleccionado.")





# Sección de alertas
st.header("Alertas del Sistema")

# Filtro interactivo para seleccionar la franja horaria
st.sidebar.header("Filtro de Franja Horaria")
start_hour = st.sidebar.slider("Hora de inicio (fuera de horario)", 0, 23, 22)
end_hour = st.sidebar.slider("Hora de fin (fuera de horario)", 0, 23, 6)

# 1. Cambios fuera de horario
night_changes = filtered_data[
    (filtered_data['Timestamp'].dt.hour >= start_hour) | 
    (filtered_data['Timestamp'].dt.hour <= end_hour)
]
if not night_changes.empty:
    st.warning(f"⚠️ Cambios realizados fuera de horario ({start_hour}:00 - {end_hour}:00):")
    st.write(night_changes)

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

# 4. Cambios fuera de rango (si se dispone de datos numéricos)
if 'Antiguo' in filtered_data.columns and 'Nuevo' in filtered_data.columns:
    try:
        filtered_data['Antiguo'] = pd.to_numeric(filtered_data['Antiguo'], errors='coerce')
        filtered_data['Nuevo'] = pd.to_numeric(filtered_data['Nuevo'], errors='coerce')
        out_of_range = filtered_data[
            (filtered_data['Nuevo'] < 0) | (filtered_data['Nuevo'] > 100)  # Ajusta el rango según tu caso
        ]
        if not out_of_range.empty:
            st.error("❗ Cambios fuera de rango detectados (0-100):")
            st.write(out_of_range)
    except Exception as e:
        st.info("No se pudieron analizar los cambios fuera de rango debido a datos no numéricos.")

