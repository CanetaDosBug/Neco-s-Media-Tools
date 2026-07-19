"""
interface.py
Interface gráfica (CustomTkinter). Usa MediaDownloader e MediaPlayer
para fazer o trabalho pesado — este arquivo só cuida de widgets e eventos.
"""

import os
import sys
import threading
import math
import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence, ImageDraw
from tkinter import filedialog, messagebox
from converter import FileConverter
from recursos import caminho_recurso

from theme import PRIMARIA, PRIMARIA_HOVER, SECUNDARIA, SECUNDARIA_HOVER, TEXTO, TEXTO_SECUNDARIO, PROGRESSO, HEADER, FUNDO, SELETOR
from downloader import MediaDownloader
from player import MediaPlayer


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Neco's MediaTools")
        self.geometry("520x600")
        self.resizable(False, False)
        self._definir_icone()
        self.configure(fg_color=FUNDO)

        # Procura o ffmpeg embutido na pasta assets/; se não existir (ex: em
        # desenvolvimento, antes de você ter colocado o .exe lá), cai no
        # comportamento antigo de procurar no PATH do sistema.
        caminho_ffmpeg_embutido = caminho_recurso(os.path.join("assets", "ffmpeg.exe"))
        ffmpeg_location = caminho_ffmpeg_embutido if os.path.exists(caminho_ffmpeg_embutido) else None

        # Lógica separada da interface
        self.downloader = MediaDownloader(ffmpeg_location=ffmpeg_location)
        self.player = MediaPlayer()

        self.converter = FileConverter(ffmpeg_location=ffmpeg_location)
        self.arquivos_para_converter = []

        # Estado
        self.pasta_destino = ctk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.arquivo_baixado = None

        self._montar_cabecalho()
        self._montar_abas()

    def _criar_icone_sol(self, tamanho=18, cor="#F5F5F5"):
        """Desenha um solzinho simples (círculo + raios) como ícone, sem depender de emoji."""
        img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        centro = tamanho / 2
        raio = tamanho / 4

        draw.ellipse([centro - raio, centro - raio, centro + raio, centro + raio], fill=cor)

        for angulo_graus in range(0, 360, 45):
            angulo = math.radians(angulo_graus)
            x1 = centro + math.cos(angulo) * (raio + 2)
            y1 = centro + math.sin(angulo) * (raio + 2)
            x2 = centro + math.cos(angulo) * (raio + 5)
            y2 = centro + math.sin(angulo) * (raio + 5)
            draw.line([x1, y1, x2, y2], fill=cor, width=2)

        return img

    def _criar_icone_lua(self, tamanho=18, cor="#F5F5F5"):
        """Desenha uma lua crescente simples como ícone, sem depender de emoji."""
        img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw.ellipse([2, 2, tamanho - 2, tamanho - 2], fill=cor)
        # "Morde" um pedaço do círculo pra virar crescente (pinta com alpha 0, sem blend)
        draw.ellipse([6, 0, tamanho + 2, tamanho - 4], fill=(0, 0, 0, 0))

        return img

    def _carregar_frames_gif(self, caminho, tamanho=(40, 40)):
        """Lê todos os frames de um GIF e devolve uma lista de CTkImage prontos pra animar."""
        try:
            gif = Image.open(caminho)
            frames = []
            for frame in ImageSequence.Iterator(gif):
                frame_rgba = frame.convert("RGBA").resize(tamanho)
                frames.append(ctk.CTkImage(light_image=frame_rgba, dark_image=frame_rgba, size=tamanho))
            return frames
        except Exception as erro:
            print(f"Não foi possível carregar o GIF {caminho}: {erro}")
            return []

    def _animar_logo(self):
        frames = self.frames_logo_escuro if ctk.get_appearance_mode() == "Dark" else self.frames_logo_claro

        if not frames:
            return  # GIF não carregou, evita erro

        self.label_logo.configure(image=frames[self.frame_atual_logo])
        self.frame_atual_logo = (self.frame_atual_logo + 1) % len(frames)

        # 80ms por frame (~12 fps) — ajuste ao gosto
        self.after(80, self._animar_logo)

    # ---------- Construção da UI ----------

    def _definir_icone(self):
        """Ícone da janela / barra de tarefas."""
        try:
            if sys.platform.startswith("win"):
                self.iconbitmap(caminho_recurso(os.path.join("assets", "icone.ico")))
            else:
                img = Image.open(caminho_recurso(os.path.join("assets", "icone.png")))
                self._icone_tk = ImageTk.PhotoImage(img)  # guarda referência viva
                self.iconphoto(True, self._icone_tk)
        except Exception as erro:
            print(f"Ícone não encontrado, seguindo sem ele: {erro}")

    def _montar_cabecalho(self):
        """Barra superior com logo, nome do app e descrição das seções."""
        frame_header = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color=HEADER)
        frame_header.pack(fill="x", side="top")

        self.frames_logo_claro = self._carregar_frames_gif(caminho_recurso(os.path.join("assets", "logo_claro.gif")))
        self.frames_logo_escuro = self._carregar_frames_gif(caminho_recurso(os.path.join("assets", "logo_escuro.gif")))
        self.frame_atual_logo = 0

        self.label_logo = ctk.CTkLabel(frame_header, text="")
        self.label_logo.pack(side="left", padx=(15, 10), pady=10)

        self._animar_logo()

        frame_textos = ctk.CTkFrame(frame_header, fg_color=HEADER)
        frame_textos.pack(side="left", pady=10)

        self.icone_sol = ctk.CTkImage(light_image=self._criar_icone_sol(), dark_image=self._criar_icone_sol(), size=(18, 18))
        self.icone_lua = ctk.CTkImage(light_image=self._criar_icone_lua(), dark_image=self._criar_icone_lua(), size=(18, 18))

        self.botao_tema = ctk.CTkButton(
            frame_header,
            text="",
            image=self.icone_sol if ctk.get_appearance_mode() == "Dark" else self.icone_lua,
            width=36, height=36,
            corner_radius=18,
            fg_color=SECUNDARIA,
            hover_color=SECUNDARIA_HOVER,
            command=self.alternar_tema,
        )
        self.botao_tema.pack(side="right", padx=15, pady=10)

        ctk.CTkLabel(frame_textos, text="Neco's MediaTools", font=("Arial", 18, "bold"), text_color=TEXTO, fg_color=HEADER).pack(anchor="w")
        ctk.CTkLabel(
            frame_textos,
            text="Baixador de Vídeo/Áudio  •  Conversor",
            font=("Arial", 12),
            text_color=TEXTO_SECUNDARIO,
            fg_color=HEADER,
        ).pack(anchor="w")

    def alternar_tema(self):
        modo_atual = ctk.get_appearance_mode()
        novo_modo = "light" if modo_atual == "Dark" else "dark"
        ctk.set_appearance_mode(novo_modo)

        self.botao_tema.configure(image=self.icone_lua if novo_modo == "light" else self.icone_sol)
        self.frame_atual_logo = 0  # reinicia a animação do gif certo

    def _montar_abas(self):
        """Cria o sistema de abas e delega o conteúdo de cada uma."""
        self.tabview = ctk.CTkTabview(self, width=480, height=480, fg_color=FUNDO, text_color=TEXTO, segmented_button_fg_color=SELETOR, segmented_button_selected_color=PRIMARIA,
            segmented_button_selected_hover_color=PRIMARIA_HOVER,
            segmented_button_unselected_color=SECUNDARIA,
            segmented_button_unselected_hover_color=SECUNDARIA_HOVER)
        self.tabview.pack(padx=20, pady=(10, 20), fill="both", expand=True)

        self.tabview.add("Baixador")
        self.tabview.add("Conversor")

        self.tabview._segmented_button.configure(text_color=TEXTO)
        self.tabview.tab("Baixador").configure(fg_color=FUNDO)
        self.tabview.tab("Conversor").configure(fg_color=FUNDO)

        scroll_baixador = ctk.CTkScrollableFrame(self.tabview.tab("Baixador"), fg_color=FUNDO)
        scroll_baixador.pack(fill="both", expand=True)

        scroll_conversor = ctk.CTkScrollableFrame(self.tabview.tab("Conversor"), fg_color=FUNDO)
        scroll_conversor.pack(fill="both", expand=True)

        self._montar_aba_baixador(scroll_baixador)
        self._montar_aba_conversor(scroll_conversor)

    def _montar_aba_conversor(self, aba):
        ctk.CTkLabel(aba, text="Conversor de Arquivos", font=("Arial", 16, "bold"), text_color=TEXTO, fg_color=FUNDO).pack(pady=(15, 5))
        ctk.CTkLabel(
            aba,
            text="Imagens, documentos, planilhas, áudio, vídeo, GIF, vetor e e-books",
            font=("Arial", 11), text_color=TEXTO_SECUNDARIO, fg_color=FUNDO
        ).pack(pady=(0, 10))

        frame_botoes_arquivo = ctk.CTkFrame(aba, fg_color="transparent")
        frame_botoes_arquivo.pack(pady=(0, 10))

        ctk.CTkButton(
            frame_botoes_arquivo, text="+ Adicionar arquivos", command=self.adicionar_arquivos_conversor,
            fg_color=PRIMARIA, hover_color=PRIMARIA_HOVER, width=160
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            frame_botoes_arquivo, text="Limpar lista", command=self.limpar_lista_conversor,
            fg_color=SECUNDARIA, hover_color=SECUNDARIA_HOVER, text_color=TEXTO, width=120
        ).pack(side="left")

        self.frame_lista_arquivos = ctk.CTkScrollableFrame(aba, width=440, height=130, fg_color=HEADER)
        self.frame_lista_arquivos.pack(pady=(0, 15))

        ctk.CTkLabel(
            self.frame_lista_arquivos, text="Nenhum arquivo adicionado ainda.", text_color=TEXTO_SECUNDARIO
        ).pack(pady=20)

        ctk.CTkLabel(aba, text="Converter tudo para:", text_color=TEXTO, fg_color=FUNDO).pack()

        self.formato_destino_selecionado = "pdf"
        self.botao_seletor_formato = ctk.CTkButton(
            aba, text=f"{self.formato_destino_selecionado}  ▼",
            command=self._abrir_seletor_formato, width=200,
            fg_color=SECUNDARIA, hover_color=SECUNDARIA_HOVER, text_color=TEXTO,
        )
        self.botao_seletor_formato.pack(pady=(5, 15))

        frame_pasta_conv = ctk.CTkFrame(aba, fg_color="transparent")
        frame_pasta_conv.pack(pady=(0, 15))

        ctk.CTkEntry(frame_pasta_conv, width=330, textvariable=self.pasta_destino).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            frame_pasta_conv, text="Escolher pasta", command=self.escolher_pasta, width=100,
            fg_color=SECUNDARIA, hover_color=SECUNDARIA_HOVER, text_color=TEXTO
        ).pack(side="left")

        self.botao_converter = ctk.CTkButton(
            aba, text="Converter", command=self.converter_arquivos, width=200, height=40,
            fg_color=PRIMARIA, hover_color=PRIMARIA_HOVER
        )
        self.botao_converter.pack(pady=(5, 15))

        self.barra_progresso_conversor = ctk.CTkProgressBar(aba, width=440, progress_color=PROGRESSO)
        self.barra_progresso_conversor.set(0)
        self.barra_progresso_conversor.pack(pady=(0, 10))

        self.label_status_conversor = ctk.CTkLabel(aba, text="Aguardando arquivos...", text_color=TEXTO_SECUNDARIO, fg_color=FUNDO)
        self.label_status_conversor.pack()

    def _montar_aba_baixador(self, aba):
        ctk.CTkLabel(aba, text="Cole a URL do vídeo/áudio:", text_color=TEXTO, fg_color=FUNDO).pack(pady=(15, 0))
        self.campo_url = ctk.CTkEntry(aba, width=440, placeholder_text="https://...")
        self.campo_url.pack(pady=(5, 15))

        ctk.CTkLabel(aba, text="Formato de saída:", text_color=TEXTO, fg_color=FUNDO).pack()
        self.seletor_formato = ctk.CTkOptionMenu(
            aba, values=self.downloader.formatos_disponiveis(), width=200, text_color=TEXTO, fg_color=PRIMARIA, button_color=PRIMARIA, button_hover_color=PRIMARIA_HOVER
        )
        self.seletor_formato.set("MP3 (áudio)")
        self.seletor_formato.pack(pady=(5, 15))

        frame_pasta = ctk.CTkFrame(aba, fg_color="transparent")
        frame_pasta.pack(pady=(0, 15))

        self.entrada_pasta = ctk.CTkEntry(frame_pasta, width=330, textvariable=self.pasta_destino)
        self.entrada_pasta.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            frame_pasta, text="Escolher pasta", command=self.escolher_pasta, width=100, text_color=TEXTO, fg_color=PRIMARIA, hover_color=PRIMARIA_HOVER
        ).pack(side="left")

        self.botao_baixar = ctk.CTkButton(
            aba, text="Baixar", command=self.baixar, width=200, height=40,
            fg_color=PRIMARIA, hover_color=PRIMARIA_HOVER, text_color=TEXTO
        )
        self.botao_baixar.pack(pady=(5, 15))

        self.barra_progresso = ctk.CTkProgressBar(aba, width=440, progress_color=PROGRESSO, fg_color=FUNDO)
        self.barra_progresso.set(0)
        self.barra_progresso.pack(pady=(0, 10))

        self.label_status = ctk.CTkLabel(aba, text="Aguardando...", text_color=TEXTO_SECUNDARIO, fg_color=FUNDO)
        self.label_status.pack(pady=(0, 15))

        frame_play = ctk.CTkFrame(aba, fg_color="transparent")
        frame_play.pack(pady=(0, 10))

        self.botao_tocar = ctk.CTkButton(
            frame_play, text="▶ Tocar", command=self.tocar_local, width=100, state="disabled", text_color=TEXTO, fg_color=PRIMARIA
        )
        self.botao_tocar.pack(side="left", padx=(0, 10))

        ctk.CTkButton(frame_play, text="■ Parar", command=self.parar_audio, width=100,
                      fg_color=SECUNDARIA, hover_color=SECUNDARIA_HOVER, text_color=TEXTO).pack(side="left")

    def _abrir_seletor_formato(self):
        """Janela customizada com os formatos agrupados por categoria (imagem, áudio, vídeo, etc)."""
        janela_popup = ctk.CTkToplevel(self)
        janela_popup.title("Escolha o formato")
        janela_popup.geometry("340x420")
        janela_popup.configure(fg_color=FUNDO)
        janela_popup.transient(self)   # fica sempre na frente da janela principal
        janela_popup.grab_set()        # bloqueia clique na janela principal até fechar

        # Centraliza a janelinha em cima do botão que a abriu
        x = self.winfo_x() + 90
        y = self.winfo_y() + 150
        janela_popup.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            janela_popup, text="Escolha o formato de destino",
            font=("Arial", 14, "bold"), text_color=TEXTO, fg_color=FUNDO
        ).pack(pady=(15, 10))

        area_rolagem = ctk.CTkScrollableFrame(janela_popup, fg_color=FUNDO, width=300, height=320)
        area_rolagem.pack(padx=15, pady=(0, 15), fill="both", expand=True)

        # Nomes de exibição mais amigáveis pra cada categoria
        nomes_categorias = {
            "imagem": "Imagem", "gif": "GIF", "vetor": "Vetor",
            "documento": "Documento", "planilha": "Planilha",
            "apresentacao": "Apresentação", "audio": "Áudio", "video": "Vídeo",
            "ebook": "E-book",
        }

        for categoria, formatos in self.converter.DESTINOS.items():
            ctk.CTkLabel(
                area_rolagem, text=nomes_categorias.get(categoria, categoria).upper(),
                font=("Arial", 11, "bold"), text_color=PRIMARIA, fg_color=FUNDO, anchor="w"
            ).pack(fill="x", padx=5, pady=(10, 4))

            frame_botoes = ctk.CTkFrame(area_rolagem, fg_color=FUNDO)
            frame_botoes.pack(fill="x", padx=5)

            # "Wrap" manual: quebra os botões em linhas de 4 em 4
            for i in range(0, len(formatos), 4):
                linha = ctk.CTkFrame(frame_botoes, fg_color=FUNDO)
                linha.pack(fill="x", pady=2)
                for formato in formatos[i:i + 4]:
                    selecionado = formato == self.formato_destino_selecionado
                    ctk.CTkButton(
                        linha, text=formato, width=60, height=28,
                        fg_color=PRIMARIA if selecionado else SECUNDARIA,
                        hover_color=PRIMARIA_HOVER if selecionado else SECUNDARIA_HOVER,
                        text_color=TEXTO,
                        command=lambda f=formato, j=janela_popup: self._escolher_formato_destino(f, j)
                    ).pack(side="left", padx=3)

    def _escolher_formato_destino(self, formato, janela_popup):
        self.formato_destino_selecionado = formato
        self.botao_seletor_formato.configure(text=f"{formato}  ▼")
        janela_popup.grab_release()
        janela_popup.destroy()

    # ---------- Eventos ----------

    def escolher_pasta(self):
        caminho = filedialog.askdirectory(title="Escolha onde salvar o arquivo")
        if caminho:
            self.pasta_destino.set(caminho)

    def atualizar_progresso(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            baixado = d.get('downloaded_bytes', 0)
            if total:
                percentual = baixado / total
                self.barra_progresso.set(percentual)
                self.label_status.configure(text=f"Baixando... {int(percentual * 100)}%")
        elif d['status'] == 'finished':
            self.barra_progresso.set(1.0)
            self.label_status.configure(text="Processando arquivo...")

    def baixar(self):
        url = self.campo_url.get().strip()
        destino = self.pasta_destino.get()
        formato = self.seletor_formato.get()

        if not url:
            messagebox.showwarning("Atenção", "Cole uma URL antes de baixar.")
            return
        if not destino:
            messagebox.showwarning("Atenção", "Escolha uma pasta de destino.")
            return

        self.botao_baixar.configure(state="disabled", text="Baixando...")
        self.botao_tocar.configure(state="disabled")
        self.barra_progresso.set(0)
        self.label_status.configure(text="Iniciando download...")
        self.arquivo_baixado = None

        threading.Thread(target=self._tarefa_download, args=(url, destino, formato), daemon=True).start()

    def adicionar_arquivos_conversor(self):
        caminhos = filedialog.askopenfilenames(title="Escolha os arquivos para converter")
        if not caminhos:
            return
        for caminho in caminhos:
            if caminho not in self.arquivos_para_converter:
                self.arquivos_para_converter.append(caminho)
        self._atualizar_lista_visual_conversor()

    def limpar_lista_conversor(self):
        self.arquivos_para_converter = []
        self._atualizar_lista_visual_conversor()

    def _remover_arquivo_conversor(self, caminho):
        self.arquivos_para_converter.remove(caminho)
        self._atualizar_lista_visual_conversor()

    def _atualizar_lista_visual_conversor(self):
        for widget in self.frame_lista_arquivos.winfo_children():
            widget.destroy()

        if not self.arquivos_para_converter:
            ctk.CTkLabel(
                self.frame_lista_arquivos, text="Nenhum arquivo adicionado ainda.", text_color=TEXTO_SECUNDARIO
            ).pack(pady=20)
            return

        # Agrupa os arquivos por categoria, mantendo a ordem em que foram adicionados
        grupos = {}
        for caminho in self.arquivos_para_converter:
            categoria = self.converter.categoria_do_arquivo(caminho) or "não reconhecido"
            grupos.setdefault(categoria, []).append(caminho)

        for categoria, arquivos in grupos.items():
            ctk.CTkLabel(
                self.frame_lista_arquivos, text=categoria.upper(),
                font=("Arial", 11, "bold"), text_color=PRIMARIA, anchor="w"
            ).pack(fill="x", padx=5, pady=(10, 2))

            for caminho in arquivos:
                nome = os.path.basename(caminho)

                linha = ctk.CTkFrame(self.frame_lista_arquivos, fg_color="transparent")
                linha.pack(fill="x", pady=1, padx=(15, 5))

                ctk.CTkLabel(
                    linha, text=nome, text_color=TEXTO, anchor="w", font=("Arial", 11)
                ).pack(side="left", fill="x", expand=True)

                ctk.CTkButton(
                    linha, text="✕", width=22, height=22, fg_color=SECUNDARIA, hover_color=SECUNDARIA_HOVER,
                    text_color=TEXTO, command=lambda c=caminho: self._remover_arquivo_conversor(c)
                ).pack(side="right")

    def converter_arquivos(self):
        if not self.arquivos_para_converter:
            messagebox.showwarning("Atenção", "Adicione pelo menos um arquivo.")
            return

        destino = self.pasta_destino.get()
        if not destino:
            messagebox.showwarning("Atenção", "Escolha uma pasta de destino.")
            return

        formato = self.formato_destino_selecionado

        self.botao_converter.configure(state="disabled", text="Convertendo...")
        self.barra_progresso_conversor.set(0)

        threading.Thread(
            target=self._tarefa_conversao,
            args=(list(self.arquivos_para_converter), destino, formato),
            daemon=True,
        ).start()

    def _tarefa_conversao(self, arquivos, destino, formato):
        total = len(arquivos)
        sucesso = 0
        erros = []

        for i, caminho in enumerate(arquivos, start=1):
            nome = os.path.basename(caminho)
            self.label_status_conversor.configure(text=f"Convertendo {nome} ({i}/{total})...")
            try:
                self.converter.converter(caminho, formato, destino)
                sucesso += 1
            except Exception as erro:
                erros.append(f"{nome}: {erro}")

            self.barra_progresso_conversor.set(i / total)

        if erros:
            texto_erro = "\n".join(erros[:5])
            self.label_status_conversor.configure(text=f"Concluído com avisos ({sucesso}/{total} ok).")
            messagebox.showwarning("Concluído com avisos", f"{sucesso}/{total} convertidos.\n\nErros:\n{texto_erro}")
        else:
            self.label_status_conversor.configure(text=f"Todos os {total} arquivos convertidos!")
            messagebox.showinfo("Sucesso", f"{sucesso}/{total} arquivos convertidos com sucesso!")

        self.botao_converter.configure(state="normal", text="Converter")

    def _tarefa_download(self, url, destino, formato):
        try:
            caminho = self.downloader.baixar(
                url, destino, formato, progress_callback=self.atualizar_progresso
            )
            self.arquivo_baixado = caminho
            self.label_status.configure(text="Download concluído!")
            self.botao_tocar.configure(state="normal")
            messagebox.showinfo("Sucesso", "Arquivo baixado com sucesso!")

        except Exception as erro:
            self.label_status.configure(text="Erro no download.")
            messagebox.showerror("Erro", f"Algo deu errado:\n{erro}")

        finally:
            self.botao_baixar.configure(state="normal", text="Baixar")

    def tocar_local(self):
        if not self.arquivo_baixado or not os.path.exists(self.arquivo_baixado):
            messagebox.showwarning("Atenção", "Nenhum arquivo válido para tocar.")
            return

        formato = self.seletor_formato.get()

        try:
            if self.downloader.is_audio(formato):
                self.player.tocar_audio(self.arquivo_baixado)
                self.label_status.configure(text="Tocando áudio local...")
            else:
                self.player.abrir_video_no_player_padrao(self.arquivo_baixado)
                self.label_status.configure(text="Abrindo vídeo no player padrão...")
        except Exception as erro:
            messagebox.showerror("Erro", f"Não foi possível tocar:\n{erro}")

    def parar_audio(self):
        self.player.parar_audio()
        self.label_status.configure(text="Parado.")
