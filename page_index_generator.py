"""
- bin/bash
- Python 3.13.5
- Debian "Trixie" (64 bits)
"""

#Script - Generador de indice para documento academico usando los marcadores de PDF
# CODIGO OPTIMIZADO Y REESCRITO POR GEMINI - 3.1 (THINKING)

from sys import argv
from io import BytesIO
from os.path import isfile 

import pypdf
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# --------------------------------- Funciones de apoyo --------------------------------- #

def get_page_num(reader, outline_item):
    """Obtiene el número de página real de un destino de marcador."""
    try:
        return reader.get_destination_page_number(outline_item) + 1
    except:
        return 0

def extract_all_bookmarks(reader, outlines, level=0):
    """Extrae marcadores de forma recursiva en una estructura de lista limpia."""
    extracted = []
    for item in outlines:
        if isinstance(item, list):
            # Si es una lista, son hijos del último elemento extraído
            if extracted:
                extracted[-1]['children'] = extract_all_bookmarks(reader, item, level + 1)
        else:
            extracted.append({
                'title': item.title.strip(),
                'page': get_page_num(reader, item),
                'level': level,
                'children': [],
                'dest': item # Guardamos el destino original para re-insertarlo
            })
    return extracted

# --------------------------- Configuración Inicial --------------------------- #

if len(argv) < 2:
    print("Uso: python script.py archivo.pdf")
    exit(1)

FILE_NAME = argv[1]
if not isfile(FILE_NAME):
    print(f"Error: El archivo {FILE_NAME} no existe.")
    exit(1)

PDF_READER = pypdf.PdfReader(FILE_NAME)
all_outlines = extract_all_bookmarks(PDF_READER, PDF_READER.outline[2:])

#code saved for debugging
#for x in all_outlines:
#    print(x, end="\n\n")
#exit()

# Buscar en qué página está el marcador "ÍNDICE"
index_page_original = 1 # Por defecto página 2 (índice 1)
for out in all_outlines:
    if "ÍNDICE" in out['title'].upper():
        index_page_original = out['page'] - 1
        break

# --------------------------- Configuración de Estilos --------------------------- #

style = getSampleStyleSheet()
FONT_NORMAL = "Helvetica" # Fallback por si no están las fuentes Arimo
FONT_BOLD = "Helvetica-Bold"

# Intentar cargar fuentes personalizadas
try:
    pdfmetrics.registerFont(TTFont('Arimo', 'rsc/Arimo/static/Arimo-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('Arimo-Bold', 'rsc/Arimo/static/Arimo-Bold.ttf'))
    FONT_NORMAL = "Arimo"
    FONT_BOLD = "Arimo-Bold"
except:
    print("Aviso: Fuentes Arimo no encontradas, usando Helvetica.")

FONT_SIZE = 11
LINE_SPACING = 2
DOC_MARGIN = 2.54 * cm

title_style = ParagraphStyle(
    'TitleStyle', parent=style['Heading1'], fontName=FONT_BOLD, 
    fontSize=FONT_SIZE, alignment=1
)

def get_subindex_style(level):
    return ParagraphStyle(
        f'SubIndex_{level}', parent=style['Normal'], fontName=FONT_NORMAL,
        fontSize=FONT_SIZE, leftIndent=level * 0.7 * cm,
        leading=FONT_SIZE * LINE_SPACING
    )

# ---------------------------- Generar el PDF del Índice --------------------------- #

buffer_pdf = BytesIO()
doc = SimpleDocTemplate(
    buffer_pdf, pagesize=letter,
    leftMargin=DOC_MARGIN, rightMargin=DOC_MARGIN,
    topMargin=DOC_MARGIN, bottomMargin=DOC_MARGIN
)

elements = [Paragraph("ÍNDICE", title_style)]

def calculate_dots(text, page_num, level):
    # letter[0] es el ancho total. Restamos márgenes e indentación.
    available_width = letter[0] - (DOC_MARGIN * 2) - (level * 2 * cm)
    text_width = pdfmetrics.stringWidth(text + " ", FONT_NORMAL, FONT_SIZE)
    page_width = pdfmetrics.stringWidth(" " + str(page_num), FONT_NORMAL, FONT_SIZE)
    dot_width = pdfmetrics.stringWidth(".", FONT_NORMAL, FONT_SIZE)

    dots_needed = int((available_width - text_width - page_width) / dot_width) - 5

    # for debug
    #print(f"texto: {text.encode()}")
    #print(f"espacio libre: {available_width}")
    #print(f"espacio de texto: {text_width}")
    #print(f"espacio de numero: {page_width}")
    #print(f"espacio de punto: {dot_width}")
    #print(f"puntos necesarios: {dots_needed}")    

    return "." * max(0, dots_needed)

def add_to_index(items, level=0):
    for item in items:
        dots = calculate_dots(item['title'], item['page'], level)
        text = f"{item['title']} {dots} {item['page']}"
        elements.append(Paragraph(text, get_subindex_style(level)))
        if item['children']:
            add_to_index(item['children'], level + 1)

add_to_index(all_outlines)
doc.build(elements)

buffer_pdf.seek(0)
new_index_reader = pypdf.PdfReader(buffer_pdf)

# ---------------------------- Construcción del PDF Final ---------------------------- #

#saved for debugging
#output_pdf = pypdf.PdfWriter()
#for z in new_index_reader.pages:
#    output_pdf.add_page(z)
#output_pdf.write("temp_index.pdf")
#exit()


writer = pypdf.PdfWriter()

# 1. Añadir páginas antes del índice original
for i in range(index_page_original):
    writer.add_page(PDF_READER.pages[i])

# 2. Añadir las nuevas páginas del índice generado
index_pages_count = len(new_index_reader.pages)
for page in new_index_reader.pages:
    writer.add_page(page)

# 3. Añadir el resto de páginas (saltando la página de índice antigua)
# Si el índice original era la página 2, saltamos la 2 (index 1)
for i in range(index_page_original + 1, len(PDF_READER.pages)):
    page = PDF_READER.pages[i]
    
    # Añadir número de página en el pie (Opcional, según tu código)
    # Nota: El desplazamiento de página depende de si el nuevo índice es más largo que el anterior
    canvas_buffer = BytesIO()
    can = canvas.Canvas(canvas_buffer, pagesize=letter)
    can.setFont(FONT_BOLD, 9)
    can.drawCentredString(letter[0]/2, 1*cm, str(i + 1 + (index_pages_count - 1)))
    can.save()
    canvas_buffer.seek(0)
    
    num_pdf = pypdf.PdfReader(canvas_buffer)
    page.merge_page(num_pdf.pages[0])
    writer.add_page(page)

# ---------------------------- Re-insertar Marcadores ---------------------------- #

def reinsert_bookmarks(items, parent=None):
    for item in items:
        # Ajustar el número de página si el índice creció
        # (Si el nuevo índice tiene más páginas que el viejo, hay que desplazar)
        page_offset = index_pages_count - 1
        new_page_index = item['page'] - 1
        if new_page_index > index_page_original:
            new_page_index += page_offset
            
        # Asegurarse de no exceder el total de páginas
        new_page_index = min(new_page_index, len(writer.pages) - 1)
        
        new_bookmark = writer.add_outline_item(
            item['title'], 
            new_page_index, 
            parent=parent
        )
        if item['children']:
            reinsert_bookmarks(item['children'], parent=new_bookmark)

reinsert_bookmarks(all_outlines)

# Guardar resultado
output_name = "resultado_con_indice.pdf"
with open(output_name, "wb") as f:
    writer.write(f)

print(f"Éxito: Documento generado como '{output_name}'")