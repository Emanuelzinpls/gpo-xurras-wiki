using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text.Json;
using XurrasXGPO.App.Models;

namespace XurrasXGPO.App.Services;

public sealed class LauncherService
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(20) };
    public const string AppVersion = "1.0.0";
    public const string ConfigUrl = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/remote_config.json";

    public async Task EnsureInternetAsync()
    {
        using var req = new HttpRequestMessage(HttpMethod.Head, "https://www.google.com/generate_204");
        using var res = await _http.SendAsync(req);
        res.EnsureSuccessStatusCode();
    }

    public async Task<RemoteConfig> FetchConfigAsync()
    {
        var json = await _http.GetStringAsync(ConfigUrl);
        var cfg = JsonSerializer.Deserialize<RemoteConfig>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
        return cfg ?? throw new InvalidOperationException("Config remota inválida.");
    }

    public bool NeedMandatoryUpdate(RemoteConfig cfg) => CompareVersion(AppVersion, cfg.MinVersion) < 0;

    public async Task DownloadAndStageUpdateAsync(RemoteConfig cfg)
    {
        var bin = await _http.GetByteArrayAsync(cfg.UpdateUrl);
        var hash = Convert.ToHexString(SHA256.HashData(bin)).ToLowerInvariant();
        if (!string.Equals(hash, cfg.UpdateSha256.ToLowerInvariant(), StringComparison.Ordinal))
            throw new InvalidOperationException("Hash de atualização inválido. Update bloqueado.");

        var exe = Environment.ProcessPath ?? throw new InvalidOperationException("Não foi possível localizar o executável.");
        var staged = exe + ".new";
        await File.WriteAllBytesAsync(staged, bin);

        var bat = Path.Combine(Path.GetTempPath(), "xurras_update_swap.bat");
        await File.WriteAllTextAsync(bat, $"@echo off\r\nsetlocal\r\ntimeout /t 2 >nul\r\nmove /Y \"{staged}\" \"{exe}\" >nul\r\nstart \"\" \"{exe}\"\r\n");
        Process.Start(new ProcessStartInfo("cmd.exe", $"/c \"{bat}\"") { CreateNoWindow = true, UseShellExecute = false });
    }

    private static int CompareVersion(string a, string b)
    {
        var pa = a.Split('.').Select(int.Parse).ToArray();
        var pb = b.Split('.').Select(int.Parse).ToArray();
        for (var i = 0; i < Math.Max(pa.Length, pb.Length); i++)
        {
            var va = i < pa.Length ? pa[i] : 0;
            var vb = i < pb.Length ? pb[i] : 0;
            if (va != vb) return va.CompareTo(vb);
        }
        return 0;
    }
}
