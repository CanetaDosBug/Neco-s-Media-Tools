"""
converter.py
Motor de conversão de arquivos. Detecta a categoria do arquivo pela extensão
e converte para o formato de destino escolhido, usando a ferramenta certa
para cada categoria (Pillow, ffmpeg, LibreOffice, etc).

Não sabe nada sobre interface gráfica.
"""

import os
import shutil
import subprocess


class FormatoNaoSuportado(Exception):
    """Erro para quando a conversão pedida não é possível."""
    pass


class FerramentaAusente(Exception):
    """Erro para quando falta uma ferramenta externa (ffmpeg, LibreOffice, Calibre, etc)."""
    pass


class FileConverter:
    # Categoria -> extensões reconhecidas como entrada
    CATEGORIAS = {
        "imagem":       [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".ico"],
        "gif":          [".gif"],
        "vetor":        [".svg"],
        "documento":    [".docx", ".doc", ".odt", ".rtf", ".txt", ".pdf"],
        "planilha":     [".xlsx", ".xls", ".csv", ".tsv", ".ods"],
        "apresentacao": [".pptx", ".ppt", ".odp"],
        "audio":        [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".opus", ".wma"],
        "video":        [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"],
        "ebook":        [".epub", ".mobi", ".azw3", ".fb2"],
    }

    # Categoria -> formatos que sabemos gerar como saída
    DESTINOS = {
        "imagem":       ["png", "jpg", "jpeg", "webp", "bmp", "tiff", "ico", "pdf"],
        "gif":          ["mp4", "webp", "png"],
        "vetor":        ["png", "jpg", "pdf"],
        "documento":    ["pdf", "docx", "odt", "rtf", "txt"],
        "planilha":     ["xlsx", "csv", "tsv", "json", "ods", "pdf"],
        "apresentacao": ["pdf", "pptx", "odp"],
        "audio":        ["mp3", "wav", "m4a", "flac", "ogg", "aac"],
        "video":        ["mp4", "avi", "mov", "mkv", "webm", "gif"],
        "ebook":        ["pdf", "epub", "mobi", "azw3", "txt"],
    }

    def __init__(self, ffmpeg_location=None, libreoffice_location=None):
        self.ffmpeg_location = ffmpeg_location or shutil.which("ffmpeg")
        self.libreoffice_location = libreoffice_location or self._detectar_libreoffice()

    # ---------- Utilidades ----------

    def _detectar_libreoffice(self):
        for nome in ("soffice", "libreoffice"):
            caminho = shutil.which(nome)
            if caminho:
                return caminho
        caminho_padrao_win = r"C:\Program Files\LibreOffice\program\soffice.exe"
        if os.path.exists(caminho_padrao_win):
            return caminho_padrao_win
        return None

    def categoria_do_arquivo(self, caminho):
        ext = os.path.splitext(caminho)[1].lower()
        for categoria, extensoes in self.CATEGORIAS.items():
            if ext in extensoes:
                return categoria
        return None

    def formatos_destino_possiveis(self, caminho):
        categoria = self.categoria_do_arquivo(caminho)
        return self.DESTINOS.get(categoria, []) if categoria else []

    def todos_formatos_destino(self):
        """Lista única com todos os formatos de saída suportados (pro seletor 'ANY to...')."""
        formatos = set()
        for lista in self.DESTINOS.values():
            formatos.update(lista)
        return sorted(formatos)

    # ---------- Conversão principal ----------

    def converter(self, caminho_entrada, formato_destino, pasta_saida):
        formato_destino = formato_destino.lower().lstrip(".")
        categoria = self.categoria_do_arquivo(caminho_entrada)

        if not categoria:
            raise FormatoNaoSuportado(
                f"Não reconheço o formato de entrada: {os.path.splitext(caminho_entrada)[1]}"
            )

        if formato_destino not in self.DESTINOS.get(categoria, []):
            raise FormatoNaoSuportado(
                f"Não é possível converter arquivos de '{categoria}' para .{formato_destino}"
            )

        nome_base = os.path.splitext(os.path.basename(caminho_entrada))[0]
        caminho_saida = os.path.join(pasta_saida, f"{nome_base}.{formato_destino}")

        metodo = getattr(self, f"_converter_{categoria}", None)
        if not metodo:
            raise FormatoNaoSuportado(f"Conversor para categoria '{categoria}' ainda não implementado.")

        return metodo(caminho_entrada, formato_destino, caminho_saida)

    # ---------- Conversores por categoria ----------

    def _converter_imagem(self, entrada, formato, saida):
        from PIL import Image
        img = Image.open(entrada)
        if formato in ("jpg", "jpeg", "pdf") and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(saida)
        return saida

    def _converter_gif(self, entrada, formato, saida):
        return self._converter_via_ffmpeg(entrada, saida)

    def _converter_vetor(self, entrada, formato, saida):
        try:
            import cairosvg
        except ImportError:
            raise FerramentaAusente("Instale: pip install cairosvg (necessário para converter SVG)")

        if formato == "png":
            cairosvg.svg2png(url=entrada, write_to=saida)
        elif formato == "pdf":
            cairosvg.svg2pdf(url=entrada, write_to=saida)
        elif formato in ("jpg", "jpeg"):
            temp_png = saida.rsplit(".", 1)[0] + "_temp.png"
            cairosvg.svg2png(url=entrada, write_to=temp_png)
            from PIL import Image
            Image.open(temp_png).convert("RGB").save(saida)
            os.remove(temp_png)
        return saida

    def _converter_documento(self, entrada, formato, saida):
        ext_entrada = os.path.splitext(entrada)[1].lower()

        # Caminhos que não dependem de LibreOffice
        if ext_entrada == ".txt" and formato == "pdf":
            return self._txt_para_pdf(entrada, saida)
        if ext_entrada == ".pdf" and formato == "txt":
            return self._pdf_para_txt(entrada, saida)

        return self._converter_via_libreoffice(entrada, formato, saida)

    def _converter_planilha(self, entrada, formato, saida):
        import pandas as pd
        ext_entrada = os.path.splitext(entrada)[1].lower()

        if ext_entrada in (".xlsx", ".xls"):
            df = pd.read_excel(entrada)
        elif ext_entrada == ".csv":
            df = pd.read_csv(entrada)
        elif ext_entrada == ".tsv":
            df = pd.read_csv(entrada, sep="\t")
        elif ext_entrada == ".ods":
            df = pd.read_excel(entrada, engine="odf")
        else:
            raise FormatoNaoSuportado(f"Entrada de planilha não suportada: {ext_entrada}")

        if formato == "xlsx":
            df.to_excel(saida, index=False)
        elif formato == "csv":
            df.to_csv(saida, index=False)
        elif formato == "tsv":
            df.to_csv(saida, index=False, sep="\t")
        elif formato == "json":
            df.to_json(saida, orient="records", indent=2, force_ascii=False)
        elif formato == "ods":
            df.to_excel(saida, index=False, engine="odf")
        elif formato == "pdf":
            return self._converter_via_libreoffice(entrada, formato, saida)

        return saida

    def _converter_apresentacao(self, entrada, formato, saida):
        return self._converter_via_libreoffice(entrada, formato, saida)

    def _converter_audio(self, entrada, formato, saida):
        return self._converter_via_ffmpeg(entrada, saida)

    def _converter_video(self, entrada, formato, saida):
        return self._converter_via_ffmpeg(entrada, saida)

    def _converter_ebook(self, entrada, formato, saida):
        ebook_convert = shutil.which("ebook-convert")
        if not ebook_convert:
            raise FerramentaAusente(
                "Conversão de e-books precisa do Calibre instalado (comando 'ebook-convert'). "
                "Baixe em: https://calibre-ebook.com/download"
            )
        resultado = subprocess.run([ebook_convert, entrada, saida], capture_output=True, text=True)
        if resultado.returncode != 0:
            raise RuntimeError(f"Erro no ebook-convert: {resultado.stderr}")
        return saida

    # ---------- Motores compartilhados ----------

    def _converter_via_ffmpeg(self, entrada, saida):
        if not self.ffmpeg_location:
            raise FerramentaAusente(
                "ffmpeg não encontrado. Instale-o e/ou informe o caminho em "
                "FileConverter(ffmpeg_location=...)."
            )
        comando = [self.ffmpeg_location, "-y", "-i", entrada, saida]
        resultado = subprocess.run(comando, capture_output=True, text=True)
        if resultado.returncode != 0:
            raise RuntimeError(f"Erro no ffmpeg: {resultado.stderr[-500:]}")
        return saida

    def _converter_via_libreoffice(self, entrada, formato, saida):
        if not self.libreoffice_location:
            raise FerramentaAusente(
                "LibreOffice não encontrado. Instale em https://www.libreoffice.org/download/ "
                "para converter documentos, planilhas e apresentações entre formatos de escritório."
            )
        pasta_saida = os.path.dirname(saida)
        comando = [
            self.libreoffice_location, "--headless", "--convert-to", formato,
            "--outdir", pasta_saida, entrada,
        ]
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=120)
        if resultado.returncode != 0:
            raise RuntimeError(f"Erro no LibreOffice: {resultado.stderr}")
        return saida

    def _txt_para_pdf(self, entrada, saida):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except ImportError:
            raise FerramentaAusente("Instale: pip install reportlab (necessário para TXT -> PDF)")

        with open(entrada, "r", encoding="utf-8", errors="ignore") as f:
            linhas = f.readlines()

        c = canvas.Canvas(saida, pagesize=A4)
        largura, altura = A4
        y = altura - 50
        for linha in linhas:
            if y < 50:
                c.showPage()
                y = altura - 50
            c.drawString(50, y, linha.rstrip()[:110])
            y -= 14
        c.save()
        return saida

    def _pdf_para_txt(self, entrada, saida):
        try:
            from pypdf import PdfReader
        except ImportError:
            raise FerramentaAusente("Instale: pip install pypdf (necessário para PDF -> TXT)")

        leitor = PdfReader(entrada)
        with open(saida, "w", encoding="utf-8") as f:
            for pagina in leitor.pages:
                f.write(pagina.extract_text() or "")
                f.write("\n\n")
        return saida
