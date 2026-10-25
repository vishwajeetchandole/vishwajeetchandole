import json
import os
import re
import urllib.request

USER = os.environ.get("GH_USER") or os.environ["GITHUB_REPOSITORY_OWNER"]
TOKEN = os.environ.get("GITHUB_TOKEN")
README = "README.md"
START = "<!--REPOS:START-->"
END = "<!--REPOS:END-->"

# Optional: comma-separated repo names to hide, e.g. EXCLUDE_REPOS="test-repo,old-project"
EXCLUDE = {
    name.strip().lower()
    for name in os.environ.get("EXCLUDE_REPOS", "").split(",")
    if name.strip()
}


def fetch_repos():
    repos = []
    page = 1
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "readme-updater",
    }
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN

    while True:
        url = (
            "https://api.github.com/users/"
            + USER
            + "/repos?per_page=100&type=owner&page="
            + str(page)
        )
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            batch = json.load(resp)
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def clean(text):
    if not text:
        return "—"
    return text.replace("|", "\\|").replace("\n", " ").strip()


def build_table(repos):
    rows = [
        r
        for r in repos
        if not r["fork"]
        and not r["archived"]
        and r["name"].lower() != USER.lower()
        and r["name"].lower() not in EXCLUDE
    ]
    rows.sort(key=lambda r: r["pushed_at"] or "", reverse=True)

    lines = [
        "*" + str(len(rows)) + " public repositories, updated automatically.*",
        "",
        "| Repository | Description | Language | ⭐ | Last push |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            "| [{name}]({url}) | {desc} | {lang} | {stars} | {date} |".format(
                name=r["name"],
                url=r["html_url"],
                desc=clean(r["description"]),
                lang=r["language"] or "—",
                stars=r["stargazers_count"],
                date=(r["pushed_at"] or "")[:10],
            )
        )
    return "\n".join(lines)


def main():
    table = build_table(fetch_repos())
    block = START + "\n" + table + "\n" + END

    with open(README, encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)

    if pattern.search(content):
        new_content = pattern.sub(lambda m: block, content)
    else:
        # Markers missing: add the section at the end of the README
        new_content = content.rstrip() + "\n\n## 📚 All Repositories\n\n" + block + "\n"

    if new_content != content:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("README updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
