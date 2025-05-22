
# 🛠 Markdown to HTML Converter

A simple Python tool to convert `.md` (Markdown) files into readable `.html` documents.

Features:

- ✅ Full Markdown rendering (headers, tables, lists, etc.)
- ✅ Mermaid diagram support
- ✅ Timestamp added to every generated HTML
- ✅ GitHub integration using Personal Access Token (PAT)
- ✅ Local or remote `.md` file support
- ✅ Automatic index page creation
- ✅ Custom HTML via Jinja2 templates

---

## 🚀 Getting Started

### 1. Clone the repository and set up a virtual environment

```bash
git clone git@github.com:TBoneMendez/cool-data-tools.git
cd cool-data-tools
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 📂 Folder Structure

```text
markdown-to-html/
├── input/
│   └── markdowns/           # Optional: place local .md files here
├── output/
│   ├── markdowns/           # GitHub-downloaded .md files will be stored here
│   └── html/                # Final HTML output files
├── html_gens/
│   ├── template.html        # Jinja template for HTML pages
│   └── index_template.html  # Jinja template for index.html
├── markdown_to_html.py      # Main script
```

> 📝 The `input/` and `output/` folders are ignored by Git by default.

---

## 🧠 Usage Guide

This tool can either convert local `.md` files, or fetch them directly from a GitHub repository using the GitHub API.

---

### 🔁 Option A: Use local markdown files

1. Place your `.md` files in `input/markdowns/`
2. Run:

```bash
python markdown_to_html.py
```

3. The rendered `.html` files will appear in `output/html/`, and an index file will be generated.

---

### 🌐 Option B: Fetch `.md` files from a GitHub repo

#### 1. Create a GitHub Personal Access Token (PAT)

- Go to [https://github.com/settings/tokens](https://github.com/settings/tokens)
- Generate a **Classic token**
- Select:
  - ✅ `repo` scope
  - ✅ `Contents` permission (read-only)
- Copy the token

#### 2. Create a `.env` file

In the root of the project, create a file called `.env` and add:

```env
GITHUB_TOKEN=ghp_YourTokenHere
```

(Do **not** commit this file – it should be listed in `.gitignore`.)

#### 3. Update the GitHub URL in the script

In `markdown_to_html.py`, find the line:

```python
github_url = "https://github.com/YourUser/YourRepo/tree/main/path/to/markdowns"
```

Replace it with the path to the `.md` files in your own GitHub repo.

#### 4. Run the script

```bash
python markdown_to_html.py
```

If your token and repo URL are valid, the script will:
- Download `.md` files from the repo
- Save them to `output/markdowns`
- Convert them to HTML and save in `output/html`
- Generate an `index.html` to link them

---

## 🧪 Token Verification

You can check whether your token is being picked up with this test:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GITHUB_TOKEN'))"
```

---

## 🛡 Offline Mode

Once your dependencies and token are set:
- The script can run fully offline using local files
- No external API calls are required unless `github_url` is defined
- Your PAT is stored locally in `.env` and never committed

---

Happy converting! 💫
