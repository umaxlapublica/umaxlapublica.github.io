import pandas as pd

# 1. Carga el archivo CSV
df = pd.read_csv('recortes.csv')

# 2. Abrimos el archivo recortes.tex para escribir
with open('recortes.tex', 'w', encoding='utf-8') as f:
    f.write(r"\begin{itemize}[leftmargin=*, labelsep=0.6em, itemsep=0.8em]" + "\n")
    
    # 3. Recorremos cada fila extrayendo la fecha (columna 0) y descripción (columna 2)
    for index, row in df.iterrows():
        fecha = row.iloc[0]
        recorte = row.iloc[2]
        
        # Formateamos la fecha (viene como string en el CSV)
        # Ejemplo: "3/06/2026 16:45:05"
        fecha_str = str(fecha).strip() if pd.notnull(fecha) else ''
        
        # Limpiamos el texto del recorte por si hay valores nulos
        recorte_str = str(recorte).strip() if pd.notnull(recorte) else ''
        
        # Solo escribimos si hay contenido
        if fecha_str and recorte_str:
            # Escribe la línea formateada en LaTeX usando \itemrecorte
            f.write(f'    \\itemrecorte{{{fecha_str}}}{{{recorte_str}}}\n')
            f.write("\n")
    
    f.write(r"\end{itemize}" + "\n")

print("✓ Archivo recortes.tex generado")