# Xurras x GPO Wiki (Launcher + App)

Projeto de desktop (Windows 10/11) em **Python/Tkinter** com visual moderno, em **um único executável** (fluxo: launcher → app principal).

## O que já está implementado

- Tela inicial de **seleção de idioma** com bandeiras.
- **Launcher integrado** com:
  - validação obrigatória de internet;
  - leitura de status remoto (`on/off`) e versão mínima;
  - bloqueio por manutenção;
  - atualização obrigatória por hash SHA-256 (integridade);
  - botão de suporte para Discord.
- App principal em abas:
  - Bosses
  - Espadas/Armas
  - Navios
  - Gamepasses
  - Merchants
  - Trade Meta
- Busca automática na wiki do GPO (Fandom API), retornando título, resumo e link da fonte.
- Arquitetura pronta para personalizar background/GIF/música via config remota.

> Observação: “segurança total impossível de burlar” não existe em software cliente. Aqui foi implementado um baseline robusto (check de rede, manutenção remota, update obrigatório com hash e bloqueio de execução fora da política).

## Arquivos

- `app.py`: app completo (launcher + wiki UI).
- `requirements.txt`: dependências Python.
- `remote_config.example.json`: modelo de configuração remota para publicar no seu GitHub.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate  # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Como transformar em .exe (Windows)

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "Xurras x GPO" app.py
```

O executável final ficará em `dist/Xurras x GPO.exe`.

## Publicação da config remota

1. Copie `remote_config.example.json` para `remote_config.json` no seu repositório público.
2. Preencha:
   - `app_online` (true/false)
   - `min_version`
   - `latest_version`
   - `update_url` (link direto para .exe)
   - `update_sha256` (hash do arquivo publicado)
3. Troque a constante `CONFIG_URL` em `app.py` para seu URL real no GitHub raw.

