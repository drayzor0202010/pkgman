#!/usr/bin/env python3
from pathlib import Path
import json, tarfile, tempfile, shutil, sys, hashlib, urllib.parse, os

try:
    import requests
except Exception:
    requests = None

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
MIRRORS_PROJECT = PROJECT_ROOT / "mirrors" / "config.txt"
MIRRORS_USER = Path.home() / ".config" / "mirrors" / "config.txt"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(BASE_DIR, "store")
STAGING = os.path.join(BASE_DIR, "staging")
PACKAGES = os.path.join(BASE_DIR, "packages")
DATABASE = os.path.join(BASE_DIR, "database")

for d in (STORE_DIR, STAGING_DIR, PACKAGES_DIR, DB_FILE.parent):
    d.mkdir(parents=True, exist_ok=True)

def _load_json(p: Path):
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))

def _save_json(p: Path, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def _sha256(path: Path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_mirrors():
    for candidate in (MIRRORS_PROJECT, MIRRORS_USER):
        if candidate.exists():
            lines = [l.strip() for l in candidate.read_text(encoding="utf-8").splitlines()]
            return [l for l in lines if l and not l.startswith("#")]
    return []

def download_package(pkgname_version: str) -> Path:
    filename = f"{pkgname_version}.tar.gz"
    dest = STORE_DIR / filename
    if dest.exists():
        return dest
    mirrors = load_mirrors()
    if not mirrors:
        raise FileNotFoundError("No mirrors configured")
    last_exc = None
    for base in mirrors:
        base = base.rstrip("/")
        if base.startswith("file://"):
            local = Path(urllib.parse.urlparse(base).path) / filename
            if local.exists():
                shutil.copy2(str(local), str(dest))
                return dest
            last_exc = FileNotFoundError(f"{local} not found")
            continue
        else:
            if requests is None:
                raise RuntimeError("requests not installed")
            url = base + "/" + filename
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    with open(dest, "wb") as f:
                        f.write(r.content)
                    return dest
                last_exc = RuntimeError(f"HTTP {r.status_code}")
            except Exception as e:
                last_exc = e
                continue
    raise last_exc

def extract_to_temp(archive_path: Path):
    tmpdir = Path(tempfile.mkdtemp(prefix="pkgman-"))

    # extrai o pacote
    with tarfile.open(archive_path, "r:gz") as tf:
        tf.extractall(tmpdir)

    # achar a pasta do pacote (ex: Gudan-1.0)
    items = list(tmpdir.iterdir())
    if not items:
        raise FileNotFoundError("empty package")

    # deve existir uma pasta única
    root = items[0]

    manifest = root / "manifest.json"
    if not manifest.exists():
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise FileNotFoundError("manifest.json missing")

    meta = json.loads(manifest.read_text(encoding="utf-8"))
    return root, meta

def load_db():
    return _load_json(DB_FILE)

def save_db(db):
    _save_json(DB_FILE, db)

def install(pkgname_version: str):
    archive = download_package(pkgname_version)
    tmpdir, meta = extract_to_temp(archive)
    name = meta.get("name")
    version = meta.get("version")
    files = meta.get("files", [])

    if not name or not version:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise ValueError("manifest missing name or version")

    installed_paths = []
    backups = []

    try:
        for p in files:
            rel = Path(p)
            if rel.parts and rel.parts[0] == "files":
                rel = Path(*rel.parts[1:])
            dst = PACKAGES_DIR / rel
            dst.parent.mkdir(parents=True, exist_ok=True)

        for p in files:
            src = tmpdir / p
            if not src.exists():
                raise FileNotFoundError(f"missing file: {p}")
            rel = Path(p)
            if rel.parts and rel.parts[0] == "files":
                rel = Path(*rel.parts[1:])
            dst = PACKAGES_DIR / rel

            if dst.exists():
                bk = dst.with_suffix(dst.suffix + ".pkgman.bak")
                i = 0
                while bk.exists():
                    i += 1
                    bk = dst.with_suffix(dst.suffix + f".pkgman.bak{i}")
                dst.rename(bk)
                backups.append((bk, dst))

            shutil.copy2(str(src), str(dst))
            installed_paths.append(str(dst))

        db = load_db()
        db[name] = {"version": version, "archive": str(archive), "files": installed_paths}
        save_db(db)

    except Exception as e:
        for p in installed_paths:
            try:
                if Path(p).exists():
                    Path(p).unlink()
            except:
                pass
        for bk, orig in backups:
            try:
                if orig.exists():
                    orig.unlink()
                bk.rename(orig)
            except:
                pass
        raise

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def remove(name: str):
    db = load_db()
    if name not in db:
        print("not installed")
        return

    files = db[name].get("files", [])
    for f in files:
        p = Path(f)
        try:
            if p.exists():
                p.unlink()
            parent = p.parent
            while parent != PACKAGES_DIR and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
            for bk in PACKAGES_DIR.rglob(p.name + ".pkgman.bak*"):
                try:
                    bk.unlink()
                except:
                    pass
        except:
            pass

    del db[name]
    save_db(db)

def query(name: str):
    db = load_db()
    print(db.get(name, "not installed"))

def list_installed():
    db = load_db()
    if not db:
        print("(no packages installed)")
        return
    for k, v in db.items():
        print(k, v.get("version", "?"))

def verify(pkgname_version: str):
    archive = STORE_DIR / f"{pkgname_version}.tar.gz"
    if not archive.exists():
        raise FileNotFoundError("archive not found")
    tmpdir, meta = extract_to_temp(archive)
    declared = meta.get("sha256")
    ok = True
    if declared:
        actual = _sha256(archive)
        ok = (declared == actual)
        print("declared:", declared)
        print("actual:  ", actual)
        print("match:", ok)
    else:
        print("no sha256 declared")
    shutil.rmtree(tmpdir, ignore_errors=True)
    return ok

def usage():
    print("usage: install/remove/query/list/verify")

def main(argv):
    if not argv:
        usage()
        return
    cmd = argv[0]
    try:
        if cmd == "install":
            install(argv[1])
        elif cmd == "remove":
            remove(argv[1])
        elif cmd == "query":
            query(argv[1])
        elif cmd == "list":
            list_installed()
        elif cmd == "verify":
            verify(argv[1])
        else:
            print("unknown command")
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main(sys.argv[1:])