# This script parses the toc.ncx file from an EPUB and extracts the hierarchical structure of the poet's works.
# It then formats this data for use in the POETS constant.
import xml.etree.ElementTree as ET
import json
import sys
import io

def parse_toc_ncx(file_path):
    """Parse toc.ncx file and extract hierarchical structure"""
    
    # Parse XML with UTF-8 encoding
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Define namespace
    ns = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
    
    # Get poet name from docTitle
    doc_title = root.find('.//ncx:docTitle/ncx:text', ns)
    poet_name = doc_title.text.strip() if doc_title is not None else "Unknown"
    
    # Get navMap
    nav_map = root.find('.//ncx:navMap', ns)
    
    def parse_nav_point(nav_point):
        """Recursively parse navPoint elements"""
        nav_label = nav_point.find('ncx:navLabel/ncx:text', ns)
        content = nav_point.find('ncx:content', ns)
        
        label = nav_label.text.strip() if nav_label is not None else ""
        src = content.get('src') if content is not None else ""
        
        # Get children
        children = []
        for child in nav_point.findall('ncx:navPoint', ns):
            children.append(parse_nav_point(child))
        
        result = {
            'label': label,
            'src': src
        }
        
        if children:
            result['children'] = children
            
        return result
    
    # Parse all top-level navPoints
    categories = []
    for nav_point in nav_map.findall('ncx:navPoint', ns):
        categories.append(parse_nav_point(nav_point))
    
    return {
        'poet': poet_name,
        'categories': categories
    }

def format_for_poets(data):
    """Format parsed data for POETS constant"""
    poet_name = data['poet']
    categories = data['categories']
    
    # Find the main poet category (usually the 3rd one after promo and bio)
    main_category = None
    for cat in categories:
        if cat['label'] == poet_name and 'children' in cat:
            main_category = cat
            break
    
    if not main_category:
        return None
    
    # Extract works (like Shahnameh)
    works = main_category.get('children', [])
    
    return {
        'id': poet_name.lower().replace(' ', '_'),
        'name': poet_name,
        'hasBio': True,
        'categories': works
    }

if __name__ == '__main__':
    # Force UTF-8 output
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='strict')
    
    if len(sys.argv) < 2:
        print("Usage: python parse_toc.py <path_to_toc.ncx>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        # Parse the file
        data = parse_toc_ncx(file_path)
        
        # Format for POETS
        poet_data = format_for_poets(data)
        
        if poet_data:
            # Output as formatted JSON
            print(json.dumps(poet_data, ensure_ascii=False, indent=2))
        else:
            print("Error: Could not extract poet data", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error parsing file: {e}", file=sys.stderr)
        sys.exit(1)
