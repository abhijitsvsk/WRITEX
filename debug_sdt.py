import zipfile
import xml.dom.minidom as md

try:
    z = zipfile.ZipFile('d:/writex/streamlit_test_output.docx')
    dom = md.parseString(z.read('word/document.xml'))
    body = dom.getElementsByTagName('w:body')[0]
    nodes = body.childNodes

    idxs = [i for i, n in enumerate(nodes) if n.nodeName == 'w:sdt']
    print('SDT Indices:', idxs)
    print('Total Body Nodes:', len(nodes))
    
    for i in idxs:
        print(f"\nSDT at index {i}")
        
        # Look at the previous 2 nodes
        for offset in [-2, -1]:
            j = i + offset
            if j >= 0:
                prev_node = nodes[j]
                name = prev_node.nodeName
                texts = prev_node.getElementsByTagName('w:t')
                if texts and texts[0].firstChild:
                    text_val = texts[0].firstChild.nodeValue
                else:
                    text_val = 'No Text'
                print(f"  Node before [{offset}]: {name}, Text: {text_val}")

        # Look at the next node
        if i + 1 < len(nodes):
             next_node = nodes[i+1]
             name = next_node.nodeName
             texts = next_node.getElementsByTagName('w:t')
             text_val = texts[0].firstChild.nodeValue if (texts and texts[0].firstChild) else 'No Text'
             print(f"  Node after [+1]: {name}, Text: {text_val}")
except Exception as e:
    print(f"Error: {e}")
