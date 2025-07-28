# 🧠 Adobe India Hackathon 2025 – Round 1A: Structured Outline Extraction

## 🚀 Problem Statement
**Challenge 1A** required us to extract a structured document outline from unstructured PDF files. This includes:

- Extracting the **document title** from the largest font block.
- Identifying **section headings** using a combination of font features and layout rules.
- Categorizing headings into hierarchical levels (**H1**, **H2**, **H3**) using font size or numbered patterns.
- Saving the extracted data in a clean, structured **JSON** format.

---

## 📁 Directory Structure

```
├── app/
│   ├── main.py                   # Main script to extract title + outline from all PDFs
│   ├── requirements.txt          # Dependencies (PyMuPDF, etc.)
│   ├── Dockerfile                # Docker setup for Round 1A
│   ├── input/                    # Place PDF files here
│   └── output/                   # JSON output files generated
```

---

## 🧠 Key Features
- Extracts clean document **titles** (even if spread across multiple lines).
- Detects headings based on:
  - Font size
  - Bold/Italic style
  - Numbered pattern (e.g., 1.2, 2.1.3)
- Ensures **no duplicate** or **footer** content is included.
- Tags headings with hierarchical level: `H1`, `H2`, `H3`.

---

## 📦 Dependencies

Install required libraries:
```bash
pip install -r requirements.txt
```

Libraries used:
- `PyMuPDF (fitz)` – for reading PDFs and fonts
- `re`, `os`, `json` – for processing and formatting

---

## 🛠️ How to Run Locally

### 🔧 Step 1: Place PDFs

Put your PDF files inside the `input/` folder.

### ▶️ Step 2: Run the script

```bash
python main.py
```

This will create a `.json` output for each PDF inside the `output/` folder.

---

## 🐳 Run with Docker

### Step 1: Build the Docker image
```bash
docker build -t round1a-extractor .
```

### Step 2: Run the container
```bash
docker run --rm -v ${PWD}/input:/app/input -v ${PWD}/output:/app/output round1a-extractor
```

✅ Your output will be saved in the `output/` folder.

---

## 📤 Download / Submission Package

You can download this submission as a zip:

📦 [Download Round 1A Submission](https://github.com/Anishhhh12/strugglers1-a)  
_(Replace with your actual GitHub zip link or release download)_

---


---

## 👤 Author
  **Strugglers**  

Feel free to reach out for any doubts or improvements!

---

## 📌 Notes

- Round 1A is **offline-compatible**.
- No AI models are used for classification; rules are applied based on font metrics.
- Docker makes the setup universal across systems.

---
