using System.Text.Json;
using XurrasXGPO.App.Models;

namespace XurrasXGPO.App.Services;

public sealed class WikiService
{
    private const string BaseApi = "https://grand-piece-online.fandom.com/api.php";
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(20) };

    public async Task<IReadOnlyList<WikiResult>> SearchAsync(string query)
    {
        var url = $"{BaseApi}?action=query&list=search&srsearch={Uri.EscapeDataString(query)}&format=json&srlimit=8";
        using var searchDoc = JsonDocument.Parse(await _http.GetStringAsync(url));
        var arr = searchDoc.RootElement.GetProperty("query").GetProperty("search");
        var list = new List<WikiResult>();
        foreach (var item in arr.EnumerateArray())
        {
            var title = item.GetProperty("title").GetString() ?? "";
            var snippet = (item.GetProperty("snippet").GetString() ?? "")
                .Replace("<span class=\"searchmatch\">", "")
                .Replace("</span>", "");
            var extract = await ExtractAsync(title);
            list.Add(new WikiResult
            {
                Title = title,
                Snippet = snippet,
                Extract = extract,
                SourceUrl = $"https://grand-piece-online.fandom.com/wiki/{Uri.EscapeDataString(title.Replace(' ', '_'))}"
            });
        }
        return list;
    }

    private async Task<string> ExtractAsync(string title)
    {
        var url = $"{BaseApi}?action=query&prop=extracts&titles={Uri.EscapeDataString(title)}&format=json&exintro=1&explaintext=1";
        using var doc = JsonDocument.Parse(await _http.GetStringAsync(url));
        var pages = doc.RootElement.GetProperty("query").GetProperty("pages");
        foreach (var p in pages.EnumerateObject())
        {
            if (p.Value.TryGetProperty("extract", out var ex))
                return (ex.GetString() ?? "Sem descrição disponível.").Trim();
        }
        return "Sem descrição disponível.";
    }
}
