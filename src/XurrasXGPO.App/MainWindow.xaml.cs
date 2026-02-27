using System.Diagnostics;
using System.Net.Http;
using System.Text;
using System.Windows;
using XurrasXGPO.App.Services;

namespace XurrasXGPO.App;

public partial class MainWindow : Window
{
    private readonly LauncherService _launcher = new();
    private readonly WikiService _wiki = new();

    private string _lang = "pt-BR";

    private readonly Dictionary<string, Dictionary<string, string>> _i18n = new()
    {
        ["pt-BR"] = new() {
            ["choose"] = "Escolha seu idioma",
            ["loading"] = "Carregando launcher...",
            ["check"] = "Checando internet, status e atualização...",
            ["offline"] = "Sem internet/Wi-Fi. O app exige conexão.",
            ["maintenance"] = "App em manutenção. Aguarde.",
            ["update"] = "Atualização obrigatória encontrada.",
            ["search"] = "Buscar",
            ["placeholder"] = "Pesquisar item, boss, arma, navio..."
        },
        ["en-US"] = new() {
            ["choose"] = "Choose your language",
            ["loading"] = "Loading launcher...",
            ["check"] = "Checking internet, status and update...",
            ["offline"] = "No internet/Wi-Fi. Connection is required.",
            ["maintenance"] = "App under maintenance.",
            ["update"] = "Mandatory update found.",
            ["search"] = "Search",
            ["placeholder"] = "Search item, boss, weapon, ship..."
        }
    };

    public MainWindow()
    {
        InitializeComponent();
    }

    private async void Language_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not FrameworkElement element || element.Tag is not string code) return;
        _lang = code;
        ApplyTexts();

        LanguageGrid.Visibility = Visibility.Collapsed;
        LauncherGrid.Visibility = Visibility.Visible;

        try
        {
            LauncherStatus.Text = T("check");
            LauncherProgress.Value = 20;
            await _launcher.EnsureInternetAsync();

            LauncherProgress.Value = 45;
            var cfg = await _launcher.FetchConfigAsync();
            if (!cfg.AppOnline)
                throw new InvalidOperationException(T("maintenance"));

            LauncherProgress.Value = 70;
            if (_launcher.NeedMandatoryUpdate(cfg))
            {
                LauncherStatus.Text = T("update");
                await _launcher.DownloadAndStageUpdateAsync(cfg);
                MessageBox.Show("Atualização baixada. O app será reiniciado.");
                Application.Current.Shutdown();
                return;
            }

            LauncherProgress.Value = 100;
            LauncherGrid.Visibility = Visibility.Collapsed;
            MainGrid.Visibility = Visibility.Visible;
            await LoadDefaultTabs();
        }
        catch (HttpRequestException)
        {
            MessageBox.Show(T("offline"));
            Application.Current.Shutdown();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message);
            Application.Current.Shutdown();
        }
    }

    private async Task LoadDefaultTabs()
    {
        SearchBox.Text = T("placeholder");
        await FillTabs("Grand Piece Online");
    }

    private async void SearchButton_Click(object sender, RoutedEventArgs e)
    {
        var q = string.IsNullOrWhiteSpace(SearchBox.Text) ? "Grand Piece Online" : SearchBox.Text.Trim();
        await FillTabs(q);
    }

    private async Task FillTabs(string q)
    {
        BossesText.Text = await BuildSection(q + " Boss");
        WeaponsText.Text = await BuildSection(q + " Sword Weapon Gun");
        ShipsText.Text = await BuildSection(q + " Ship Boat");
        PassesText.Text = await BuildSection(q + " Gamepass");
        MerchantsText.Text = await BuildSection(q + " Merchant NPC");
        TradeText.Text = await BuildSection(q + " Trade Value Meta");
    }

    private async Task<string> BuildSection(string query)
    {
        var sb = new StringBuilder();
        var results = await _wiki.SearchAsync(query);
        foreach (var item in results)
        {
            sb.AppendLine($"# {item.Title}");
            sb.AppendLine(item.Snippet);
            sb.AppendLine(item.Extract);
            sb.AppendLine($"Fonte: {item.SourceUrl}");
            sb.AppendLine();
        }
        return sb.ToString();
    }

    private void Discord_Click(object sender, RoutedEventArgs e)
        => Process.Start(new ProcessStartInfo("https://discord.gg/hKGt4Pw9Wr") { UseShellExecute = true });

    private string T(string key)
    {
        if (_i18n.TryGetValue(_lang, out var lang) && lang.TryGetValue(key, out var val)) return val;
        return _i18n["en-US"][key];
    }

    private void ApplyTexts()
    {
        LanguageTitle.Text = T("choose");
        LauncherTitle.Text = T("loading");
        SearchButton.Content = T("search");
    }
}
