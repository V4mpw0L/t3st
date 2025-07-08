#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyTools: Uma suíte de ferramentas de utilidade para Linux e Termux.
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
    from pytube import YouTube, Playlist
    from pytube.exceptions import PytubeError
except ImportError as e:
    print(f"Erro de importação: {e}. Por favor, instale as dependências necessárias.")
    print("Execute: pip install rich requests pytube")
    exit(1)


# --- Configuração e Constantes ---

# Informações do Script
SCRIPT_VERSION = "v2.0.0"
AUTHOR = "V4mpw0L (Revisado por Gemini)"
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
    """Limpa o console, compatível com Linux, Windows e Termux."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_panel(content: str, title: str, style: str = "blue") -> None:
    """Exibe um painel formatado com Rich."""
    console.print(Panel(content, title=f"[bold]{title}[/bold]", border_style=style, expand=False))

def run_command(command: List[str], message: str) -> bool:
    """
    Executa um comando de sistema com uma barra de progresso e captura o resultado.
    Retorna True se bem-sucedido, False caso contrário.
    """
    print_panel(message, "Executando Comando", "cyan")
    try:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            transient=True,
            console=console
        ) as progress:
            task = progress.add_task("[green]Processando...", total=None)
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # A barra de progresso se move enquanto o comando está em execução
            while process.poll() is None:
                time.sleep(0.1)
                progress.update(task, advance=1)

            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error_msg = f"Comando falhou com código {process.returncode}.\n[bold red]Erro:[/bold red]\n{stderr}"
                print_panel(error_msg, "Erro", "red")
                logging.error(f"Comando {' '.join(command)} falhou: {stderr.strip()}")
                return False
            
            if stdout:
                console.print(f"[bold green]Saída:[/bold green]\n{stdout}")

        return True

    except FileNotFoundError:
        error_msg = f"Comando '{command[0]}' não encontrado. Verifique se está instalado e no PATH."
        print_panel(error_msg, "Erro", "red")
        logging.error(error_msg)
        return False
    except Exception as e:
        print_panel(str(e), "Erro Inesperado", "red")
        logging.error(f"Erro ao executar comando {' '.join(command)}: {e}")
        return False

def slugify(text: str) -> str:
    """Converte um texto em um formato seguro para nome de arquivo (slug)."""
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[\s-]+', '-', text)
    return text

# --- Funcionalidades do Menu ---

def update_system() -> None:
    """Atualiza os pacotes do sistema (APT ou PKG)."""
    clear_console()
    console.print("[bold yellow]Iniciando atualização do sistema...[/bold yellow]")
    
    is_termux = 'com.termux' in os.environ.get('PREFIX', '')
    
    if is_termux:
        commands = [
            (['pkg', 'update', '-y'], "Atualizando listas de pacotes..."),
            (['pkg', 'upgrade', '-y'], "Atualizando pacotes instalados..."),
        ]
    else:
        commands = [
            (['sudo', 'apt', 'update', '-y'], "Atualizando listas de pacotes..."),
            (['sudo', 'apt', 'upgrade', '-y'], "Atualizando pacotes instalados..."),
            (['sudo', 'apt', 'autoremove', '-y'], "Removendo pacotes não utilizados..."),
            (['sudo', 'apt', 'autoclean', '-y'], "Limpando cache de pacotes..."),
        ]

    all_successful = all(run_command(cmd, msg) for cmd, msg in commands)
    
    if all_successful:
        print_panel("O sistema foi atualizado com sucesso!", "Concluído", "green")
    else:
        print_panel("A atualização do sistema encontrou erros.", "Falha", "red")
    input("\nPressione Enter para continuar...")

def ping_host() -> None:
    """Pinga um host (website ou IP) e exibe o resultado."""
    clear_console()
    host = console.input("[bold cyan]Digite o website ou IP para pingar: [/bold cyan]")
    if not host:
        console.print("[red]Nenhum host fornecido.[/red]")
        return
        
    console.print(f"\n[yellow]Pingando {host}...[/yellow]")
    run_command(['ping', '-c', '4', host], f"Pingando {host}")
    input("\nPressione Enter para continuar...")

def geolocate_ip() -> None:
    """Busca informações de geolocalização de um endereço IP."""
    clear_console()
    ip = console.input("[bold cyan]Digite o IP para geolocalizar: [/bold cyan]")
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        response.raise_for_status()
        data = response.json()
        
        table = Table(title=f"Geolocalização para [bold]{ip}[/bold]", show_header=False)
        table.add_column("Campo", style="bold yellow")
        table.add_column("Valor")
        
        for key, value in data.items():
            table.add_row(key.capitalize(), str(value))
            
        console.print(table)
        logging.info(f"Geolocalização bem-sucedida para o IP: {ip}")

    except requests.RequestException as e:
        print_panel(f"Erro ao contatar o serviço de geolocalização: {e}", "Erro de Rede", "red")
        logging.error(f"Erro de geolocalização para o IP {ip}: {e}")
    input("\nPressione Enter para continuar...")

def show_disk_usage() -> None:
    """Exibe o uso de disco do sistema em uma tabela."""
    clear_console()
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        table = Table(title="Uso de Disco", header_style="bold blue")
        headers = lines[0].split()
        for header in headers:
            table.add_column(header)
            
        for line in lines[1:]:
            table.add_row(*line.split())
            
        console.print(table)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print_panel(f"Não foi possível obter o uso de disco: {e}", "Erro", "red")
    input("\nPressione Enter para continuar...")

def show_memory_usage() -> None:
    """Exibe o uso de memória e swap do sistema."""
    clear_console()
    try:
        result = subprocess.run(['free', '-h'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')

        table = Table(title="Uso de Memória e Swap", header_style="bold magenta")
        headers = lines[0].split()
        for header in headers:
            table.add_column(header.capitalize())
        
        for line in lines[1:]:
            # Adiciona cor à linha da Memória
            if line.startswith("Mem:"):
                table.add_row(*line.split(), style="cyan")
            # Adiciona cor à linha do Swap
            elif line.startswith("Swap:"):
                table.add_row(*line.split(), style="yellow")
            else:
                 table.add_row(*line.split())

        console.print(table)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print_panel(f"Não foi possível obter o uso de memória: {e}", "Erro", "red")
    input("\nPressione Enter para continuar...")

def _download_stream(stream, title: str, path: str, p_bar: Progress) -> None:
    """Função auxiliar para baixar um stream do YouTube com barra de progresso."""
    task = p_bar.add_task(f"[cyan]Baixando '{title}'...", total=stream.filesize)
    
    try:
        stream.download(output_path=os.path.dirname(path), filename=os.path.basename(path))
        p_bar.update(task, completed=stream.filesize)
    except Exception as e:
        logging.error(f"Falha no download de '{title}': {e}")
        p_bar.print(f"[red]Erro ao baixar '{title}': {e}[/red]")

def handle_youtube_download() -> None:
    """Gerencia o download de vídeos ou áudios do YouTube."""
    clear_console()
    url = console.input("[bold cyan]Insira a URL do vídeo ou playlist do YouTube: [/bold cyan]")
    if not url:
        return

    try:
        if 'playlist' in url:
            playlist = Playlist(url)
            console.print(f"[yellow]Playlist encontrada:[/] [bold]{playlist.title}[/]")
            urls = playlist.video_urls
        else:
            urls = [url]
            
        choice = console.input("[bold]O que deseja baixar? (1) [green]Vídeo[/green] (2) [magenta]Áudio (MP3)[/magenta]: [/bold]")

        os.makedirs(VIDEO_DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(AUDIO_DOWNLOAD_DIR, exist_ok=True)
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
            console=console
        ) as progress:
            for video_url in urls:
                yt = YouTube(video_url)
                safe_title = slugify(yt.title)
                
                if choice == '1':
                    stream = yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()
                    path = os.path.join(VIDEO_DOWNLOAD_DIR, f"{safe_title}.mp4")
                    _download_stream(stream, yt.title, path, progress)
                elif choice == '2':
                    stream = yt.streams.filter(only_audio=True).first()
                    path = os.path.join(AUDIO_DOWNLOAD_DIR, f"{safe_title}.mp3")
                    _download_stream(stream, yt.title, path, progress)
                else:
                    console.print("[red]Opção inválida.[/red]")
                    break

        print_panel("Downloads concluídos!", "Sucesso", "green")
    except PytubeError as e:
        print_panel(f"Erro do Pytube: {e}", "Erro", "red")
    except Exception as e:
        print_panel(f"Ocorreu um erro inesperado: {e}", "Erro", "red")

    input("\nPressione Enter para continuar...")

def temporary_email() -> None:
    """Gera um e-mail temporário e verifica a caixa de entrada."""
    clear_console()
    try:
        api_url = "https://www.1secmail.com/api/v1/"
        response = requests.get(f"{api_url}?action=genRandomMailbox&count=1")
        response.raise_for_status()
        email = response.json()[0]
        login, domain = email.split('@')

        print_panel(f"Seu e-mail temporário é: [bold green]{email}[/bold green]\n"
                    "Aguardando novos e-mails... Pressione [bold]Ctrl+C[/bold] para sair.",
                    "E-mail Temporário", "green")

        displayed_ids = set()
        with Live(console=console, screen=False, auto_refresh=False) as live:
            while True:
                check_url = f"{api_url}?action=getMessages&login={login}&domain={domain}"
                try:
                    res = requests.get(check_url)
                    res.raise_for_status()
                    inbox = res.json()

                    table = Table(title=f"Caixa de Entrada de [bold]{email}[/bold]")
                    table.add_column("ID", style="dim")
                    table.add_column("De")
                    table.add_column("Assunto")
                    table.add_column("Data")

                    if not inbox:
                        table.add_row("-", "Caixa de entrada vazia", "-", "-")
                    
                    for mail in inbox:
                        table.add_row(str(mail['id']), mail['from'], mail['subject'], mail['date'])
                        if mail['id'] not in displayed_ids:
                             print_panel(f"Novo E-mail de: {mail['from']}\nAssunto: {mail['subject']}",
                                         "Novo E-mail!", "yellow")
                             displayed_ids.add(mail['id'])

                    live.update(table, refresh=True)
                    time.sleep(5)
                
                except requests.RequestException:
                    time.sleep(10) # Aguarda mais em caso de erro de rede

    except requests.RequestException as e:
        print_panel(f"Não foi possível conectar à API de e-mail: {e}", "Erro de Rede", "red")
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Retornando ao menu principal...[/bold yellow]")
    except Exception as e:
        print_panel(f"Ocorreu um erro: {e}", "Erro", "red")
    
    time.sleep(1) # Pequena pausa antes de voltar ao menu


def update_script() -> None:
    """Atualiza o script a partir de um repositório Git."""
    clear_console()
    print_panel("Tentando atualizar o script via Git...", "Atualização", "yellow")
    
    commands = [
        (['git', 'fetch', 'origin'], "Buscando atualizações remotas..."),
        (['git', 'reset', '--hard', 'origin/main'], "Resetando para a versão remota..."), # ou main/master
    ]

    if all(run_command(cmd, msg) for cmd, msg in commands):
        print_panel("Script atualizado com sucesso!\nPor favor, reinicie o script para aplicar as mudanças.",
                    "Sucesso", "green")
        exit(0)
    else:
        print_panel("A atualização via Git falhou. Verifique se você clonou o repositório "
                    "e se o Git está configurado corretamente.", "Falha", "red")
    input("\nPressione Enter para continuar...")


# --- Menu Principal e Execução ---

def display_main_menu(menu_options: List[Dict[str, Any]]) -> None:
    """Exibe o menu principal de opções."""
    clear_console()
    
    logo = """
[bold blue]  ____        _   _   _  ____  _      _      
 |  _ \ _   _| |_| |_| |/ ___|| |    | |     
 | |_) | | | | __| __| | |    | |    | |     
 |  __/| |_| | |_| |_| | |___ | |___ | |___  
 |_|    \__, |\__|\__|_|\____||_____||_____| 
        |___/                                
    """
    console.print(logo, justify="center")
    console.print(f"[bold cyan]Version {SCRIPT_VERSION}[/bold cyan]", justify="center")
    console.print(CREDITS, justify="center")
    
    menu_table = Table(show_header=False, box=None)
    menu_table.add_column(style="bold cyan")
    menu_table.add_column()
    
    for i, option in enumerate(menu_options, 1):
        menu_table.add_row(f"{i}.", option['title'])
    
    console.print(menu_table)
    console.print(f"[bold red]{len(menu_options) + 1}.[/bold red] Sair")


def main() -> None:
    """Função principal que executa o loop do menu."""
    
    menu_options = [
        {"title": "Atualizar o sistema", "func": update_system},
        {"title": "Pingar um website ou IP", "func": ping_host},
        {"title": "Geolocalizar um IP", "func": geolocate_ip},
        {"title": "Ver Uso de Disco", "func": show_disk_usage},
        {"title": "Ver Uso de Memória", "func": show_memory_usage},
        {"title": "Download de Vídeo/Áudio do YouTube", "func": handle_youtube_download},
        {"title": "E-mail Temporário", "func": temporary_email},
        {"title": "Atualizar este Script (via Git)", "func": update_script},
    ]
    
    while True:
        display_main_menu(menu_options)
        try:
            choice_str = console.input("\n[bold]Escolha uma opção: [/bold]")
            if not choice_str.isdigit():
                console.print("[red]Entrada inválida. Por favor, insira um número.[/red]")
                time.sleep(1.5)
                continue
                
            choice = int(choice_str)
            
            if 1 <= choice <= len(menu_options):
                menu_options[choice - 1]['func']()
            elif choice == len(menu_options) + 1:
                console.print("[bold yellow]Saindo... Até logo![/bold yellow]")
                break
            else:
                console.print("[red]Opção inválida. Tente novamente.[/red]")
                time.sleep(1.5)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Saindo... Até logo![/bold yellow]")
            break
        except Exception as e:
            logging.error(f"Erro inesperado no menu principal: {e}")
            print_panel(f"Ocorreu um erro crítico: {e}", "Erro Fatal", "red")
            time.sleep(3)


if __name__ == "__main__":
    main()
