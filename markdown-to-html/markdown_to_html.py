
import os
import requests
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

print("🔍 GITHUB_TOKEN loaded:", os.getenv("GITHUB_TOKEN"))

# Set github_url if you want to fetch markdowns from GitHub, or leave it empty to use local files in "input/markdowns/"
github_url = "https://github.com/TBoneMendez/cool-data-tools/tree/main/transcirber-app"
# github_url = ""  # Uncomment to use local mode

def fetch_markdown_files_from_github(repo_url, output_md_dir):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ Missing GITHUB_TOKEN environment variable.")
        return []

    if "tree" not in repo_url:
        print("❌ Invalid GitHub URL (must contain 'tree').")
        return []

    try:
        parts = repo_url.split("/")
        owner = parts[3]
        repo = parts[4]
        branch = parts[6]
        path = "/".join(parts[7:])

        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get(api_url, headers=headers)

        if response.status_code != 200:
            print(f"❌ Failed to fetch from GitHub: {response.status_code} {response.reason}")
            return []

        os.makedirs(output_md_dir, exist_ok=True)
        files_downloaded = []

        for file in response.json():
            if file["name"].endswith(".md"):
                file_content = requests.get(file["download_url"], headers=headers).text
                local_path = os.path.join(output_md_dir, file["name"])
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
                files_downloaded.append(local_path)
                print(f"⬇️  Downloaded: {file['name']}")

        return files_downloaded

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def convert_md_to_html(input_dir, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    files = [f for f in os.listdir(input_dir) if f.endswith(".md")]
    if not files:
        print("⚠️  Input folder is empty.")
        return

    for filename in files:
        with open(os.path.join(input_dir, filename), "r", encoding="utf-8") as f:
            md_content = f.read().replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

        title = filename.replace(".md", "").replace("_", " ").title()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        env = Environment(loader=FileSystemLoader("./html_gens/"))
        template = env.get_template("template.html")
        html_content = template.render(
            title=title,
            markdown=md_content,
            timestamp=timestamp
        )

        output_path = os.path.join(output_folder, filename.replace(".md", ".html"))
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ Converted: {filename} → {output_path}")


def generate_index_html(output_folder):
    env = Environment(loader=FileSystemLoader("./html_gens/"))
    template = env.get_template("index_template.html")

    html_files = sorted(
        f for f in os.listdir(output_folder)
        if f.endswith(".html") and f != "index.html"
    )

    html_output = template.render(files=html_files)
    index_path = os.path.join(output_folder, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"📄 Created index file: {index_path}")


if __name__ == "__main__":
    input_dir = "input/markdowns"
    os.makedirs(input_dir, exist_ok=True)
    output_md_dir = "output/markdowns"
    output_html_dir = "output/html"
    source_dir = ""

    if github_url:
        print(f"🌐 Fetching markdown-files from: {github_url}")
        downloaded = fetch_markdown_files_from_github(github_url, output_md_dir)
        source_dir = output_md_dir if downloaded else ""
        if not downloaded:
            print("⚠️  No markdown files found via GitHub URL.")
    else:
        print("📁 Using local files from input/markdowns/")
        source_dir = input_dir

    if source_dir:
        convert_md_to_html(source_dir, output_html_dir)
        generate_index_html(output_html_dir)
    else:
        print("❌ No markdown files found to convert.")
