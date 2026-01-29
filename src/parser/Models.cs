using System.Text.Json.Serialization;

namespace DemoParser
{
    public class Segment
    {
        [JsonPropertyName("start_tick")]
        public int StartTick { get; set; }

        [JsonPropertyName("end_tick")]
        public int EndTick { get; set; }

        [JsonPropertyName("duration_sec")]
        public double DurationSec { get; set; }

        [JsonPropertyName("end_reason")]
        public string EndReason { get; set; } = string.Empty;

        [JsonPropertyName("round_number")]
        public int RoundNumber { get; set; }
    }

    public class ParserOutput
    {
        [JsonPropertyName("player")]
        public string PlayerName { get; set; } = string.Empty;

        [JsonPropertyName("steamid")]
        public string SteamId { get; set; } = string.Empty;

        [JsonPropertyName("demo")]
        public string DemoName { get; set; } = string.Empty;

        [JsonPropertyName("tick_rate")]
        public int TickRate { get; set; }

        [JsonPropertyName("segments")]
        public List<Segment> Segments { get; set; } = new List<Segment>();

        [JsonPropertyName("total_segments")]
        public int TotalSegments => Segments.Count;

        [JsonPropertyName("total_duration_sec")]
        public double TotalDurationSec => Segments.Sum(s => s.DurationSec);
    }
}
