import requests
import gzip
import re
import html


def build_ncbi_download_page(gse):
    return f"https://www.ncbi.nlm.nih.gov/geo/download/?acc={gse}"


def build_geo_supplement_url(gse):
    prefix = gse[:-3] + "nnn"
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{prefix}/{gse}/suppl/"


def find_ncbi_raw_counts(url):
    r = requests.get(url, timeout=60)
    r.raise_for_status()

    pattern = r'href="([^"]*raw_counts[^"]*\.tsv\.gz)"'
    matches = re.findall(pattern, r.text, flags=re.IGNORECASE)

    for m in matches:
        clean = html.unescape(m)
        if not clean.startswith("/"):
            clean = "/" + clean
        return clean

    return None


def list_files(url):
    r = requests.get(url, timeout=60)
    r.raise_for_status()

    files = []
    for line in r.text.splitlines():
        if "href=" in line:
            part = line.split("href=")[1].split(">")[0]
            fname = part.replace('"', "").strip()
            if not fname.startswith("?") and fname != "../":
                files.append(fname)
    return files

def download_file_bytes(url):
    """
    Downloads a file into memory (no disk write)
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()
    return response.content

def unzip_gz_bytes(file_bytes):
    """
    Decompress gzip file fully in memory
    """
    return gzip.decompress(file_bytes)

def download_raw_counts_for_gse(gse):
    """
    Returns:
        [
            {
                "filename": str,
                "data": bytes
            }
        ]
    """

    downloaded = []

    # --------------------------------------------------
    # 1. Try NCBI-generated raw counts
    # --------------------------------------------------
    try:

        ncbi_page = build_ncbi_download_page(gse)
        raw_counts_link = find_ncbi_raw_counts(ncbi_page)

        if raw_counts_link:

            download_url = "https://www.ncbi.nlm.nih.gov" + raw_counts_link

            fname = raw_counts_link.split("file=")[-1]

            print(f"[{gse}] Found NCBI raw counts: {fname}")

            content = download_file_bytes(download_url)

            if fname.endswith(".gz"):

                downloaded.append(
                    {
                        "filename": fname.replace(".gz", ""),
                        "data": unzip_gz_bytes(content)
                    }
                )

            else:

                downloaded.append(
                    {
                        "filename": fname,
                        "data": content
                    }
                )

            return downloaded

        print(f"[{gse}] No NCBI raw counts found, trying supplements.")

    except Exception as e:

        print(f"[{gse}] NCBI raw counts check failed: {e}")
        print(f"[{gse}] Falling back to supplements.")

    # --------------------------------------------------
    # 2. Supplement files
    # --------------------------------------------------
    try:

        url = build_geo_supplement_url(gse)

        files = list_files(url)

        target_files = [
            f
            for f in files
            if any(
                k in f.lower()
                for k in [
                    "count",
                    "counts",
                    "matrix",
                    "readcount",
                    "gene"
                ]
            )
        ]

        if not target_files:
            target_files = files

        for file in target_files:

            print(f"[{gse}] Downloading supplement: {file}")

            content = download_file_bytes(url + file)

            if file.endswith(".gz"):

                downloaded.append(
                    {
                        "filename": file.replace(".gz", ""),
                        "data": unzip_gz_bytes(content)
                    }
                )

            else:

                downloaded.append(
                    {
                        "filename": file,
                        "data": content
                    }
                )

    except Exception as e:

        print(f"[{gse}] Supplement download failed: {e}")

    return downloaded