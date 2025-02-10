# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from CLI                  import konsol
from Core                 import kekik_FastAPI, Request
from time                 import time
from user_agents          import parse
from Core.Modules._IP_Log import ip_log

@kekik_FastAPI.middleware("http")
async def istekten_once_sonra(request: Request, call_next):
    baslangic_zamani = time()

    if request.method == "GET":
        request.state.req_veri = dict(request.query_params) if request.query_params else None
    else:
        try:
            request.state.req_veri = await request.json()
        except Exception:
            form_data = await request.form()
            request.state.req_veri = dict(form_data.items())

    response   = await call_next(request)
    gecen_sure = time() - baslangic_zamani

    for skip_path in ("/favicon.ico", "/static", "/webfonts"):
        if skip_path in request.url.path:
            return response

    try:
        ua_header = request.headers.get("User-Agent")
        parsed_ua = parse(ua_header)
        cihaz = ua_header if str(parsed_ua).split("/")[2].strip() == "Other" else parsed_ua
    except Exception:
        cihaz = request.headers.get("User-Agent")

    log_ip  = request.headers.get("X-Forwarded-For") or request.client.host
    ip_w_cf = (
        f"{request.headers.get('Cf-Connecting-Ip')} [yellow]| CF: ({log_ip})[/]"
            if request.headers.get("Cf-Connecting-Ip")
               else log_ip
    )

    log_veri = {
        "id"     : request.headers.get("X-Request-ID") or "",
        "method" : request.method,
        "url"    : str(request.url).rstrip("?").split("?")[0],
        "veri"   : request.state.req_veri,
        "kod"    : response.status_code,
        "sure"   : round(gecen_sure, 2),
        "ip"     : log_ip,
        "cihaz"  : cihaz,
        "host"   : request.url.hostname,
    }

    log_url = (
        log_veri['url'].replace(request.url.scheme, request.headers.get("X-Forwarded-Proto"))
            if request.headers.get("X-Forwarded-Proto")
                else log_veri['url']
    )

    LABEL_WIDTH  = 5
    durum_label  = f"[green]{'durum':<{LABEL_WIDTH}}:[/]"
    ip_label     = f"[green]{'ip':<{LABEL_WIDTH}}:[/]"
    konum_label  = f"[green]{'konum':<{LABEL_WIDTH}}:[/]"
    cihaz_label  = f"[green]{'cihaz':<{LABEL_WIDTH}}:[/]"

    log_lines = []
    
    header_line = (
        f"[bold blue]»[/] [bold turquoise2]{log_url}[/]"
    )
    log_lines.append(header_line)

    if log_veri["veri"]:
        veri_line = f"[bold magenta]»[/] [bold cyan]{log_veri['veri']}[/]"
        log_lines.append(veri_line)

    durum_line = (
        f"  {durum_label} [bold green]{log_veri['method']}[/]"
        f" [blue]-[/] [bold bright_yellow]{log_veri['kod']}[/]"
        f" [blue]-[/] [bold yellow2]{log_veri['sure']} sn[/]"
    )
    log_lines.append(durum_line)

    if log_veri["id"]:
        ip_line = (
            f"  {ip_label} [bold bright_blue]{log_veri['id']}[/]"
            f"[bold green]@[/][bold red]{log_veri['ip']}[/]"
        )
    else:
        ip_line = f"  {ip_label} [bold red]{log_veri['ip']}[/]"
    log_lines.append(ip_line)

    ip_detay = await ip_log(log_veri["ip"].split()[0].replace(",", ""))
    if ("hata" not in ip_detay) and ip_detay.get("ulke"):
        il   = ip_detay["il"].replace(" Province", "")
        ilce = ip_detay["ilce"]

        host_str = " ".join(ip_detay["host"].split()[1:4])

        if il != ilce:
            konum_line = (
                f"  {konum_label} [bold chartreuse3]{ip_detay['ulke']}[/]"
                f" [blue]|[/] [bold chartreuse3]{il}[/]"
                f" [blue]|[/] [bold chartreuse3]{ilce}[/]"
                f" [blue]|[/] [bold chartreuse3]{host_str}[/]"
            )
        else:
            konum_line = (
                f"  {konum_label} [bold chartreuse3]{ip_detay['ulke']}[/]"
                f" [blue]|[/] [bold chartreuse3]{il}[/]"
                f" [blue]|[/] [bold chartreuse3]{host_str}[/]"
            )
        log_lines.append(konum_line)

    cihaz_line = f"  {cihaz_label} [magenta]{log_veri['cihaz']}[/]"
    log_lines.append(cihaz_line)

    final_log = "\n".join(log_lines)
    konsol.log(final_log + "\n")

    return response