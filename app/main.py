import os
import re
import fitz 
import json

TITLE_EXCEPTIONS = {
    "a", "an", "the", "and", "but", "or", "nor", "so", "yet",
    "for", "on", "in", "at", "to", "by", "of", "up", "with", "as", "from"
}

def is_bold_italic(font_name):
    font = font_name.lower()
    return any(kw in font for kw in ["bold", "italic", "oblique", "black", "medium", "demi"])

def is_numbered_heading_valid(text):
    match = re.match(r"^\d+(\.\d+)*\s*(.*)", text)
    if not match:
        return False
    heading_text = match.group(2)
    words = re.findall(r"\b\w+\b", heading_text)
    significant = [w for w in words if w.lower() not in TITLE_EXCEPTIONS]
    return sum(1 for w in significant if w[0].isupper()) == len(significant)

def is_valid_heading_block(text, lines, flags, avg_size, seen_texts, footer_texts):
    norm_text = re.sub(r"\s+", " ", text.lower())
    if not text or norm_text in footer_texts or norm_text in seen_texts:
        return False
    if len(lines) > 3 or len(text) > 300:
        return False
    if not re.search(r"[a-zA-Z]", text):
        return False
    if len(lines) >= 2 and all(len(t) <= 15 for _, t in lines):
        return False
    if len(lines) >= 2 and not all(re.search(r"[a-zA-Z]", t) for _, t in lines):
        return False
    return all(flags) or (is_numbered_heading_valid(text) and len(lines) <= 2)

def extract_blocks_for_json(pdf_path):
    doc = fitz.open(pdf_path)
    extracted_data = {
        "title": "",
        "outline": []
    }
    seen_texts = set()
    global_max_title_size = -1 
    
    potential_headings = []
    first_page_candidates_for_title = [] 
    normalized_title_block_texts = set() 

    for page_num, page in enumerate(doc, start=1):
        line_counter = 1
        blocks = page.get_text("dict")["blocks"]

        
        footer_texts = set()
        for b in reversed(blocks):
            if b["type"] != 0 or "lines" not in b:
                continue
            text = ""
            all_bold_italic = True
            for line in b["lines"]:
                for span in line["spans"]:
                    text += span["text"]
                    if not is_bold_italic(span["font"]):
                        all_bold_italic = False
            norm_text = re.sub(r"\s+", " ", text.strip().lower())
            if norm_text and all_bold_italic:
                footer_texts.add(norm_text)
            else:
                break

        for b in blocks:
            if b["type"] != 0 or "lines" not in b:
                continue

            font_sub_blocks = []
            current_font_key = None
            sub_lines, sub_fonts, sub_sizes, sub_flags = [], set(), [], []

            def flush_sub_block():
                nonlocal sub_lines, sub_fonts, sub_sizes, sub_flags
                if sub_lines:
                    font_sub_blocks.append((list(sub_lines), list(sub_fonts), list(sub_sizes), list(sub_flags)))
                    sub_lines.clear()
                    sub_fonts.clear()
                    sub_sizes.clear()
                    sub_flags.clear()

            for line in b["lines"]:
                sizes_in_line = set(round(span["size"], 1) for span in line["spans"])
                size_key = tuple(sorted(sizes_in_line))

                if current_font_key and size_key != current_font_key:
                    flush_sub_block()

                current_font_key = size_key

                line_text = ""
                styles = set()
                bold_flag = True

                for span in line["spans"]:
                    line_text += span["text"]
                    sub_fonts.add(span["font"])
                    sub_sizes.append(round(span["size"], 1))
                    style = span["font"].lower()
                    is_bold = any(kw in style for kw in ["bold", "black", "medium", "demi"])
                    is_italic = any(kw in style for kw in ["italic", "oblique"])
                    styles.add(("B" if is_bold else "") + ("I" if is_italic else ""))
                    if not is_bold and not is_italic:
                        bold_flag = False

                if len(styles) > 1:
                    bold_flag = False

                sub_lines.append((line_counter, line_text.strip()))
                sub_flags.append(bold_flag)
                line_counter += 1

            flush_sub_block()

            
            for lines, fonts, sizes, flags in font_sub_blocks:
                block_text = "\n".join([text for _, text in lines]).strip()
                avg_size = sum(sizes) / len(sizes) if sizes else 0

                
                if avg_size > global_max_title_size:
                    global_max_title_size = avg_size

               
                
                if is_valid_heading_block(block_text, lines, flags, avg_size, seen_texts, footer_texts):
                    potential_headings.append({
                        "text": block_text,
                        "page": page_num,
                        "font_size": avg_size,
                        "is_numbered": is_numbered_heading_valid(block_text)
                    })
                    norm_text_for_seen = re.sub(r"\s+", " ", block_text.lower())
                    seen_texts.add(norm_text_for_seen)

                
                if page_num == 1:
                    first_page_candidates_for_title.append({
                        "text": block_text,
                        "font_size": avg_size,
                        "lines": lines,
                        "flags": flags,
                        "is_valid_heading": is_valid_heading_block(block_text, lines, flags, avg_size, seen_texts, footer_texts)
                    })
    
    
    merged_title_parts = []
    
    
    FONT_SIZE_TOLERANCE = 0.5 

    current_title_font_size = -1
    for candidate in first_page_candidates_for_title:
        is_candidate_valid_for_title_part = (
            bool(candidate["text"].strip()) and 
            re.search(r"[a-zA-Z]", candidate["text"]) and 
            len(candidate["text"]) <= 300 
        )


        if not merged_title_parts and \
           abs(candidate["font_size"] - global_max_title_size) < FONT_SIZE_TOLERANCE and \
           is_candidate_valid_for_title_part:
            merged_title_parts.append(candidate["text"])
            current_title_font_size = candidate["font_size"]

        elif merged_title_parts and \
             abs(candidate["font_size"] - current_title_font_size) < FONT_SIZE_TOLERANCE and \
             is_candidate_valid_for_title_part:
            merged_title_parts.append(candidate["text"])

        elif merged_title_parts: 
            break 
    

    if not merged_title_parts:
        best_fallback_title = ""
        for heading in potential_headings:
            if heading["font_size"] == global_max_title_size:
                best_fallback_title = heading["text"]
                break 
        extracted_data["title"] = re.sub(r'\s+', ' ', best_fallback_title).strip()
        if extracted_data["title"]: 
             normalized_title_block_texts.add(extracted_data["title"].lower())
    else:
        
        for part in merged_title_parts:
            normalized_title_block_texts.add(re.sub(r'\s+', ' ', part).strip().lower())
        extracted_data["title"] = re.sub(r'\s+', ' ', "\n".join(merged_title_parts)).strip()
    
    
    unique_font_sizes = sorted(list(set(h["font_size"] for h in potential_headings)), reverse=True)
    
   
    font_size_to_level = {}
    if len(unique_font_sizes) >= 1:
        font_size_to_level[unique_font_sizes[0]] = "H1"
    if len(unique_font_sizes) >= 2:
        font_size_to_level[unique_font_sizes[1]] = "H2"
    if len(unique_font_sizes) >= 3:
        font_size_to_level[unique_font_sizes[2]] = "H3"

    for heading in potential_headings:

        normalized_heading_text = re.sub(r'\s+', ' ', heading["text"]).strip().lower()
        if normalized_heading_text in normalized_title_block_texts or \
           normalized_heading_text == extracted_data["title"].lower():
            continue

        level = None

        if heading["is_numbered"]:
            match = re.match(r"^\d+(\.\d+)*", heading["text"])
            if match:
                numerical_prefix = match.group(0)
                dots = numerical_prefix.count('.')
                if dots == 0:
                    level = "H1"
                elif dots == 1:
                    level = "H2"
                elif dots >= 2:
                    level = "H3"

        if level is None:
            level = font_size_to_level.get(heading["font_size"], "H3") 


        clean_text = heading["text"]
        if heading["is_numbered"]:
            clean_text = re.sub(r"^\d+(\.\d+)*\s*", "", heading["text"]).strip()


        if level in ["H1", "H2", "H3"]:
            extracted_data["outline"].append({
                "level": level,
                "text": clean_text,
                "page": heading["page"]
            })

    level_order = {"H1": 1, "H2": 2, "H3": 3}
    extracted_data["outline"].sort(key=lambda x: (x["page"], level_order.get(x["level"], 4)))

    return extracted_data

def process_pdf_to_json(pdf_path, json_output_path):
    """
    Processes a PDF to extract title and outline, then saves it as a JSON file.
    """
    outline_data = extract_blocks_for_json(pdf_path)
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(outline_data, f, indent=2, ensure_ascii=False)
    print(f"📝 Saved: {json_output_path}")

if __name__ == "__main__":
    input_dir = "input"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]
    if not pdf_files:
        print("❌ No PDF files found in input folder.")
    else:
        for filename in pdf_files:
            pdf_path = os.path.join(input_dir, filename)
            base_name = os.path.splitext(filename)[0]
            json_out = os.path.join(output_dir, f"{base_name}.json")

            try:
                process_pdf_to_json(pdf_path, json_out)
            except Exception as e:
                print(f"⚠️ Error processing {filename}: {e}")