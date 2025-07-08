#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyTools: Suíte de Ferramentas para Linux e Termux
"""

import os
import subprocess
import time
import datetime
import requests
import socket
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

# Bibliotecas de terceiros
try:
    from rich.console import Console
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich.text import Text
    from rich.box import ROUNDED
    from pytube import YouTube, Playlist
    from pytube.exceptions import PytubeError, RegexMatchError
except ImportError as e:
    print(f"Erro de importação: {e}. Por favor, instale as dependências necessárias.")
    print("Execute: pip install rich requests pytube")
    exit(1)

# --- Configuração e Constantes ---
SCRIPT_VERSION = "v2.1.0"
AUTHOR = "Seu Nome"
CREDITS = f"[bold magenta]{AUTHOR} (2025)[/bold magenta]"

# Diretórios
CWD = os.getcwd()
VIDEO_DOWNLOAD_DIR = os.path.join(CWD, "VideosDownloads")
AUDIO_DOWNLOAD_DIR = os.path.join(CWD, "AudiosDownloads")

# Configuração do Console Rich
console = Console()

# Configuração de Logging
logging.basicConfig(
    filename='pytools.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Funções Auxiliares e de UI ---
def clear_console() -> None:
    """Limpa o console de forma multiplataforma."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header() -> None:
    """Exibe o cabeçalho estilizado do programa."""
    header = Text("""
╔═╗┬ ┬┌─┐┌─┐┬  ┌─┐
╠═╝└┬┘│ ││  │  └─┐
╩   ┴ └─┘└─┘┴─┘└─┘
""", style="bold blue")
    version = Text(f"Versão {SCRIPT_VERSION}", style="bold cyan")
    credits = Text(f"por {AUTHOR}", style="bold magenta")
    
    console.print(header, justify="center")
    console.print(version, justify="center")
    console.print(credits, justify="center")
    console.print("")

def print_panel(content: str, title: str, style: str = "blue") -> None:
    """Exibe um painel formatado com Rich."""
    console.print(Panel.fit(
        content, 
        title=f"[bold]{title}[/bold]", 
        border_style=style, 
        box=ROUNDED,
        padding=(1, 2)
    ))

def print_section(title: str, style: str = "yellow") -> None:
    """Exibe um título de seção formatado."""
    console.print(f"\n[bold {style}]{'='*50}[/bold {style}]")
    console.print(f"[bold {style}]{title.upper()}[/bold {style}]")
    console.print(f"[bold {style}]{'='*50}[/bold {style}]\n")

def run_command(command: List[str], message: str, timeout: int = 300) -> bool:
    """Executa um comando do sistema com tratamento de erros."""
    print_panel(message, "Executando Comando", "cyan")
    
    try:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
            transient=True,
            console=console
        ) as progress:
            task = progress.add_task("[green]Processando...", total=100)
            
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            start_time = time.time()
            while process.poll() is None:
                if time.time() - start_time > timeout:
                    process.kill()
                    raise subprocess.TimeoutExpired(command, timeout)
                
                elapsed = min(time.time() - start_time, timeout)
                progress.update(task, completed=(elapsed/timeout)*100)
                time.sleep(0.1)
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error_msg = f"Erro (code {process.returncode}):\n{stderr.strip()}"
                print_panel(error_msg, "Falha no Comando", "red")
                logging.error(f"Comando {' '.join(command)} falhou: {stderr.strip()}")
                return False
            
            if stdout.strip():
                print_panel(stdout.strip(), "Saída do Comando", "green")
            
            return True

    except subprocess.TimeoutExpired:
        error_msg = f"O comando excedeu o tempo limite de {timeout} segundos"
        print_panel(error_msg, "Tempo Esgotado", "red")
        return False
    except FileNotFoundError:
        error_msg = f"Comando '{command[0]}' não encontrado"
        print_panel(error_msg, "Erro", "red")
        return False
    except Exception as e:
        print_panel(str(e), "Erro Inesperado", "red")
        logging.error(f"Erro ao executar comando {' '.join(command)}: {e}")
        return False

def slugify(text: str) -> str:
    """Converte texto para formato seguro em nomes de arquivo."""
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[\s-]+', '-', text)
    return text

# --- Funcionalidades do Menu ---
def update_system() -> None:
    """Atualiza os pacotes do sistema."""
    clear_console()
    print_header()
    print_section("Atualização do Sistema")
    
    is_termux = 'com.termux' in os.environ.get('PREFIX', '')
    
    commands = [
        (['pkg', 'update', '-y'], "Atualizando listas de pacotes...") if is_termux 
        else (['sudo', 'apt', 'update', '-y'], "Atualizando listas de pacotes..."),
        
        (['pkg', 'upgrade', '-y'], "Atualizando pacotes...") if is_termux
        else (['sudo', 'apt', 'upgrade', '-y'], "Atualizando pacotes..."),
        
        (None, None) if is_termux 
        else (['sudo', 'apt', 'autoremove', '-y'], "Removendo pacotes não usados..."),
        
        (None, None) if is_termux
        else (['sudo', 'apt', 'autoclean', '-y'], "Limpando cache...")
    ]
    
    success = True
    for cmd, msg in commands:
        if cmd and msg:
            if not run_command(cmd, msg):
                success = False
                break
    
    if success:
        print_panel("Sistema atualizado com sucesso!", "Concluído", "green")
    else:
        print_panel("Ocorreram erros durante a atualização", "Aviso", "yellow")
    
    input("\n[dim]Pressione Enter para continuar...[/dim]")

def ping_host() -> None:
    """Realiza ping para um host."""
    clear_console()
    print_header()
    print_section("Teste de Ping")
    
    host = console.input("[bold cyan]Digite o host ou IP para pingar: [/bold cyan]")
    if not host:
        console.print("[red]Nenhum host especificado.[/red]")
        time.sleep(1.5)
        return
    
    count = "4" if not os.name == 'nt' else "n"
    run_command(['ping', f'-{count}', '4', host], f"Testando conexão com {host}")
    input("\n[dim]Pressione Enter para continuar...[/dim]")

def geolocate_ip() -> None:
    """Obtém informações de geolocalização para um IP."""
    clear_console()
    print_header()
    print_section("Geolocalização de IP")
    
    ip = console.input("[bold cyan]Digite o IP para geolocalizar: [/bold cyan]")
    if not ip:
        console.print("[red]Nenhum IP especificado.[/red]")
        time.sleep(1.5)
        return
    
    try:
        print_panel("Obtendo informações de geolocalização...", "Consultando", "cyan")
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query")
        data = response.json()
        
        if data.get('status') != 'success':
            raise ValueError(data.get('message', 'Erro desconhecido'))
        
        table = Table(show_header=False, box=ROUNDED)
        table.add_column("Campo", style="bold cyan")
        table.add_column("Valor", style="green")
        
        for key, value in data.items():
            if key not in ['status', 'message']:
                table.add_row(key.capitalize(), str(value))
        
        print_panel(table, "Resultado da Geolocalização", "green")
        logging.info(f"Geolocalização bem-sucedida para IP: {ip}")
        
    except Exception as e:
        print_panel(f"Erro ao geolocalizar IP: {e}", "Erro", "red")
        logging.error(f"Falha na geolocalização para IP {ip}: {e}")
    
    input("\n[dim]Pressione Enter para continuar...[/dim]")

def show_disk_usage() -> None:
    """Exibe o uso de disco do sistema."""
    clear_console()
    print_header()
    print_section("Uso de Disco")
    
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        table = Table(title="Espaço em Disco", box=ROUNDED)
        for header in lines[0].split():
            table.add_column(header, style="bold blue")
        
        for line in lines[1:]:
            parts = line.split()
            # Destaca partições com pouco espaço livre
            style = "red" if int(parts[4].replace('%', '')) > 80 else None
            table.add_row(*parts, style=style)
        
        console.print(table)
    except Exception as e:
        print_panel(f"Erro ao obter uso de disco: {e}", "Erro", "red")
    
    input("\n[dim]Pressione Enter para continuar...[/dim]")

def show_memory_usage() -> None:
    """Exibe o uso de memória do sistema."""
    clear_console()
    print_header()
    print_section("Uso de Memória")
    
    try:
        result = subprocess.run(['free', '-h'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        table = Table(title="Uso de Memória", box=ROUNDED)
        for header in lines[0].split():
            table.add_column(header, style="bold magenta")
        
        for line in lines[1:]:
            parts = line.split()
            style = None
            if parts[0] == 'Mem:':
                style = "cyan"
            elif parts[0] == 'Swap:':
                style = "yellow"
            table.add_row(*parts, style=style)
        
        console.print(table)
    except Exception as e:
        print_panel(f"Erro ao obter uso de memória: {e}", "Erro", "red")
    
    input("\n[dim]Pressione Enter para continuar...[/dim]")

def handle_youtube_download() -> None:
    """Gerencia downloads do YouTube."""
    clear_console()
    print_header()
    print_section("YouTube Downloader")
    
    url = console.input("[bold cyan]URL do vídeo/playlist do YouTube: [/bold cyan]")
    if not url:
        return
    
    try:
        # Verifica se é playlist
        if 'playlist' in url.lower():
            playlist = Playlist(url)
            console.print(f"\n[bold]Playlist:[/bold] [cyan]{playlist.title}[/cyan]")
            console.print(f"[bold]Vídeos:[/bold] [yellow]{len(playlist.videos)}[/yellow]")
            
            confirm = console.input("\n[bold]Deseja baixar toda a playlist? (S/N): [/bold]").lower()
            if confirm != 's':
                return
            
            urls = playlist.video_urls
        else:
            urls = [url]
        
        # Tipo de download
        console.print("\n[bold]Tipo de download:[/bold]")
        console.print("1. [green]Vídeo (MP4)[/green]")
        console.print("2. [magenta]Áudio (MP3)[/magenta]")
        choice = console.input("\n[bold]Escolha (1/2): [/bold]")
        
        if choice not in ['1', '2']:
            console.print("[red]Opção inválida.[/red]", style="red")
            time.sleep(1.5)
            return
        
        # Cria diretórios se não existirem
        os.makedirs(VIDEO_DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(AUDIO_DOWNLOAD_DIR, exist_ok=True)
        
        # Processa cada URL
        with Progress(
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
            console=console
        ) as progress:
            for video_url in urls:
                try:
                    yt = YouTube(video_url)
                    safe_title = slugify(yt.title)
                    
                    if choice == '1':
                        stream = yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()
                        path = os.path.join(VIDEO_DOWNLOAD_DIR, f"{safe_title}.mp4")
                        desc = f"Baixando vídeo: {yt.title[:30]}..."
                    else:
                        stream = yt.streams.filter(only_audio=True).first()
                        path = os.path.join(AUDIO_DOWNLOAD_DIR, f"{safe_title}.mp3")
                        desc = f"Baixando áudio: {yt.title[:30]}..."
                    
                    task = progress.add_task(desc, total=stream.filesize)
                    
                    # Callback de progresso
                    def on_progress(stream, chunk, bytes_remaining):
                        progress.update(task, completed=stream.filesize - bytes_remaining)
                    
                    yt.register_on_progress_callback(on_progress)
                    
                    # Realiza o download
                    stream.download(
                        output_path=os.path.dirname(path),
                        filename=os.path.basename(path)
                    )
                    
                except RegexMatchError:
                    progress.print(f"[red]Erro: URL inválida ou vídeo indisponível: {video_url}[/red]")
                except Exception as e:
                    progress.print(f"[red]Erro ao processar {video_url}: {str(e)}[/red]")
                    logging.error(f"Falha no download: {video_url} - {str(e)}")
        
        print_panel("Downloads concluídos com sucesso!", "Concluído", "green")
        
    except PytubeError as e:
        print_panel(f"Erro no YouTube Downloader: {e}", "Erro", "red")
    except Exception as e:
        print_panel(f"Erro inesperado: {e}", "Erro", "red")
    
    input("\n[dim]Pressione Enter para continuar...[/dim]")

def temporary_email() -> None:
    """Gerencia e-mail temporário."""
    clear_console()
    print_header()
    print_section("E-mail Temporário")
    
    try:
        # Gera e-mail aleatório
        response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
        email = response.json()[0]
        login, domain = email.split('@')
        
        print_panel(
            f"[bold]E-mail temporário gerado:[/bold] [green]{email}[/green]\n\n"
            "Aguardando mensagens... Pressione [bold red]Ctrl+C[/bold red] para sair.",
            "E-mail Temporário",
            "green"
        )
        
        displayed_messages = set()
        
        try:
            with Live(refresh_per_second=4, console=console) as live:
                while True:
                    # Verifica caixa de entrada
                    response = requests.get(
                        f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
                    )
                    messages = response.json()
                    
                    # Cria tabela de mensagens
                    table = Table(
                        title=f"Mensagens para [bold]{email}[/bold]",
                        box=ROUNDED,
                        header_style="bold magenta"
                    )
                    table.add_column("ID", style="dim")
                    table.add_column("De")
                    table.add_column("Assunto")
                    table.add_column("Data")
                    
                    if not messages:
                        table.add_row("-", "Nenhuma mensagem", "-", "-", style="dim")
                    
                    for msg in messages:
                        if msg['id'] not in displayed_messages:
                            # Notifica nova mensagem
                            print_panel(
                                f"[bold]Nova mensagem de:[/bold] {msg['from']}\n"
                                f"[bold]Assunto:[/bold] {msg['subject']}",
                                "Nova Mensagem Recebida!",
                                "yellow"
                            )
                            displayed_messages.add(msg['id'])
                        
                        table.add_row(
                            str(msg['id']),
                            msg['from'],
                            msg['subject'],
                            msg['date']
                        )
                    
                    live.update(table)
                    time.sleep(5)
                    
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Saindo do e-mail temporário...[/bold yellow]")
        
    except requests.RequestException as e:
        print_panel(f"Erro de conexão: {e}", "Erro", "red")
    except Exception as e:
        print_panel(f"Erro inesperado: {e}", "Erro", "red")
    
    time.sleep(1)

def update_script() -> None:
    """Atualiza o script via Git."""
    clear_console()
    print_header()
    print_section("Atualização do Script")
    
    print_panel(
        "Esta função tentará atualizar o script usando Git.\n"
        "Certifique-se de que:\n"
        "1. O script está em um repositório Git clonado\n"
        "2. Você tem permissões de escrita\n"
        "3. Há conexão com a internet",
        "Aviso",
        "yellow"
    )
    
    confirm = console.input("\n[bold]Deseja continuar? (S/N): [/bold]").lower()
    if confirm != 's':
        return
    
    commands = [
        (['git', 'fetch', '--all'], "Buscando atualizações..."),
        (['git', 'reset', '--hard', 'origin/main'], "Aplicando atualizações..."),
        (['git', 'pull'], "Finalizando atualização...")
    ]
    
    success = True
    for cmd, msg in commands:
        if not run_command(cmd, msg):
            success = False
            break
    
    if success:
        print_panel(
            "Script atualizado com sucesso!\n"
            "Por favor, execute o script novamente para aplicar as mudanças.",
            "Atualização Concluída",
            "green"
        )
        exit(0)
    else:
        print_panel(
            "A atualização falhou. Verifique:\n"
            "- Se está em um repositório Git\n"
            "- Suas permissões\n"
            "- Conexão com a internet",
            "Falha na Atualização",
            "red"
        )
    
    input("\n[dim]Pressione Enter para continuar...[/dim]")

# --- Menu Principal ---
def display_menu() -> None:
    """Exibe o menu principal."""
    clear_console()
    print_header()
    
    menu_options = [
        {"title": "Atualizar Sistema", "func": update_system},
        {"title": "Testar Conexão (Ping)", "func": ping_host},
        {"title": "Geolocalizar IP", "func": geolocate_ip},
        {"title": "Uso de Disco", "func": show_disk_usage},
        {"title": "Uso de Memória", "func": show_memory_usage},
        {"title": "YouTube Downloader", "func": handle_youtube_download},
        {"title": "E-mail Temporário", "func": temporary_email},
        {"title": "Atualizar Script", "func": update_script},
    ]
    
    table = Table(
        title="Menu Principal",
        box=ROUNDED,
        header_style="bold blue",
        show_lines=True
    )
    table.add_column("Opção", style="bold cyan")
    table.add_column("Descrição", style="green")
    
    for i, option in enumerate(menu_options, 1):
        table.add_row(str(i), option['title'])
    
    table.add_row("0", "[bold red]Sair[/bold red]")
    console.print(table)

def main() -> None:
    """Função principal."""
    menu_options = [
        {"title": "Atualizar Sistema", "func": update_system},
        {"title": "Testar Conexão (Ping)", "func": ping_host},
        {"title": "Geolocalizar IP", "func": geolocate_ip},
        {"title": "Uso de Disco", "func": show_disk_usage},
        {"title": "Uso de Memória", "func": show_memory_usage},
        {"title": "YouTube Downloader", "func": handle_youtube_download},
        {"title": "E-mail Temporário", "func": temporary_email},
        {"title": "Atualizar Script", "func": update_script},
    ]
    
    while True:
        try:
            display_menu()
            choice = console.input("\n[bold]Escolha uma opção: [/bold]")
            
            if choice == '0':
                console.print("\n[bold green]Obrigado por usar PyTools![/bold green]")
                break
            
            if not choice.isdigit() or not (1 <= int(choice) <= len(menu_options)):
                console.print("[red]Opção inválida![/red]")
                time.sleep(1.5)
                continue
            
            menu_options[int(choice)-1]['func']()
            
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Saindo...[/bold yellow]")
            break
        except Exception as e:
            logging.error(f"Erro no menu principal: {e}")
            console.print(f"[red]Erro inesperado: {e}[/red]")
            time.sleep(2)

if __name__ == "__main__":
    main()
