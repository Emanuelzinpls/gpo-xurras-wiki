import hashlib
import io
import json
import locale
import os
import queue
import sys
import tempfile
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, ttk
from urllib.parse import quote

import requests
from PIL import Image, ImageTk

APP_NAME = "Xurras x GPO"
APP_VERSION = "1.0.0"
CONFIG_URL = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/remote_config.json"
DEFAULT_TIMEOUT = 15
CACHE_DIR = Path(tempfile.gettempdir()) / "xurras_gpo_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

LANGUAGES = {
    "pt-BR": {"flag": "🇧🇷", "name": "Português (Brasil)"},
    "en-US": {"flag": "🇺🇸", "name": "English (US)"},
    "es-ES": {"flag": "🇪🇸", "name": "Español"},
    "fr-FR": {"flag": "🇫🇷", "name": "Français"},
    "de-DE": {"flag": "🇩🇪", "name": "Deutsch"},
    "it-IT": {"flag": "🇮🇹", "name": "Italiano"},
    "ja-JP": {"flag": "🇯🇵", "name": "日本語"},
    "ko-KR": {"flag": "🇰🇷", "name": "한국어"},
}

I18N = {
    "pt-BR": {
        "choose_language": "Escolha seu idioma",
        "loading": "Carregando launcher...",
        "checking": "Checando internet, status e atualizações...",
        "maintenance": "App em manutenção. Tente novamente mais tarde.",
        "update_required": "Atualização obrigatória encontrada. Atualizando...",
        "no_internet": "Sem internet/Wi-Fi. O app exige conexão para abrir.",
        "support": "Suporte no Discord",
        "search_placeholder": "Pesquisar item, boss, arma, navio...",
        "search": "Buscar",
        "tabs": ["Bosses", "Espadas/Armas", "Navios", "Gamepasses", "Merchants", "Trade Meta"],
        "about": "Sobre",
        "source": "Fonte",
    },
    "en-US": {
        "choose_language": "Choose your language",
        "loading": "Loading launcher...",
        "checking": "Checking internet, status and updates...",
        "maintenance": "App is under maintenance. Please try again later.",
        "update_required": "Mandatory update found. Updating...",
        "no_internet": "No internet/Wi-Fi. The app requires connection to open.",
        "support": "Discord Support",
        "search_placeholder": "Search boss, weapon, ship, item...",
        "search": "Search",
        "tabs": ["Bosses", "Swords/Weapons", "Ships", "Gamepasses", "Merchants", "Trade Meta"],
        "about": "About",
        "source": "Source",
    },
}

for code in LANGUAGES:
    if code not in I18N:
        I18N[code] = I18N["en-US"]


@dataclass
class RemoteConfig:
    app_online: bool
    min_version: str
    latest_version: str
    update_url: str
    update_sha256: str
    background_image_url: str
    loading_gif_url: str
    music_url: str


class NetworkError(RuntimeError):
    pass


class SecurityError(RuntimeError):
    pass


class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1280x760")
        self.configure(bg="#0b1220")
        self.minsize(1100, 700)

        self.lang = self._detect_language()
        self.text = I18N[self.lang]
        self.config_data = None
        self.bg_label = tk.Label(self, bg="#0b1220")
        self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.overlay = tk.Frame(self, bg="#000000")
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.content = tk.Frame(self.overlay, bg="#101827", padx=16, pady=16)
        self.content.place(relx=0.5, rely=0.5, anchor="center", width=900, height=580)

        self.status_var = tk.StringVar(value="")
        self.progress_var = tk.DoubleVar(value=0)

        self._build_language_screen()

    def _detect_language(self):
        loc = locale.getdefaultlocale()[0] or "en-US"
        return loc if loc in LANGUAGES else "pt-BR"

    def _build_language_screen(self):
        for child in self.content.winfo_children():
            child.destroy()

        title = tk.Label(self.content, text=self.text["choose_language"], fg="#f8fafc", bg="#101827", font=("Segoe UI", 28, "bold"))
        title.pack(pady=(20, 30))

        grid = tk.Frame(self.content, bg="#101827")
        grid.pack(fill="both", expand=True)

        row = col = 0
        for code, data in LANGUAGES.items():
            b = tk.Button(
                grid,
                text=f"{data['flag']}  {data['name']}",
                command=lambda c=code: self.start_launcher(c),
                fg="#e2e8f0",
                bg="#1e293b",
                activebackground="#334155",
                activeforeground="#ffffff",
                relief="flat",
                padx=20,
                pady=14,
                font=("Segoe UI", 14, "bold"),
                width=25,
            )
            b.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            col += 1
            if col > 1:
                col = 0
                row += 1

        for i in range(2):
            grid.columnconfigure(i, weight=1)

    def start_launcher(self, lang_code):
        self.lang = lang_code
        self.text = I18N[self.lang]

        for child in self.content.winfo_children():
            child.destroy()

        tk.Label(self.content, text=APP_NAME, fg="#93c5fd", bg="#101827", font=("Segoe UI", 30, "bold")).pack(pady=(10, 4))
        tk.Label(self.content, text=self.text["loading"], fg="#f8fafc", bg="#101827", font=("Segoe UI", 20, "bold")).pack(pady=8)
        tk.Label(self.content, text=self.text["checking"], fg="#cbd5e1", bg="#101827", font=("Segoe UI", 12)).pack(pady=6)

        pb = ttk.Progressbar(self.content, variable=self.progress_var, maximum=100, length=700)
        pb.pack(pady=12)
        tk.Label(self.content, textvariable=self.status_var, fg="#e2e8f0", bg="#101827", font=("Segoe UI", 11)).pack(pady=4)

        tk.Button(
            self.content,
            text=self.text["support"],
            command=lambda: self._open_link("https://discord.gg/hKGt4Pw9Wr"),
            bg="#0ea5e9",
            fg="#ffffff",
            relief="flat",
            padx=24,
            pady=10,
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=16)

        threading.Thread(target=self._launcher_checks, daemon=True).start()

    def _launcher_checks(self):
        try:
            self._set_status("Internet...", 10)
            self._check_internet()
            self._set_status("Config remoto...", 35)
            self.config_data = self._fetch_remote_config()
            self._load_background(self.config_data.background_image_url)
            self._set_status("Integridade...", 60)
            self._enforce_online_and_version(self.config_data)
            self._set_status("Pronto!", 100)
            self.after(500, self._build_main_app)
        except Exception as exc:
            self.after(0, lambda: self._show_error(str(exc)))

    def _open_link(self, url):
        import webbrowser
        webbrowser.open(url)

    def _set_status(self, text, progress):
        self.after(0, lambda: self.status_var.set(text))
        self.after(0, lambda: self.progress_var.set(progress))

    def _check_internet(self):
        try:
            requests.get("https://www.google.com/generate_204", timeout=8)
        except Exception:
            raise NetworkError(self.text["no_internet"])

    def _fetch_remote_config(self):
        try:
            res = requests.get(CONFIG_URL, timeout=DEFAULT_TIMEOUT)
            res.raise_for_status()
            data = res.json()
            return RemoteConfig(**data)
        except Exception as exc:
            raise NetworkError(f"Falha ao carregar config remota: {exc}")

    def _enforce_online_and_version(self, cfg: RemoteConfig):
        if not cfg.app_online:
            raise RuntimeError(self.text["maintenance"])
        if self._version_lt(APP_VERSION, cfg.min_version):
            self._set_status(self.text["update_required"], 75)
            self._apply_update(cfg)

    def _apply_update(self, cfg: RemoteConfig):
        res = requests.get(cfg.update_url, timeout=DEFAULT_TIMEOUT)
        res.raise_for_status()
        binary = res.content
        digest = hashlib.sha256(binary).hexdigest()
        if digest.lower() != cfg.update_sha256.lower():
            raise SecurityError("Hash da atualização inválido. Atualização bloqueada por segurança.")

        exe_path = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
        update_file = exe_path.with_suffix(".new")
        update_file.write_bytes(binary)
        raise RuntimeError("Atualização validada. Reinicie o app para concluir a troca do executável.")

    def _load_background(self, image_url):
        if not image_url:
            return
        try:
            cached = CACHE_DIR / "bg.jpg"
            if not cached.exists():
                data = requests.get(image_url, timeout=DEFAULT_TIMEOUT).content
                cached.write_bytes(data)
            image = Image.open(cached).resize((1280, 760), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(image)
            self.after(0, lambda: self.bg_label.config(image=self.bg_photo))
        except Exception:
            pass

    @staticmethod
    def _version_lt(v1, v2):
        def parse(v):
            return [int(p) for p in v.split(".")]
        return parse(v1) < parse(v2)

    def _show_error(self, err):
        messagebox.showerror(APP_NAME, err)
        self.destroy()

    def _build_main_app(self):
        for child in self.overlay.winfo_children():
            child.destroy()

        main = MainWikiFrame(self.overlay, self.lang)
        main.pack(fill="both", expand=True)


class MainWikiFrame(tk.Frame):
    BASE_API = "https://grand-piece-online.fandom.com/api.php"

    CATEGORY_HINTS = {
        0: "Boss",
        1: "Sword Weapon Gun",
        2: "Ship Boat",
        3: "Gamepass",
        4: "Merchant NPC",
        5: "Trade Value Meta",
    }

    def __init__(self, master, lang):
        super().__init__(master, bg="#020617")
        self.lang = lang
        self.text = I18N[lang]
        self.results_queues = [queue.Queue() for _ in range(6)]
        self.images = []

        top = tk.Frame(self, bg="#020617", pady=12, padx=12)
        top.pack(fill="x")
        tk.Label(top, text=APP_NAME, fg="#38bdf8", bg="#020617", font=("Segoe UI", 24, "bold")).pack(side="left")

        search_wrap = tk.Frame(top, bg="#020617")
        search_wrap.pack(side="right")
        self.search_var = tk.StringVar()
        e = ttk.Entry(search_wrap, textvariable=self.search_var, width=55)
        e.pack(side="left", padx=8)
        e.insert(0, self.text["search_placeholder"])
        ttk.Button(search_wrap, text=self.text["search"], command=self.search_all_tabs).pack(side="left")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.text_widgets = []

        for label in self.text["tabs"]:
            tab = tk.Frame(self.nb, bg="#0f172a")
            self.nb.add(tab, text=label)
            txt = tk.Text(tab, wrap="word", bg="#0f172a", fg="#e2e8f0", font=("Segoe UI", 11), relief="flat")
            txt.pack(fill="both", expand=True, padx=8, pady=8)
            self.text_widgets.append(txt)

        self.search_all_tabs(initial=True)
        self.after(300, self._flush_queues)

    def search_all_tabs(self, initial=False):
        query = self.search_var.get().strip()
        if not query or query == self.text["search_placeholder"]:
            query = "Grand Piece Online"

        for idx, widget in enumerate(self.text_widgets):
            widget.delete("1.0", "end")
            widget.insert("end", "Carregando resultados...\n")
            hint = self.CATEGORY_HINTS.get(idx, "")
            final_query = f"{query} {hint}" if not initial else hint
            threading.Thread(target=self._fetch_and_render, args=(idx, final_query), daemon=True).start()

    def _fetch_and_render(self, idx, query):
        try:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 8,
            }
            res = requests.get(self.BASE_API, params=params, timeout=DEFAULT_TIMEOUT)
            res.raise_for_status()
            docs = res.json().get("query", {}).get("search", [])

            parts = [f"=== {self.text['tabs'][idx]} ===\n\n"]
            for doc in docs:
                title = doc.get("title", "")
                snippet = doc.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
                details = self._get_page_extract(title)
                parts.append(f"# {title}\n{snippet}\n{details}\n\n")

            self.results_queues[idx].put("".join(parts))
        except Exception as exc:
            self.results_queues[idx].put(f"Erro ao buscar dados: {exc}")

    def _get_page_extract(self, title):
        params = {
            "action": "query",
            "prop": "extracts|pageimages",
            "titles": title,
            "format": "json",
            "exintro": 1,
            "explaintext": 1,
            "piprop": "original",
        }
        res = requests.get(self.BASE_API, params=params, timeout=DEFAULT_TIMEOUT)
        res.raise_for_status()
        pages = res.json().get("query", {}).get("pages", {})
        for page in pages.values():
            extract = page.get("extract", "Sem descrição disponível.")[:900]
            source = f"{self.text['source']}: https://grand-piece-online.fandom.com/wiki/{quote(title.replace(' ', '_'))}"
            return f"{extract}\n{source}"
        return ""

    def _flush_queues(self):
        for idx, q in enumerate(self.results_queues):
            try:
                content = q.get_nowait()
                w = self.text_widgets[idx]
                w.delete("1.0", "end")
                w.insert("end", content)
            except queue.Empty:
                pass
        self.after(300, self._flush_queues)


if __name__ == "__main__":
    try:
        app = LauncherApp()
        app.mainloop()
    except KeyboardInterrupt:
        pass
