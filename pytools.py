#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyTools: Uma suíte de ferramentas de utilidade para Linux e Termux.
"""

import os
import subprocess
import time
import requests
import socket
import re
import logging
import secrets
import string
from typing import List, Dict, Any, Optional, Tuple

# Bibliotecas de terceiros
try:
    from rich.console import Console
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich.rule import Rule
    from rich.prompt import Prompt, IntPrompt
    from pytube import YouTube, Playlist
    from pytube.exceptions import PytubeError, AgeRestrictedError, VideoUnavailable
except ImportError as e:
    print(f"Erro de importação: {e}. Por favor, instale as dependências necessárias.")
    print("Execute: pip install rich requests pytube")
    exit(1)


# --- Configuração e Constantes ---

SCRIPT_VERSION = "v2.5.0"
AUTHOR = "V4mpw0L (Revisado e Aprimorado por Gemini)"
CREDITS = f"[bold magenta]{AUTHOR} (2025)[/bold magenta]"

CWD = os.getcwd()
VIDEO_DOWNLOAD_DIR = os.path.join(CWD, "VideosDownloads")
AUDIO_DOWNLOAD_DIR = os.path.join(CWD, "AudiosDownloads")

console = Console()

logging.basicConfig(
    filename='pytools.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

# --- Funções Auxiliares e de UI ---

def clear_console() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')

def print_panel(content: str, title: str, style: str = "blue") -> None:
    console.print(Panel(content, title=f"[bold]{title}[/bold]", border_style=style, expand=False))

def run_shell_command(command: List[str], title: str) -> None:
    """Executa um comando de terminal e exibe a saída diretamente."""
    clear_console()
    print_panel(f"Executando: `{' '.join(command)}`", title, "cyan")
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print_panel(f"Comando '{command[0]}' não encontrado. Verifique se está instalado.", "Erro", "red")
    except subprocess.CalledProcessError as e:
        print_panel(f"O comando falhou com o código de saída {e.returncode}.", "Erro", "red")
    input("\n[yellow]Pressione Enter para continuar...[/yellow]")

def slugify(text: str) -> str:
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[\s-]+', '-', text)
    return text

# --- Funções de Sistema ---

def update_system() -> None:
    """Atualiza os pacotes do sistema (APT ou PKG)."""
    clear_console()
    console.print("[bold yellow]🚀 Iniciando atualização do sistema...[/bold yellow]")
    is_termux = 'com.termux' in os.environ.get('PREFIX', '')
    cmd = ['pkg'] if is_termux else ['sudo', 'apt']
    
    try:
        subprocess.run(cmd + ['update', '-y'], check=True)
        subprocess.run(cmd + ['upgrade', '-y'], check=True)
        if not is_termux:
            subprocess.run(cmd + ['autoremove', '-y'], check=True)
            subprocess.run(cmd + ['autoclean', '-y'], check=True)
        print_panel("O sistema foi atualizado com sucesso!", "Concluído", "green")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print_panel(f"A atualização falhou: {e}", "Erro", "red")
    input("\n[yellow]Pressione Enter para continuar...[/yellow]")

def show_system_info() -> None:
    """Exibe informações do sistema usando 'neofetch'."""
    run_shell_command(['neofetch'], "💻 Informações do Sistema")

def show_disk_usage() -> None:
    """Exibe o uso de disco do sistema em uma tabela."""
    clear_console()
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        table = Table(title="📊 Uso de Disco", header_style="bold blue")
        headers = lines[0].split()
        for header in headers:
            table.add_column(header)
            
        for line in lines[1:]:
            table.add_row(*line.split())
            
        console.print(table)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print_panel(f"Não foi possível obter o uso de disco: {e}", "Erro", "red")
    input("\n[yellow]Pressione Enter para continuar...[/yellow]")

def list_processes() -> None:
    """Exibe os processos em execução em uma tabela."""
    clear_console()
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')

        table = Table(title="⚙️ Processos em Execução", header_style="bold green", expand=True)
        headers = [h for h in lines[0].split(None, 10)] # Split max 10 times
        
        # Manually define headers for better control
        table.add_column("USER")
        table.add_column("PID")
        table.add_column("%CPU")
        table.add_column("%MEM")
        table.add_column("TTY")
        table.add_column("STAT")
        table.add_column("START")
        table.add_column("TIME")
        table.add_column("COMMAND")
        
        for line in lines[1:]:
            parts = line.split(None, 10)
            if len(parts) > 9:
                table.add_row(parts[0], parts[1], parts[2], parts[3], parts[6], parts[7], parts[8], parts[9], parts[10])

        console.print(table)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print_panel(f"Não foi possível listar os processos: {e}", "Erro", "red")
    input("\n[yellow]Pressione Enter para continuar...[/yellow]")

# --- Funções de Rede ---

def ping_host() -> None:
    """Pinga um host (website ou IP)."""
    host = Prompt.ask("[bold cyan]📡 Digite o website ou IP para pingar[/bold cyan]")
    if not host:
        return
    run_shell_command(['ping', '-c', '4', host], f"Pingando {host}")

def show_network_info() -> None:
    """Exibe informações das interfaces de rede."""
    clear_console()
    try:
        result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, check=True)
        
        panel_content = ""
        for line in result.stdout.strip().split('\n'):
            if re.match(r'^\d+:', line):
                panel_content += f"\n[bold yellow]{line.strip()}[/bold yellow]\n"
            elif 'inet ' in line:
                panel_content += f"  [green]{line.strip()}[/green]\n"
            else:
                panel_content += f"  [dim]{line.strip()}[/dim]\n"
        
        print_panel(panel_content, "🌐 Informações de Rede", "cyan")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print_panel(f"Não foi possível obter informações de rede: {e}", "Erro", "red")
    input("\n[yellow]Pressione Enter para continuar...[/yellow]")

def perform_traceroute() -> None:
    """Executa um traceroute para um destino."""
    host = Prompt.ask("[bold cyan]🗺️ Digite o destino para o traceroute[/bold cyan]")
    if not host:
        return
    run_shell_command(['traceroute', host], f"Traceroute para {host}")

# --- Funções de Segurança ---

def check_password_strength() -> None:
    """Verifica a força de uma senha fornecida pelo usuário."""
    clear_console()
    password = Prompt.ask("[bold cyan]🔒 Digite a senha para verificar a força[/bold cyan]", password=True)
    
    score = 0
    feedback = []
    
    if len(password) >= 8:
        score += 1
        feedback.append("[green]✓ Pelo menos 8 caracteres.[/green]")
    else:
        feedback.append("[red]✗ Menos de 8 caracteres.[/red]")
        
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'[A-Z]', password):
        score += 1
    if score < 3:
        feedback.append("[red]✗ Faltam letras maiúsculas ou minúsculas.[/red]")
    else:
        feedback.append("[green]✓ Contém letras maiúsculas e minúsculas.[/green]")
        
    if re.search(r'\d', password):
        score += 1
        feedback.append("[green]✓ Contém números.[/green]")
    else:
        feedback.append("[red]✗ Não contém números.[/red]")

    if re.search(r'[\W_]', password):
        score += 1
        feedback.append("[green]✓ Contém símbolos especiais.[/green]")
    else:
        feedback.append("[red]✗ Não contém símbolos especiais.[/red]")

    strength_map = {
        0: ("[on red]MUITO FRACA[/on red]", "red"),
        1: ("[on red]MUITO FRACA[/on red]", "red"),
        2: ("[red]FRACA[/red]", "red"),
        3: ("[yellow]MÉDIA[/yellow]", "yellow"),
        4: ("[green]FORTE[/green]", "green"),
        5: ("[bold green]MUITO FORTE[/bold green]", "green"),
    }
    strength_text, panel_color = strength_map.get(score, strength_map[0])
    
    feedback_str = "\n".join(feedback)
    print_panel(f"Força da Senha: {strength_text}\n\n{feedback_str}", "Análise de Senha", panel_color)
    input("\n[yellow]Pressione Enter para continuar...[/yellow]")

def generate_password() -> None:
    """Gera uma senha segura com base nos critérios do usuário."""
    clear_console()
    print_panel("Gerador de Senhas Seguras", "🔑", "green")
    length = IntPrompt.ask("Qual o comprimento da senha?", default=16)
    use_uppercase = Prompt.ask("Incluir letras maiúsculas? (s/n)", default="s").lower() == 's'
    use_digits = Prompt.ask("Incluir números? (s/n)", default="s").lower() == 's'
    use_symbols = Prompt.ask("Incluir símbolos? (s/n)", default="s").lower() == 's'

    alphabet = string.ascii_lowercase
    if use_uppercase:
        alphabet += string.ascii_uppercase
    if use_digits:
        alphabet += string.digits
    if use_symbols:
        alphabet += string.punctuation
        
    if not alphabet:
        print_panel("Você deve selecionar pelo menos um tipo de caractere!", "Erro", "red")
        return

    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    print_panel(f"Sua nova senha segura é:\n\n[bold white on green] {password} [/bold white on green]", "Senha Gerada", "green")
    input("\n[yellow]Pressione Enter para continuar...[/yellow]")

# --- Funções de Utilitários ---

def _download_stream_with_progress(stream, title: str, path: str, p_bar: Progress):
    """Auxiliar para baixar stream com barra de progresso."""
    task = p_bar.add_task(f"[cyan]Baixando '{title[:30]}...'[/cyan]", total=stream.filesize)
    try:
        stream.download(output_path=os.path.dirname(path), filename=os.path.basename(path))
        p_bar.update(task, completed=stream.filesize)
        p_bar.print(f"[green]✓ Download concluído:[/green] {os.path.basename(path)}")
    except Exception as e:
        p_bar.print(f"[red]✗ Erro ao baixar '{title}': {e}[/red]")
        logging.error(f"Falha no download de '{title}': {e}")


def handle_youtube_download() -> None:
    """Gerencia o download de vídeos ou áudios do YouTube."""
    clear_console()
    url = Prompt.ask("[bold cyan]▶️ Insira a URL do vídeo ou playlist do YouTube[/bold cyan]")
    if not url: return

    is_playlist = 'playlist' in url

    try:
        if is_playlist:
            pl = Playlist(url)
            console.print(f"🎵 Playlist encontrada: [bold]{pl.title}[/bold] ({len(pl.video_urls)} vídeos)")
            urls = pl.video_urls
        else:
            # Testa a URL para falhar rápido se for inválida
            yt_test = YouTube(url)
            console.print(f"🎬 Vídeo encontrado: [bold]{yt_test.title}[/bold]")
            urls = [url]
            
        choice = IntPrompt.ask("[bold]O que deseja baixar? (1) [green]Vídeo[/green] (2) [magenta]Áudio (MP3)[/magenta][/bold]", choices=["1", "2"])

        os.makedirs(VIDEO_DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(AUDIO_DOWNLOAD_DIR, exist_ok=True)
        
        with Progress(TextColumn("{task.description}"), BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%", TimeRemainingColumn(), console=console) as progress:
            for i, video_url in enumerate(urls, 1):
                try:
                    yt = YouTube(video_url)
                    if is_playlist:
                        progress.print(f"[yellow]Processando vídeo {i}/{len(urls)}: {yt.title}[/yellow]")

                    safe_title = slugify(yt.title)
                    
                    if choice == 1: # Vídeo
                        streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
                        if not streams:
                            progress.print(f"[red]Nenhum stream de vídeo progressivo encontrado para {yt.title}[/red]")
                            continue
                        
                        stream_choices = {f"{idx+1}": stream for idx, stream in enumerate(streams)}
                        console.print("\n[bold]Selecione a resolução:[/bold]")
                        for k, s in stream_choices.items():
                            size_mb = s.filesize / (1024*1024)
                            console.print(f"  [cyan]{k}[/cyan] - {s.resolution} ({size_mb:.2f} MB)")
                        
                        res_choice = Prompt.ask("[bold]Escolha um número[/bold]", choices=stream_choices.keys(), default="1")
                        stream = stream_choices[res_choice]
                        path = os.path.join(VIDEO_DOWNLOAD_DIR, f"{safe_title}_{stream.resolution}.mp4")
                        
                    else: # Áudio
                        stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
                        if not stream:
                           progress.print(f"[red]Nenhum stream de áudio encontrado para {yt.title}[/red]")
                           continue
                        path = os.path.join(AUDIO_DOWNLOAD_DIR, f"{safe_title}.mp3")

                    _download_stream_with_progress(stream, yt.title, path, progress)

                except AgeRestrictedError:
                    progress.print(f"[red]✗ Vídeo '{yt.title}' tem restrição de idade e não pôde ser baixado.[/red]")
                except VideoUnavailable:
                    progress.print(f"[red]✗ Vídeo '{yt.title}' está indisponível.[/red]")
                except Exception as e:
                    progress.print(f"[red]✗ Ocorreu um erro com o vídeo '{yt.title}': {e}[/red]")

        print_panel("Todos os downloads foram concluídos!", "Sucesso", "green")
    except Exception as e:
        print_panel(f"Ocorreu um erro ao processar a URL: {e}", "Erro", "red")
    
    input("\n[yellow]Pressione Enter para continuar...[/yellow]")


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
                    "📧 E-mail Temporário", "green")

        displayed_ids = set()
        table = Table(title=f"Caixa de Entrada de [bold]{email}[/bold]")
        table.add_column("De")
        table.add_column("Assunto")
        table.add_column("Data")

        with Live(table, console=console, screen=False, auto_refresh=False) as live:
            while True:
                try:
                    check_url = f"{api_url}?action=getMessages&login={login}&domain={domain}"
                    res = requests.get(check_url, timeout=10)
                    res.raise_for_status()
                    inbox = res.json()

                    # Recria a tabela para limpar e atualizar
                    new_table = Table(title=f"Caixa de Entrada de [bold]{email}[/bold] (Última verificação: {time.strftime('%H:%M:%S')})")
                    new_table.add_column("De", style="cyan")
                    new_table.add_column("Assunto", style="yellow")
                    new_table.add_column("Data", style="dim")
                    
                    if not inbox:
                        new_table.add_row("Caixa de entrada vazia...", "", "")
                    
                    for mail in inbox:
                        new_table.add_row(mail['from'], mail['subject'], mail['date'])
                        if mail['id'] not in displayed_ids:
                             console.print(Panel(f"[bold]De:[/] {mail['from']}\n[bold]Assunto:[/] {mail['subject']}",
                                         title="🎉 Novo E-mail!", border_style="yellow"))
                             displayed_ids.add(mail['id'])

                    live.update(new_table, refresh=True)
                    time.sleep(5)
                
                except requests.RequestException:
                    live.update(f"[red]Erro de conexão... Tentando novamente em 10s.[/red]", refresh=True)
                    time.sleep(10)

    except requests.RequestException as e:
        print_panel(f"Não foi possível conectar à API de e-mail: {e}", "Erro de Rede", "red")
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Retornando ao menu principal...[/bold yellow]")
        time.sleep(1)

# --- Menu Principal e Execução ---

def display_main_menu(menu_options: List[Dict[str, Any]]) -> None:
    clear_console()
    
    logo = """
[bold blue]
  _____       _   _              _     
 |  __ \     | | | |            | |    
 | |__) |   _| |_| | _____   ___| |___ 
 |  ___/ | | | __| |/ / _ \ / __| / __|
 | |   | |_| | |_|   < (_) | (__| \__ \\
 |_|    \__, |\__|_|\_\___/ \___|_|___/
         __/ |                        
        |___/                         
[/bold blue]
    """
    console.print(Panel(logo, border_style="blue", expand=False), justify="center")
    console.print(f"[bold cyan]Versão {SCRIPT_VERSION}[/bold cyan]", justify="center")
    console.print(CREDITS, justify="center")
    
    menu_panel_content = ""
    last_category = ""
    for i, option in enumerate(menu_options, 1):
        if option['category'] != last_category:
            menu_panel_content += f"\n[bold magenta]--- {option['category']} ---[/bold magenta]\n"
            last_category = option['category']
        menu_panel_content += f"  [bold cyan]{i}.[/bold cyan] {option['title']}\n"
        
    menu_panel_content += "\n[bold red]--- Sair ---[/bold red]\n"
    menu_panel_content += f"  [bold red]{len(menu_options) + 1}.[/bold red] Sair do PyTools\n"

    console.print(Panel(menu_panel_content, title="[bold]Menu Principal[/bold]", border_style="green"))


def main() -> None:
    menu_options = [
        {"category": "Sistema", "title": "🚀 Atualizar o sistema", "func": update_system},
        {"category": "Sistema", "title": "💻 Informações do Sistema", "func": show_system_info},
        {"category": "Sistema", "title": "📊 Ver Uso de Disco", "func": show_disk_usage},
        {"category": "Sistema", "title": "⚙️ Listar Processos", "func": list_processes},
        {"category": "Rede", "title": "📡 Pingar um Host", "func": ping_host},
        {"category": "Rede", "title": "🌐 Informações de Rede", "func": show_network_info},
        {"category": "Rede", "title": "🗺️ Traceroute", "func": perform_traceroute},
        {"category": "Segurança", "title": "🔒 Verificar Força de Senha", "func": check_password_strength},
        {"category": "Segurança", "title": "🔑 Gerar Senha Segura", "func": generate_password},
        {"category": "Utilitários", "title": "▶️ Download do YouTube", "func": handle_youtube_download},
        {"category": "Utilitários", "title": "📧 E-mail Temporário", "func": temporary_email},
    ]
    
    while True:
        display_main_menu(menu_options)
        try:
            choice = IntPrompt.ask("\n[bold]Escolha uma opção[/bold]", choices=[str(i) for i in range(1, len(menu_options) + 2)])
            
            if 1 <= choice <= len(menu_options):
                menu_options[choice - 1]['func']()
            elif choice == len(menu_options) + 1:
                console.print("\n[bold yellow]Saindo... Até logo! 👋[/bold yellow]")
                break

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Saindo... Até logo! 👋[/bold yellow]")
            break
        except Exception as e:
            logging.critical(f"Erro fatal no loop principal: {e}", exc_info=True)
            print_panel(f"Ocorreu um erro crítico: {e}\nVerifique 'pytools.log' para detalhes.", "Erro Fatal", "red")
            time.sleep(3)


if __name__ == "__main__":
    main()

