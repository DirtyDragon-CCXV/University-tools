from sys import argv
from io import BytesIO
from os.path import isfile 

import pypdf
from pypdf.types import OutlineType

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph


# --------------------------------- index funtions --------------------------------- #
def GetPageNum(item : OutlineType):
    """funtion to get the number of the page referenced in the bookmark"""
    return PDF.get_page_number(item.page) + 1

def extract_childs(bookmark, previus_child = None):
    """funtion to structure fathers and chils of the index, recursive function"""
    if type(bookmark) != list:
        return (bookmark.title.strip(), GetPageNum(bookmark), previus_child)
    
    else:
        temp_list = []
        for item in bookmark[ ::-1 ]:
            return_value = extract_childs(item, previus_child)

            if type(return_value) != list:
                temp_list.append(return_value)
                previus_child = None
            else:
                previus_child = return_value

        temp_list.reverse()
        
        return temp_list

#get file path with arguments on call
FILE_NAME = argv[1]

try:
    if isfile(FILE_NAME) == False:
        print("file error.")
        exit(1)
except:
    print("executing code...")

# open the original pdf
PDF = pypdf.PdfReader(FILE_NAME)

# get bookmarks titles
pdf_outlines = PDF.outline

#code saved for debugging
#for x in pdf_outlines:
#    print(x, end="\n\n")
#exit()

#create bookmarks dict
bookmarks = []

# convert booksmarks type
for i in pdf_outlines:
    if i.title.strip() == "ÍNDICE":
        index_start = pdf_outlines.index(i)
        break

# extract the bookmarks from the pdf
saved_child = None
for bookmark in pdf_outlines[ :index_start:-1 ]:
    output_value = extract_childs(bookmark)

    if type(output_value) == list:
        saved_child = output_value

    else:    
        bookmarks.append([bookmark.title.strip(), GetPageNum(bookmark), saved_child])
        saved_child = None
bookmarks.reverse()


# --------------------------- create pdf in memory --------------------------- #
style = getSampleStyleSheet()
try:
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'rsc/arial-font/G_ari_bd.TTF')) #include Arial_BOLD font
    pdfmetrics.registerFont(TTFont('Arial', 'rsc/arial-font/arial.ttf')) #include Arial font

    FONT_BOlD = "Arial-Bold"
    FONT_NORMAL = "Arial"
except:
    FONT_BOlD = "Times-Bold"
    FONT_NORMAL = "Times-Bold"

#deafult values
FONT_SIZE_HEADING1 = 22
FONT_SIZE_NORMAL = 11
LINE_SPACING = 1.5
DOC_MARGIN = 2.2

#text style
normal_style = style["Normal"]
normal_style.fontName = FONT_NORMAL
normal_style.fontSize = FONT_SIZE_NORMAL
normal_style.leading = FONT_SIZE_NORMAL * LINE_SPACING

#paragraph style
title_style = ParagraphStyle(
    name = "title",
    parent = style["Heading1"],
    fontName = FONT_BOlD,
    fontSize = FONT_SIZE_HEADING1,
    alignment = 1,
    leading = FONT_SIZE_HEADING1 * LINE_SPACING,
    firstLineIndent = 0
)

# sub level 1 with left indent
subindex_style = ParagraphStyle(
    name = "subindex",
    parent = style["Normal"],
    fontName = FONT_NORMAL,
    fontSize = FONT_SIZE_NORMAL,
    leading = FONT_SIZE_NORMAL * LINE_SPACING,
    leftIndent = 15
)

# sub level 2 with left indent
subindex_style_2v = ParagraphStyle(
    name = "subindex",
    parent = style["Normal"],
    fontName = FONT_NORMAL,
    fontSize = FONT_SIZE_NORMAL,
    leading = FONT_SIZE_NORMAL * LINE_SPACING,
    leftIndent = 30
)

# sub level 3 with left indent
subindex_style_3v = ParagraphStyle(
    name = "subindex",
    parent = style["Normal"],
    fontName = FONT_NORMAL,
    fontSize = FONT_SIZE_NORMAL,
    leading = FONT_SIZE_NORMAL * LINE_SPACING,
    leftIndent = 45
)

subindex_styles = [normal_style, subindex_style, subindex_style_2v, subindex_style_3v]

#init buffer
buffer_pdf = BytesIO()
buffer_doc = SimpleDocTemplate(
    buffer_pdf, 
    pagesize = letter,
    leftMargin = DOC_MARGIN * cm,
    rightMargin = DOC_MARGIN * cm,
    topMargin = DOC_MARGIN * cm,
    bottomMargin = DOC_MARGIN * cm
)


# ---------------------------- Paragraph functions --------------------------- #
def GetPoints(text : str, page_num : int):
    """function to calculate the number of points to set in the sub index text"""
    page_width = letter[0] - 155
    text_space = pdfmetrics.stringWidth(text, FONT_NORMAL, FONT_SIZE_NORMAL)
    page_number_space = pdfmetrics.stringWidth(str(page_num), FONT_NORMAL, FONT_SIZE_NORMAL)
    points_space = pdfmetrics.stringWidth(".", FONT_NORMAL, FONT_SIZE_NORMAL)
    
    remain_space = page_width - text_space - page_number_space - 10

    nums_points = int(remain_space / points_space)
    return nums_points

def add_child_paragraph(child:tuple, level):
    """recursive function to add sub index text to the page"""

    #code saved for debugging
    #print(child, end="\n\n")

    if child[2] == None:
        #create the paragraph and add the text
        points_to_add = "." * ( GetPoints( child[0], child[1] ) - 10*level)
        p = Paragraph(f"{child[0]} {points_to_add} {child[1]}", subindex_styles[level])
        paragraphs.append(p)

    else:
        points_to_add = "." * ( GetPoints( child[0], child[1] ) - 10*level)
        p = Paragraph(f"{child[0]} {points_to_add} {child[1]}", subindex_styles[level])
        paragraphs.append(p)
        
        for children in child[2]:
            add_child_paragraph(children, level+1)


# creating the main paragraph page
paragraphs = []

#add the index ttile
index_title = Paragraph("ÍNDICE", title_style)
paragraphs.append(index_title)

for item in bookmarks:
    add_child_paragraph(item, 0)

buffer_doc.build(paragraphs) #construct the doc
buffer_pdf.seek(0) #get back to the start

buffer_doc = pypdf.PdfReader(buffer_pdf) #read the memory doc

#saved for debugging
#output_pdf = pypdf.PdfWriter()
#for z in buffer_doc.pages:
#    output_pdf.add_page(z)
#output_pdf.write("temp_index.pdf")
#exit()

output_pages = []
output_pages.append(PDF.pages[0]) #add cover page

for indexs in buffer_doc.pages:
    output_pages.append(indexs) #add index page

for page in PDF.pages[2:]: #add the rest of the pages
    output_pages.append(page)

# draw the numbers index bottom the each page
for p in range(2, len(output_pages)):
    canvas_buffer = BytesIO()
    canvas_draw = canvas.Canvas( canvas_buffer, pagesize = letter )
    canvas_draw.setFont(FONT_BOlD, FONT_SIZE_NORMAL)
    canvas_draw.drawString(letter[0] / 2, 1 * cm, str(p + 1))
    canvas_draw.save()
    canvas_buffer.seek(0)
    
    new_pdf_page = pypdf.PdfReader(canvas_buffer)
    output_pages[p].merge_page(new_pdf_page.pages[0])


# ---------------------------- init the final doc ---------------------------- #
output_pdf = pypdf.PdfWriter()

for page in output_pages: #add the pages
    output_pdf.add_page(page)
    
def add_bookmarks(writer, outlines, parent = None):
    """recursive function to add the bookmarks to the final file"""
    for outline in outlines:
        if isinstance(outline, list):
            sub_parent = writer.add_outline_item_dict(outline[0], parent)
            add_bookmarks(writer, outline, sub_parent)
        else:
            writer.add_outline_item_dict(outline, parent)
    
add_bookmarks(output_pdf, pdf_outlines)

#saved for debugging
#output_pdf.write("temp_doc.pdf")

output_pdf.write(FILE_NAME) #export the doc
