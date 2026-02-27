namespace XurrasXGPO.App.Models;

public sealed class RemoteConfig
{
    public bool AppOnline { get; set; } = true;
    public string MinVersion { get; set; } = "1.0.0";
    public string LatestVersion { get; set; } = "1.0.0";
    public string UpdateUrl { get; set; } = string.Empty;
    public string UpdateSha256 { get; set; } = string.Empty;
    public string BackgroundImageUrl { get; set; } = string.Empty;
}
