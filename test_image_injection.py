import io
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.file_formatting.formatting import generate_report, StyleConfig
from docx.enum.text import WD_ALIGN_PARAGRAPH

text = """Experiment 2
Bar charts and Column charts

Aim:
Plot a Bar Chart, Column chart, Stacked Column chart, and a Grouped Column chart for the data given in the CSV file named “Quarter_sales.csv”.

Theory:
A bar chart is a graphical representation of data that uses rectangular bars to illustrate the values of different categories or groups. The length of each bar corresponds to the magnitude of the data it represents. Bar charts are effective for comparing individual values or displaying trends over a specific period. They are commonly used to visualize categorical data and make it easy to interpret and compare values at a glance.

A column chart is similar to a bar chart but typically uses vertical bars to represent data values. Like bar charts, column charts are excellent for comparing values across different categories, making them widely used in various fields such as business, finance, and research. The vertical orientation of the bars in a column chart allows for easy comparison of data points, and the length of each column directly corresponds to the value it represents.

A stacked column chart is an extension of the basic column chart, where multiple data series are stacked on top of one another within each category. This type of chart is useful for showing the total and the contribution of each sub-category to that total. Stacked column charts are effective in illustrating the composition of a whole and how each part contributes to the overall value, making them valuable for conveying both individual and collective trends within a dataset.

A grouped column chart, on the other hand, displays multiple sets of data side by side within each category. Each group consists of several columns, each representing a different data series. Grouped column charts are beneficial when you want to compare values across multiple data series within each category. This format allows for easy visual comparison of different groups, making it a useful tool in scenarios where you need to analyze and contrast multiple datasets simultaneously.

CODE:
data <- read.csv("Quater_sales.csv")

head(data)

str(data)
print(data)

grouped <- aggregate(data$profit,list(data$quarter),sum)

colnames(grouped) <- c("Quarter","Profit") grouped

barplot(grouped$Profit,
names.arg=grouped$Quarter, col="blue",
main="Quarterly Profit", xlab="Quarter",
ylab="Profit")

barplot(grouped$Profit,
names.arg=grouped$Quarter,
horiz=TRUE,
col="green",
main="Quarterly Profit")
install.packages("ggplot2")
library(ggplot2)
ggplot(grouped,aes(x=Quarter,y=Profit))+geom_col(fill="steelblue")
ggplot(data,aes(x=quarter, y=profit,fill=product))+geom_col(position="dodge")

OUTPUT:
quarter product profit
1 Q1 A 10 2 Q1 B 14 3 Q1 C 13
4 Q2 A 12 5 Q2 B 11 6 Q2 C 13 quarter product profit 1 Q1 A 10
2 Q1 B 14 3 Q1 C 13
4 Q2 A 12 5 Q2 B 11 6 Q2 C 13 7 Q3 A 13 8 Q3 B 15 9 Q3 C 12 10 Q4 A 16
11 Q4 B 18 12 Q4 C 17
Quarter Profit 1 Q1 37 2 Q2 36
3 Q3 40
4 Q4"""

# Parse simple AST
lines = text.split("\n")
structure = []
in_code = False
code_lines = []

for line in lines:
    line = line.strip()
    if not line:
        continue
    
    if line == "CODE:":
        in_code = True
        structure.append({"type": "section_header", "text": "CODE"})
        continue
        
    if line == "OUTPUT:":
        in_code = False
        if code_lines:
            structure.append({"type": "code_block", "text": "\n".join(code_lines)})
            code_lines = []
        structure.append({"type": "section_header", "text": "OUTPUT"})
        continue
        
    if in_code:
        code_lines.append(line)
    elif line in ["Aim:", "Theory:"]:
        structure.append({"type": "section_header", "text": line.strip(":")})
    elif line.startswith("Experiment "):
        structure.append({"type": "chapter", "text": line})
    elif "Bar charts and Column charts" in line:
        structure.append({"type": "paragraph", "text": line})
    else:
        # Use terminal_output for output block simulation
        if structure and structure[-1].get("text") == "OUTPUT":
             structure.append({"type": "terminal_output", "text": line})
        else:
             structure.append({"type": "paragraph", "text": line})

if code_lines:
    structure.append({"type": "code_block", "text": "\n".join(code_lines)})

# Image injection (BOTTOM PLACEMENT)
image1_path = r"C:\Users\jithu\.gemini\antigravity\brain\de43b68d-19ac-4236-ad3c-de557e73e03d\media__1783761098857.png"
image2_path = r"C:\Users\jithu\.gemini\antigravity\brain\de43b68d-19ac-4236-ad3c-de557e73e03d\media__1783761118088.png"

with open(image1_path, "rb") as f1, open(image2_path, "rb") as f2:
    structure.append({"type": "image", "content": f1.read()})
    structure.append({"type": "image", "content": f2.read()})

# Setup strict StyleConfig
config = StyleConfig(
    margin_inches=1.0,
    heading_font="Times New Roman",
    heading_size_pt=14.0,
    heading_bold=True,
    heading_alignment=WD_ALIGN_PARAGRAPH.CENTER,
    content_font="Times New Roman",
    content_size_pt=12.0,
    content_alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
    line_spacing=1.5,
    space_before_pt=0.0,
    space_after_pt=0.0,
    code_language="R",
    continuous_sections=True
)

output_path = "test_images_bottom_continuous.docx"
with open(output_path, "wb") as f:
    generate_report(structure, f, style_config=config)
    
print(f"Generated successfully at {output_path}")
