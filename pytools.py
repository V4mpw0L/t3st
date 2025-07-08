#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyTools: Uma suíte de ferramentas de utilidade para Linux, Termux e Windows.
Versão avançada com novas funcionalidades, temas e melhorias de desempenho.
"""

import os
import subprocess
import time
import datetime
import requests
import socket
import re
import logging
import sys
import json
import yaml
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import platform
import psutil  # Nova biblioteca para monitoramento avançado

# Bibliotecas de terceiros
try:
    from rich.console import Console
    from rich.theme import Theme
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from pytube import YouTube, Playlist
    from pytube.exceptions import PytubeError
except ImportError as e:
    is_termux = 'com.termux' in os.environ.get('PREFIX', '')
    if is_termux:
        print("Erro de importação. No Termux, instale com: pkg install python-pip && pip install rich requests pytube pyyaml psutil")
    else:
        print("Erro de importação. Instale com: pip install rich requests pytube pyyaml psutil")
    sys.exit(1)

# --- Configuração e Constantes ---

# Informações do Script
SCRIPT_VERSION = "v2.1.0"
AUTHOR = "V4mpw0L (Revisado e Aprimorado por Grok 3)"
CREDITS = f"[bold magenta]{AUTHOR} (2025)[/bold magenta]"

# Carrega configurações de um arquivo YAML
def load_config() -> Dict[str, Any]:
    """Carrega configurações de um arquivo YAML ou retorna padrões."""
    default_config = {
        'video_download_dir': os.path.join(os.getcwd(), 'VideosDownloads'),
        'audio_download_dir': os.path.join(os.getcwd(), 'AudiosDownloads'),
        'log_file': 'pytools.log',
        'theme': 'dark',
        'max_download_threads': 3
    }
    try:
        with open('pytools_config.yaml', 'r') as f:
            config = yaml.safe_load(f) or {}
        return {**default_config, **config}
    except FileNotFoundError:
        return default_config

CONFIG = load_config()
VIDEO_DOWNLOAD_DIR = CONFIG['video_download_dir']
AUDIO_DOWNLOAD_DIR = CONFIG['audio_download_dir']
LOG_FILE = CONFIG['log_file']
MAX_DOWNLOAD_THREADS = CONFIG['max_download_threads']

# Temas personalizados para o Rich
THEMES = {
    'dark': Theme({
        'success': 'bold green',
        'error': 'bold red',
        'info': 'bold cyan',
        'warning': 'bold yellow',
        'header': 'bold magenta',
        'highlight': 'bold blue'
    }),
    'light': Theme({
        'success': 'green',
        'error': 'red',
        'info': 'cyan',
        'warning': 'yellow',
        'header': 'magenta',
        'highlight': 'blue'
    })
}

# Configuração do Console Rich
console = Console(theme=THEMES.get(CONFIG['theme'], THEMES['dark']))

# Configuração de Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Cache para geolocalização
IP_CACHE_FILE = 'ip_cache.json'

# --- Funções Auxiliares e de UI ---

def clear_console() -> None:
    """Limpa o console, compatível com Linux, Windows e Termux."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_panel(content: str, title: str, style: str = "info") -> None:
    """Exibe um painel formatado com Rich."""
    console.print(Panel(content, title=f"[bold]{title}[/bold]", border_style=style, expand=False))

def run_command(command: List[str], message: str) -> bool:
    """
    Executa um comando de sistema com uma barra de progresso e captura o resultado.
    Retorna True se bem-sucedido, False caso contrário.
    """
    if any(';' in arg or '|' in arg or '&' in arg for arg in command):
        print_panel("Comando inválido: contém caracteres não permitidos.", "Erro", "error")
        logging.error(f"Comando bloqueado por segurança: {' '.join(command)}")
        return False

    print_panel(message, "Executando Comando", "info")
    try:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            transient=True,
            console=console
        ) as progress:
            task = progress.add_task("[highlight]Processando...", total=None)
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            while process.poll() is None:
                time.sleep(0.1)
                progress.update(task, advance=1)

            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error_msg = f"Comando falhou com código {process.returncode}.\n[error]Erro:[/error]\n{stderr}"
                print_panel(error_msg, "Erro", "error")
                logging.error(f"Comando {' '.join(command)} falhou: {stderr.strip()}")
                return False
            
            if stdout:
                console.print(f"[success]Saída:[/success]\n{stdout}")

        return True

    except FileNotFoundError:
        error_msg = f"Comando '{command[0]}' não encontrado. Verifique se está instalado e no PATH."
        print_panel(error_msg, "Erro", "error")
        logging.error(error_msg)
        return False
    except Exception as e:
        print_panel(str(e), "Erro Inesperado", "error")
        logging.error(f"Erro ao executar comando {' '.join(command)}: {e}")
        return False

def slugify(text: str) -> str:
    """Converte um texto em um formato seguro para nome de arquivo (slug)."""
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[\s-]+', '-', text)
    return text[:100]  # Limita o tamanho para evitar nomes de arquivo muito longos

def validate_ip(ip: str) -> bool:
    """Valida se uma string é um endereço IP válido."""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def validate_domain(domain: str) -> bool:
    """Valida se uma string é um domínio válido."""
    pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))

def check_directory_writable(path: str) -> bool:
    """Verifica se o diretório é gravável."""
    try:
        os.makedirs(path, exist_ok=True)
        test_file = os.path.join(path, ".test_write")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return True
    except (OSError, PermissionError) as e:
        logging.error(f"Erro ao verificar diretório {path}: {e}")
        return False

# --- Funções de Cache ---

def load_ip_cache() -> Dict[str, Any]:
    """Carrega o cache de geolocalização de IPs."""
    try:
        with open(IP_CACHE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_ip_cache(cache: Dict[str, Any]) -> None:
    """Salva o cache de geolocalização de IPs."""
    with open(IP_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

# --- Funcionalidades do Menu ---

def update_system() -> None:
    """Atualiza os pacotes do sistema (APT ou PKG)."""
    clear_console()
    console.print("[warning]Iniciando atualização do sistema...[/warning]")
    
    is_termux = 'com.termux' in os.environ.get('PREFIX', '')
    
    if is_termux:
        commands = [
            (['pkg', 'update', '-y'], "Atualizando listas de pacotes..."),
            (['pkg', 'upgrade', '-y'], "Atualizando pacotes instalados..."),
        ]
    else:
        if os.name != 'nt' and os.geteuid() != 0:
            print_panel("Este comando requer privilégios de administrador. Execute com sudo.", "Erro", "error")
            return
        commands = [
            (['sudo', 'apt', 'update', '-y'], "Atualizando listas de pacotes..."),
            (['sudo', 'apt', 'upgrade', '-y'], "Atualizando pacotes instalados..."),
            (['sudo', 'apt', 'autoremove', '-y'], "Removendo pacotes não utilizados..."),
            (['sudo', 'apt', 'autoclean', '-y'], "Limpando cache de pacotes..."),
        ]

    all_successful = all(run_command(cmd, msg) for cmd, msg in commands)
    
    if all_successful:
        print_panel("O sistema foi atualizado com sucesso!", "Concluído", "success")
    else:
        print_panel("A atualização do sistema encontrou erros.", "Falha", "error")
    input("\nPressione Enter para continuar...")

def ping_host() -> None:
    """Pinga um host (website ou IP) e exibe o resultado."""
    clear_console()
    host = console.input("[info]Digite o website ou IP para pingar: [/info]").strip()
    if not host:
        console.print("[error]Nenhum host fornecido.[/error]")
        return
    if not (validate_ip(host) or validate_domain(host)):
        console.print("[error]Host inválido. Insira um IP ou domínio válido.[/error]")
        return
        
    console.print(f"\n[warning]Pingando {host}...[/warning]")
    run_command(['ping', '-c', '4', host], f"Pingando {host}")
    input("\nPressione Enter para continuar...")

def geolocate_ip() -> None:
    """Busca informações de geolocalização de um endereço IP."""
    clear_console()
    ip = console.input("[info]Digite o IP para geolocalizar: [/info]").strip()
    if not validate_ip(ip):
        console.print("[error]IP inválido. Insira um endereço IP válido.[/error]")
        return

    ip_cache = load_ip_cache()
    if ip in ip_cache:
        data = ip_cache[ip]
        table = Table(title=f"Geolocalização para [bold]{ip}[/bold] (Cache)", show_header=False)
    else:
        try:
            response = requests.get(f"https://ipinfo.io/{ip}/json")
            response.raise_for_status()
            data = response.json()
            ip_cache[ip] = data
            save_ip_cache(ip_cache)
            table = alltid(title=f"Geolocalização para [bold]{ip}[/bold]", show_header=False)
        except requests.RequestException as e:
            print_panel(f"Erro ao contatar o serviço de geolocalização: {e}", "Erro de Rede", "error")
            logging.error(f"Erro de geolocalização para o IP {ip}: {e}")
            return

    table.add_column("Campo", style="warning")
    table.add_column("Valor")
    for key, value in data.items():
        table.add_row(key.capitalize(), str(value))
    
    console.print(table)
    logging.info(f"Geolocalização bem-sucedida para o IP: {ip}")
    input("\nPressione Enter para continuar...")

def show_disk_usage() -> None:
    """Exibe o uso de disco do sistema em uma tabela."""
    clear_console()
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        table = Table(title="Uso de Disco", header_style="header")
        headers = lines[0].split()
        for header in headers:
            table.add_column(header, style="highlight")
            
        for line in lines[1:]:
            table.add_row(*line.split())
            
        console.print(table)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print_panel(f"Não foi possível obter o uso de disco: {e}", "Erro", "error")
    input("\nPressione Enter para continuar...")

def show_memory_usage() -> None:
    """Exibe o uso de memória e swap do sistema."""
    clear_console()
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        table = Table(title="Uso de Memória e Swap", header_style="header")
        table.add_column("Tipo", style="highlight")
        table.add_column("Total")
        table.add_column("Usado")
        table.add_column("Livre")
        table.add_column("Percentual", style="warning")
        
        table.add_row("Memória", f"{mem.total / (1024**3):.2f} GB", f"{mem.used / (1024**3):.2f} GB",
                      f"{mem.available / (1024**3):.2f} GB", f"{mem.percent}%", style="cyan")
        table.add_row("Swap", f"{swap.total / (1024**3):.2f} GB", f"{swap.used / (1024**3):.2f} GB",
                      f"{swap.free / (1024**3):.2f} GB", f"{swap.percent}%", style="yellow")
        
        console.print(table)
    except Exception as e:
        print_panel(f"Não foi possível obter o uso de memória: {e}", "Erro", "error")
    input("\nPressione Enter para continuar...")

def _download_stream(stream, title: str, path: str, p_bar: Progress) -> None:
    """Função auxiliar para baixar um stream do YouTube com barra de progresso."""
    task = p_bar.add_task(f"[info]Baixando '{title}'...", total=stream.filesize)
    
    def on_progress(stream, chunk, bytes_remaining):
        p_bar.update(task, completed=stream.filesize - bytes_remaining)
    
    try:
        yt = stream._monostate
        yt.register_on_progress_callback(on_progress)
        temp_path = path + ".temp"
        stream.download(output_path=os.path.dirname(path), filename=os.path.basename(temp_path))
        if path.endswith('.mp3'):
            if not run_command(['ffmpeg', '-i', temp_path, '-vn', '-acodec', 'mp3', path], "Convertendo para MP3..."):
                raise RuntimeError("Falha na conversão para MP3")
            os.remove(temp_path)
        else:
            os.rename(temp_path, path)
        p_bar.update(task, completed=stream.filesize)
    except Exception as e:
        logging.error(f"Falha no download de '{title}': {e}")
        p_bar.print(f"[error]Erro ao baixar '{title}': {e}[/error]")

def handle_youtube_download() -> None:
    """Gerencia o download de vídeos ou áudios do YouTube."""
    clear_console()
    if not (check_directory_writable(VIDEO_DOWNLOAD_DIR) and check_directory_writable(AUDIO_DOWNLOAD_DIR)):
        print_panel("Erro: Diretórios de download não são graváveis.", "Erro", "error")
        return

    url = console.input("[info]Insira a URL do vídeo ou playlist do YouTube: [/info]").strip()
    if not url:
        return

    try:
        if 'playlist' in url:
            playlist = Playlist(url)
            console.print(f"[warning]Playlist encontrada:[/] [bold]{playlist.title}[/]")
            urls = playlist.video_urls
        else:
            urls = [url]
            
        choice = console.input("[bold]O que deseja baixar? (1) [success]Vídeo[/success] (2) [header]Áudio (MP3)[/header]: [/bold]").strip()
        if choice not in ('1', '2'):
            console.print("[error]Opção inválida.[/error]")
            return

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
            console=console
        ) as progress:
            with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_THREADS) as executor:
                futures = []
                for video_url in urls:
                    yt = YouTube(video_url)
                    safe_title = slugify(yt.title)
                    stream = (yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()
                              if choice == '1' else
                              yt.streams.filter(only_audio=True).first())
                    path = os.path.join(VIDEO_DOWNLOAD_DIR if choice == '1' else AUDIO_DOWNLOAD_DIR,
                                        f"{safe_title}.{'mp4' if choice == '1' else 'mp3'}")
                    futures.append(executor.submit(_download_stream, stream, yt.title, path, progress))
                for future in futures:
                    future.result()

        print_panel("Downloads concluídos!", "Sucesso", "success")
    except PytubeError as e:
        print_panel(f"Erro do Pytube: {e}", "Erro", "error")
    except Exception as e:
        print_panel(f"Ocorreu um erro inesperado: {e}", "Erro", "error")

    input("\nPressione Enter para continuar...")

def temporary_email() -> None:
    """Gera um e-mail temporário e verifica a caixa de entrada."""
    clear_console()
    console.print("[warning]Aviso: E-mails temporários são públicos e não devem ser usados para dados sensíveis.[/warning]")
    try:
        api_url = "https://www.1secmail.com/api/v1/"
        response = requests.get(f"{api_url}?action=genRandomMailbox&count=1")
        response.raise_for_status()
        email = response.json()[0]
        login, domain = email.split('@')

        print_panel(f"Seu e-mail temporário é: [success]{email}[/success]\n"
                    "Digite 'q' para sair ou aguarde novos e-mails...",
                    "E-mail Temporário", "success")

        displayed_ids = set()
        with Live(console=console, screen=False, auto_refresh=False) as live:
            while True:
                user_input = console.input("")
                if user_input.lower() == 'q':
                    console.print("[warning]Retornando ao menu principal...[/warning]")
                    break

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
                                        "Novo E-mail!", "warning")
                            displayed_ids.add(mail['id'])

                    live.update(table, refresh=True)
                    time.sleep(5)
                
                except requests.RequestException:
                    time.sleep(10)

    except requests.RequestException as e:
        print_panel(f"Não foi possível conectar à API de e-mail: {e}", "Erro de Rede", "error")
    except Exception as e:
        print_panel(f"Ocorreu um erro: {e}", "Erro", "error")
    
    time.sleep(1)

def update_script() -> None:
    """Atualiza o script a partir de um repositório Git."""
    clear_console()
    def get_current_branch() -> Optional[str]:
        try:
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    branch = get_current_branch() or 'main'
    print_panel(f"Tentando atualizar o script via Git (branch: {branch})...", "Atualização", "warning")
    
    commands = [
        (['git', 'fetch', 'origin'], "Buscando atualizações remotas..."),
        (['git', 'reset', '--hard', f'origin/{branch}'], f"Resetando para a versão remota ({branch})..."),
    ]

    if all(run_command(cmd, msg) for cmd, msg in commands):
        print_panel("Script atualizado com sucesso!\nPor favor, reinicie o script para aplicar as mudanças.",
                    "Sucesso", "success")
        sys.exit(0)
    else:
        print_panel("A atualização via Git “‘falhou. Verifique se você clonou o repositório "
                    "e se o Git está configurado corretamente.", "Falha", "error")
    input("\nPressione Enter para continuar...")

def show_system_info() -> None:
    """Exibe informações detalhadas do sistema."""
    clear_console()
    table = Table(title="Informações do Sistema", show_header=False)
    table.add_column("Campo", style="warning")
    table.add_column("Valor")
    table.add_row("Versão do Script", SCRIPT_VERSION)
    table.add_row("Sistema Operacional", platform.system())
    table.add_row("Versão do Sistema", platform.release())
    table.add_row("Versão do Python", sys.version.split()[0])
    table.add_row("Diretório Atual", os.getcwd())
    table.add_row("Tema Atual", CONFIG['theme'])
    table.add_row("Memória Total", f"{psutil.virtual_memory().total / (1024**3):.2f} GB")
    console.print(table)
    input("\nPressione Enter para continuar...")

def check_network_status() -> None:
    """Verifica o status da conexão de rede."""
    clear_console()
    console.print("[info]Verificando status da rede...[/info]")
    try:
        # Tenta conectar a um servidor confiável
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        console.print("[success]Conexão de rede ativa![/success]")
        
        # Obtém informações de interfaces de rede
        table = Table(title="Interfaces de Rede", header_style="header")
        table.add_column("Interface", style="highlight")
        table.add_column("Endereço IP")
        table.add_column("Status")
        
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    status = psutil.net_if_stats()[interface].isup
                    table.add_row(interface, addr.address, "Ativa" if status else "Inativa", style="success" if status else "error")
        
        console.print(table)
    except socket.error:
        print_panel("Sem conexão de rede. Verifique sua internet.", "Erro de Rede", "error")
    except Exception as e:
        print_panel(f"Erro ao verificar rede: {e}", "Erro", "error")
    input("\nPressione Enter para continuar...")

def clean_temp_files() -> None:
    """Remove arquivos temporários do sistema."""
    clear_console()
    temp_dirs = [os.path.join(os.getenv('TEMP', '/tmp') if os.name == 'nt' else '/tmp')]
    console.print("[warning]Limpando arquivos temporários...[/warning]")
    
    total_size = 0
    file_count = 0
    
    for temp_dir in temp_dirs:
        try:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        os.remove(file_path)
                        file_count += 1
                    except (OSError, PermissionError):
                        continue
            print_panel(f"Removidos {file_count} arquivos, liberando {(total_size / (1024**2)):.2f} MB.",
                        "Limpeza Concluída", "success")
        except Exception as e:
            print_panel(f"Erro ao limpar arquivos temporários: {e}", "Erro", "error")
    
    input("\nPressione Enter para continuar...")

# --- Menu Principal e Execução ---

def display_main_menu(menu_options: List[Dict[str, Any]]) -> None:
    """Exibe o menu principal de opções."""
    clear_console()
    
    logo = """
[header]  ____        _   _   _  ____  _      _      
 |  _ \ _   _| |_| |_| |/ ___|| |    | |     
 | |_) | | | | __| __| | |    | |    | |     
 |  __/| |_| | |_| |_| | |___ | |___ | |___  
 |_|    \__, |\__|\__|_|\____||_____||_____| 
        |___/                                
    [/header]
    """
    console.print(logo, justify="center")
    console.print(f"[info]Version {SCRIPT_VERSION}[/info]", justify="center")
    console.print(CREDITS, justify="center")
    
    menu_table = Table(show_header=False, box=None)
    menu_table.add_column(style="info")
    menu_table.add_column()
    
    for i, option in enumerate(menu_options, 1):
        menu_table.add_row(f"{i}.", option['title'])
    
    console.print(menu_table)
    console.print(f"[error]{len(menu_options) + 1}.[/error] Sair")

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
        {"title": "Informações do Sistema", "func": show_system_info},
        {"title": "Verificar Status da Rede", "func": check_network_status},
        {"title": "Limpar Arquivos Temporários", "func": clean_temp_files},
    ]
    
    while True:
        display_main_menu(menu_options)
        try:
            choice_str = console.input("\n[bold]Escolha uma opção: [/bold]").strip()
            if not choice_str.isdigit():
                console.print("[error]Entrada inválida. Por favor, insira um número.[/error]")
                time.sleep(1.5)
                continue
                
            choice = int(choice_str)
            
            if 1 <= choice <= len(menu_options):
                menu_options[choice - 1]['func']()
            elif choice == len(menu_options) + 1:
                console.print("[warning]Saindo... Até logo![/warning]")
                break
            else:
                console.print("[error]Opção inválida. Tente novamente.[/error]")
                time.sleep(1.5)

        except KeyboardInterrupt:
            console.print("\n[warning]Saindo... Até logo![/warning]")
            break
        except Exception as e:
            logging.error(f"Erro inesperado no menu principal: {e}")
            print_panel(f"Ocorreu um erro crítico: {e}", "Erro Fatal", "error")
            time.sleep(3)

if __name__ == "__main__":
    main()