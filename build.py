#!/usr/bin/env python3
import os
import argparse
import markdown
import re
import json
import time
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape


def extract_headings(body):
    """Extract all headings from markdown body, excluding code blocks."""
    headings = []
    in_code_block = False
    
    for line in body.split('\n'):
        stripped = line.strip()
        
        # Track code block boundaries
        if stripped.startswith('```') or stripped.startswith('~~~'):
            in_code_block = not in_code_block
            continue
        
        # Skip lines inside code blocks
        if in_code_block:
            continue
        
        # Extract headings (h1-h6)
        if stripped.startswith('#'):
            level = 0
            for char in stripped:
                if char == '#':
                    level += 1
                else:
                    break
            if level > 0 and level <= 6 and stripped[level:level+1] == ' ':
                text = stripped[level:].strip()
                slug = re.sub(r'[^\w\s-]', '', text.lower()).replace(' ', '-')
                headings.append({'level': level, 'text': text, 'slug': slug})
    return headings


def generate_toc_html(headings, levels_to_include):
    """Generate HTML for table of contents.
    
    Args:
        headings: List of heading dictionaries
        levels_to_include: List of heading levels to include (e.g., [1, 2])
    """
    if not headings:
        return ''
    
    # Filter headings based on requested levels
    filtered = [h for h in headings if h['level'] in levels_to_include]
    if not filtered:
        return ''
    
    html = '<div class="table-of-contents">\n<h2>Contents</h2>\n<ul>\n'
    for heading in filtered:
        # Determine CSS class based on level (h2+ get indented)
        css_class = f'toc-h{heading["level"]}' if heading['level'] > 1 else ''
        class_attr = f' class="{css_class}"' if css_class else ''
        html += f'<li{class_attr}><a href="#{heading["slug"]}">{heading["text"]}</a></li>\n'
    html += '</ul>\n</div>\n'
    return html


def extract_frontmatter(content):
    """Extract YAML-style frontmatter from markdown content."""
    if not content.startswith('---'):
        return {}, content
    
    match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if not match:
        return {}, content
    
    fm_text, body = match.groups()
    fm = {}
    for line in fm_text.split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            fm[key.strip()] = val.strip().strip('"\'')
    return fm, body


def extract_title(path):
    """Extract title from frontmatter or first markdown heading."""
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()
    
    fm, body = extract_frontmatter(content)
    if 'title' in fm:
        return fm['title']
    
    for line in body.split('\n'):
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return None


def extract_text_content(path):
    """Extract plain text content from markdown file."""
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    fm, body = extract_frontmatter(content)
    # Convert markdown to HTML then strip tags for plain text
    html = markdown.markdown(body, extensions=['fenced_code', 'codehilite', 'tables', 'toc', 'attr_list', 'md_in_html'])
    # Simple HTML tag removal
    text = re.sub(r'<[^>]+>', '', html)
    # Clean up whitespace
    text = ' '.join(text.split())
    return text


def find_pages(src):
    pages = []
    for root, dirs, files in os.walk(src):
        for f in sorted(files):
            if f.lower().endswith('.md') and f.lower() != 'index.md':
                path = os.path.join(root, f)
                rel = os.path.relpath(path, src)
                # Normalize section directory to lowercase and replace spaces with hyphens
                parts = rel.split(os.sep)
                parts[0] = parts[0].lower().replace(' ', '-')
                # Normalize subsection names if they exist
                for i in range(1, len(parts)):
                    parts[i] = parts[i].lower().replace(' ', '-')
                normalized_rel = os.sep.join(parts)
                # Skip asset/static folders
                exclude_dirs = {'assets', 'static'}
                if any(p.lower() in exclude_dirs for p in parts):
                    continue
                url = os.path.splitext(normalized_rel)[0] + '.html'
                title = extract_title(path) or os.path.splitext(f)[0].replace('-', ' ').replace('_', ' ').title()
                section = rel.split(os.sep)[0] if os.sep in rel else ''
                subsection = rel.split(os.sep)[1] if len(rel.split(os.sep)) > 2 else None
                text = extract_text_content(path)
                # Get modification time
                mtime = os.path.getmtime(path)
                pages.append({'path': path, 'rel': normalized_rel, 'url': url.replace(os.sep, '/'), 'title': title, 'section': section, 'subsection': subsection, 'text': text, 'mtime': mtime})
    return pages


def build_search_index(pages):
    """Build a searchable index from all pages."""
    documents = []
    for i, page in enumerate(pages):
        doc = {
            'id': str(i),
            'title': page['title'],
            'url': '/' + page['url'],
            'content': page['text'][:500],  # Limit content preview
            'type': 'page'
        }
        documents.append(doc)
    return documents


def build(src='content', out='site', templates_dir='templates'):
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=select_autoescape(['html', 'xml']))
    page_tpl = env.get_template('page.html')

    pages = find_pages(src)

    nav = {}
    for p in pages:
        sec = p['section'] or ''
        nav.setdefault(sec, []).append(p)

    # Exclude asset/static sections from nav
    exclude_dirs = {'assets', 'static'}
    sections = sorted([s for s in nav.keys() if s and s.lower() not in exclude_dirs])
    
    # Parse section names and shortcuts
    section_info = {}
    for section in sections:
        # Extract display name by removing trailing -K format if present
        display_name = section.rsplit('-', 1)[0] if '-' in section and len(section.rsplit('-', 1)[1]) == 1 else section
        # Use first letter of display name as shortcut (in lowercase)
        shortcut = display_name[0].lower() if display_name else ''
        section_info[section] = {'display': display_name, 'shortcut': shortcut}

    # render pages
    for p in pages:
        with open(p['path'], 'r', encoding='utf-8') as fh:
            content = fh.read()
        fm, body = extract_frontmatter(content)
        
        # Generate table of contents if requested
        toc_html = ''
        contents_list = fm.get('contents-list', '')
        if contents_list:
            # Parse the levels to include (e.g., "h1" or "h1,h2" or "h1,h2,h3")
            levels_to_include = []
            for level_str in contents_list.lower().replace(' ', '').split(','):
                if level_str.startswith('h') and level_str[1:].isdigit():
                    level = int(level_str[1:])
                    if 1 <= level <= 6:
                        levels_to_include.append(level)
            
            if levels_to_include:
                headings = extract_headings(body)
                toc_html = generate_toc_html(headings, levels_to_include)
        
        # Use toc extension with custom permalink
        html = markdown.markdown(body, extensions=['fenced_code', 'codehilite', 'tables', 'toc', 'attr_list', 'md_in_html'], 
                                extension_configs={'toc': {'permalink': False}})
        
        # Add title as h1 at the top if it's from frontmatter
        if 'title' in fm:
            html = f'<h1>{fm["title"]}</h1>\n' + html
        
        # Insert TOC after title if requested
        if toc_html:
            html = html.split('\n', 1)
            if len(html) > 1:
                html = html[0] + '\n' + toc_html + html[1]
            else:
                html = html[0] + '\n' + toc_html
        
        out_path = os.path.join(out, p['url'])
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        # Format last updated date
        last_updated = datetime.fromtimestamp(p['mtime']).strftime('%B %d, %Y')
        page_data = {**p, 'last_updated': last_updated}
        rendered = page_tpl.render(title=p['title'], content=html, sections=sections, section_info=section_info, page=page_data)
        with open(out_path, 'w', encoding='utf-8') as fh:
            fh.write(rendered)

    # Group pages by subsection
    def group_by_subsection(pages_list):
        subsections = {}
        direct_pages = []
        for p in pages_list:
            if p.get('subsection'):
                subsections.setdefault(p['subsection'], []).append(p)
            else:
                direct_pages.append(p)
        return direct_pages, subsections

    # per-section index pages
    for section in sections:
        pages_in_sec = nav[section]
        
        # Normalize section directory name: lowercase and replace spaces with hyphens
        section_url = section.lower().replace(' ', '-')
        
        # Check for index.md in the section directory
        index_md_path = os.path.join(src, section, 'index.md')
        section_intro = ''
        if os.path.isfile(index_md_path):
            with open(index_md_path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            fm, body = extract_frontmatter(content)
            section_intro = markdown.markdown(body, extensions=['fenced_code', 'codehilite', 'tables', 'toc', 'attr_list', 'md_in_html'])
        
        direct_pages, subsections = group_by_subsection(pages_in_sec)
        
        # Build section index content with section title
        section_display = section_info[section]['display']
        index_content = f'<h1>{section_display.replace("_", " ")}</h1>\n' + section_intro

        # Combine subsections and direct pages in a single numbered list
        all_items = []
        
        # Add subsections first
        for subsec_name in sorted(subsections.keys()):
            subsec_url = subsec_name.lower().replace(' ', '-')
            all_items.append({
                'type': 'subsection',
                'name': subsec_name,
                'url': f'/{section_url}/{subsec_url}/',
                'title': subsec_name
            })
        
        # Add direct pages
        for p in direct_pages:
            all_items.append({
                'type': 'page',
                'url': f'/{p["url"]}',
                'title': p['title']
            })
        
        # Render as numbered list with subsection indicators
        if all_items:
            index_content += '\n<ul class="page-list">\n'
            for i, item in enumerate(all_items, 1):
                icon_html = '&nbsp;&nbsp;<span class="subsection-icon">📁</span>' if item['type'] == 'subsection' else ''
                index_content += f'  <li><a href="{item["url"]}" data-number="{i}"><span class="page-number">{i}</span>{item["title"].replace("_", " ")}{icon_html}</a></li>\n'
            index_content += '</ul>\n'
        
        index_path = os.path.join(out, section_url, 'index.html')
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        rendered = page_tpl.render(title=section, content=index_content, sections=sections, section_info=section_info, page={'url': f'{section_url}/index.html'})
        with open(index_path, 'w', encoding='utf-8') as fh:
            fh.write(rendered)
        
        # per-subsection index pages
        for subsec_name, subsec_pages in subsections.items():
            subsec_url = subsec_name.lower().replace(' ', '-')
            
            # Check for index.md in the subsection directory
            subsec_index_path = os.path.join(src, section, subsec_name, 'index.md')
            subsec_intro = ''
            if os.path.isfile(subsec_index_path):
                with open(subsec_index_path, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                fm, body = extract_frontmatter(content)
                subsec_intro = markdown.markdown(body, extensions=['fenced_code', 'codehilite', 'tables', 'toc', 'attr_list', 'md_in_html'])
            
            subsec_content = f'<h1>{subsec_name.replace("_", " ")}</h1>\n' + subsec_intro + '\n<ul class="page-list">\n'
            for i, p in enumerate(subsec_pages, 1):
                subsec_content += f'  <li><a href="/{p["url"]}" data-number="{i}"><span class="page-number">{i}</span>{p["title"]}</a></li>\n'
            subsec_content += '</ul>\n'
            
            subsec_out_path = os.path.join(out, section_url, subsec_url, 'index.html')
            os.makedirs(os.path.dirname(subsec_out_path), exist_ok=True)
            rendered = page_tpl.render(title=subsec_name, content=subsec_content, sections=sections, section_info=section_info, page={'url': f'{section_url}/{subsec_url}/index.html'})
            with open(subsec_out_path, 'w', encoding='utf-8') as fh:
                fh.write(rendered)

    # root index listing top 20 most recently edited pages
    # Check for root index.md
    root_intro = ''
    root_index_path = os.path.join(src, 'index.md')
    if os.path.isfile(root_index_path):
        with open(root_index_path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        fm, body = extract_frontmatter(content)
        root_intro = markdown.markdown(body, extensions=['fenced_code', 'codehilite', 'tables', 'toc', 'attr_list', 'md_in_html'])
    
    # Load tiles from tile*.md files in content root
    tiles = []
    import glob
    for tile_path in sorted(glob.glob(os.path.join(src, 'tile*.md'))):
        with open(tile_path, 'r', encoding='utf-8') as fh:
            tile_content = fh.read()
        tile_fm, tile_body = extract_frontmatter(tile_content)
        tile_html = markdown.markdown(tile_body, extensions=['fenced_code', 'codehilite', 'tables', 'toc', 'attr_list', 'md_in_html'])
        tiles.append({
            'title': tile_fm.get('title', ''),
            'link': tile_fm.get('link', '#'),
            'content': tile_html,
            'icon': tile_fm.get('icon', '📄')
        })
    
    # Build tiles HTML
    tiles_html = ''
    if tiles:
        tiles_html = '<div class="tiles-container">\n'
        for tile in tiles:
            tiles_html += f'''  <div class="tile">
    <a href="{tile['link']}.html">
      <h3 class="tile-title">{tile['title']}</h3>
      <div class="tile-content">{tile['content']}</div>
    </a>
  </div>
'''
        tiles_html += '</div>\n\n'
    
    # Sort pages by modification time (newest first), excluding asset/static pages
    recent_pages = [p for p in pages if p.get('section') and p.get('section').lower() not in {'assets', 'static'}]
    recent_pages = sorted(recent_pages, key=lambda p: p['mtime'], reverse=True)[:20]
    
    index_content = root_intro + tiles_html + '\n<h2>Recently Updated</h2>\n<ul class="page-list">\n'
    for i, p in enumerate(recent_pages, 1):
        index_content += f'  <li><a href="/{p["url"]}" data-number="{i}"><span class="page-number">{i}</span>{p["title"]}</a></li>\n'
    index_content += '</ul>\n'
    
    # Pass flag to indicate if we should hide the hero section
    page_data = {'url': 'index.html', 'hide_hero': bool(root_intro)}
    index_html = page_tpl.render(title='Home', content=index_content, sections=sections, section_info=section_info, page=page_data)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as fh:
        fh.write(index_html)

    # copy static
    static_src = os.path.join(os.path.dirname(templates_dir), 'static')
    static_src = os.path.normpath(static_src)
    if os.path.isdir(static_src):
        import shutil
        dst = os.path.join(out, 'static')
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(static_src, dst)

    # copy favicon
    import shutil
    # Get the directory where build.py is located, then go up one level to find MjN.png
    script_dir = os.path.dirname(os.path.abspath(__file__))
    favicon_src = os.path.join(os.path.dirname(script_dir), 'MjN.png')
    if os.path.isfile(favicon_src):
        favicon_dst = os.path.join(out, 'favicon.png')
        shutil.copy2(favicon_src, favicon_dst)
        print(f'Copied favicon: {favicon_src} -> {favicon_dst}')
    else:
        print(f'Warning: Favicon not found at {favicon_src}')

    # Copy assets and images from content directory to their respective locations
    import shutil
    for root, dirs, files in os.walk(src):
        # Look for assets or images directories
        for folder_name in ['assets', 'images']:
            if folder_name in dirs:
                folder_src = os.path.join(root, folder_name)
                # Calculate relative path from src
                rel_path = os.path.relpath(root, src)
                # Normalize the path (lowercase, replace spaces with hyphens)
                if rel_path != '.':
                    parts = rel_path.split(os.sep)
                    normalized_parts = [p.lower().replace(' ', '-') for p in parts]
                    rel_path_normalized = os.sep.join(normalized_parts)
                else:
                    rel_path_normalized = ''
                
                # Create destination path maintaining folder structure
                if rel_path_normalized:
                    folder_dst = os.path.join(out, rel_path_normalized, folder_name)
                else:
                    folder_dst = os.path.join(out, folder_name)
                
                # Copy the directory, ignoring permission errors
                try:
                    if os.path.exists(folder_dst):
                        shutil.rmtree(folder_dst)
                    shutil.copytree(folder_src, folder_dst, ignore_dangling_symlinks=True)
                    print(f'Copied {folder_name}: {folder_src} -> {folder_dst}')
                except (PermissionError, OSError) as e:
                    print(f'Warning: Could not copy some files from {folder_src}: {e}')
                    # Try to copy individual files that are accessible
                    os.makedirs(folder_dst, exist_ok=True)
                    for item in os.listdir(folder_src):
                        src_item = os.path.join(folder_src, item)
                        dst_item = os.path.join(folder_dst, item)
                        try:
                            if os.path.isfile(src_item):
                                shutil.copy2(src_item, dst_item)
                        except (PermissionError, OSError):
                            pass

    # Build and save search index
    search_index = build_search_index(pages)
    search_index_path = os.path.join(out, 'static', 'search-index.json')
    os.makedirs(os.path.dirname(search_index_path), exist_ok=True)
    with open(search_index_path, 'w', encoding='utf-8') as fh:
        json.dump(search_index, fh, indent=2)

    print('Site built to', out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build a simple static site from Markdown')
    parser.add_argument('--src', '-s', default='content', help='Source content directory')
    parser.add_argument('--out', '-o', default='site', help='Output directory')
    parser.add_argument('--templates', '-t', default='templates', help='Templates directory')
    args = parser.parse_args()
    
    # Clean output directory before building
    import shutil
    if os.path.isdir(args.out):
        shutil.rmtree(args.out)
    
    build(args.src, args.out, args.templates)
