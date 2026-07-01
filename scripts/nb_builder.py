import nbformat as nbf
from nbclient import NotebookClient

def build_and_run(cells, out_path, kernel_name="python3"):
    """cells: list of (type, source) tuples where type is 'markdown' or 'code'"""
    nb = nbf.v4.new_notebook()
    nb['cells'] = []
    for ctype, src in cells:
        if ctype == "markdown":
            nb['cells'].append(nbf.v4.new_markdown_cell(src))
        else:
            nb['cells'].append(nbf.v4.new_code_cell(src))
    client = NotebookClient(nb, timeout=600, kernel_name=kernel_name,
                             resources={"metadata": {"path": "notebooks"}})
    client.execute()
    with open(out_path, "w") as f:
        nbf.write(nb, f)
    print(f"Executed and saved: {out_path}")
