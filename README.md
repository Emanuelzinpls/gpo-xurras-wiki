# Xurras x GPO (C# / WPF)

Agora o projeto foi refeito em **C# (WPF)**, sem Python.

## Entrega
- App desktop para Windows 10/11 com fluxo único:
  1. Seleção de idioma com bandeiras.
  2. Launcher (internet obrigatória, manutenção on/off, atualização obrigatória).
  3. Wiki principal em abas (Bosses, Armas, Navios, Gamepasses, Merchants, Trade Meta).
- Busca automática de conteúdo no Fandom do GPO (título, resumo, fonte).
- Botão de suporte no Discord.

## Estrutura
- `src/XurrasXGPO.App`: app WPF completo.
- `remote_config.example.json`: modelo de controle remoto para manutenção e updates.

## Rodar localmente
```bash
dotnet restore src/XurrasXGPO.App/XurrasXGPO.App.csproj
dotnet run --project src/XurrasXGPO.App/XurrasXGPO.App.csproj
```

## Build Windows
```bash
dotnet publish src/XurrasXGPO.App/XurrasXGPO.App.csproj -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true
```

## Configuração remota
Edite e publique um `remote_config.json` no GitHub (raw URL) e ajuste `ConfigUrl` em `LauncherService.cs`.

Campos:
- `appOnline`: true/false
- `minVersion`: versão mínima permitida
- `latestVersion`: versão atual
- `updateUrl`: link direto do .exe novo
- `updateSha256`: hash SHA-256 do .exe
- `backgroundImageUrl`: imagem de fundo
