using System.Text.Json;
using DemoFile;
using DemoFile.Game.Cs;
using DemoFile.Sdk;
using DemoParser;

class Program
{
    private static int? _aliveStartTick;
    private static bool _waitingForMovement;
    private static bool _playerIsAlive;
    private static ulong _targetSteamId;
    private static List<Segment> _segments = new();
    private static string _targetPlayerName = string.Empty;
    private static int _tickRate = 64; // Default
    private static int _currentRound = 0;

    // Config
    private const double MOVEMENT_THRESHOLD = 50.0;
    private const int BUFFER_TICKS = 384; 

    static async Task Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("Usage: parser <path/to/demo.dem> <steamID64> OR parser <path/to/demo.dem> list");
            return;
        }

        string demoPath = args[0];

        if (args[1] == "list")
        {
            await ListPlayers(demoPath);
            return;
        }

        if (!ulong.TryParse(args[1], out _targetSteamId))
        {
            Console.WriteLine("Invalid SteamID64.");
            return;
        }

        Console.WriteLine($"Parsing demo: {demoPath} for SteamID: {_targetSteamId}");

        var demo = new CsDemoParser();

        // Event: Round Start
        demo.Source1GameEvents.RoundStart += e =>
        {
            _currentRound++;
        };

        // Event: Player Spawn
        demo.Source1GameEvents.PlayerSpawn += e =>
        {
            var player = e.Player; 
            if (player?.SteamID == _targetSteamId)
            {
                _playerIsAlive = true;
                _waitingForMovement = true;
                _aliveStartTick = null;
                _targetPlayerName = player.PlayerName;
            }
        };

        // Event: Player Death
        demo.Source1GameEvents.PlayerDeath += e =>
        {
            var player = e.Player;
            if (player?.SteamID == _targetSteamId && _aliveStartTick.HasValue)
            {
                SaveSegment(demo.CurrentDemoTick.Value, "death");
                _playerIsAlive = false;
                _aliveStartTick = null;
            }
        };

        // Event: Round End
        demo.Source1GameEvents.RoundEnd += e =>
        {
            if (_playerIsAlive && _aliveStartTick.HasValue)
            {
                SaveSegment(demo.CurrentDemoTick.Value, "round_end");
            }
            _playerIsAlive = false;
            _aliveStartTick = null;
            _waitingForMovement = false;
        };

        // Event: Player Disconnect
        demo.Source1GameEvents.PlayerDisconnect += e =>
        {
             var player = e.Player;
             if (player?.SteamID == _targetSteamId && _aliveStartTick.HasValue)
             {
                 SaveSegment(demo.CurrentDemoTick.Value, "disconnect");
                 _aliveStartTick = null;
             }
        };
        
        try
        {
            using var stream = File.OpenRead(demoPath);
            var reader = DemoFileReader.Create(demo, stream);
            await reader.StartReadingAsync(default);

            while (await reader.MoveNextAsync(default))
            {
                // Tick Logic
                if (_waitingForMovement)
                {
                    var player = demo.Players.FirstOrDefault(p => p.SteamID == _targetSteamId);
                    
                    if (player != null && player.PlayerPawn != null)
                    {
                        var pawn = player.PlayerPawn;
                        var vel = pawn.Velocity;
                        
                        var velocity = Math.Sqrt(vel.X * vel.X + vel.Y * vel.Y);
                        
                        if (velocity > MOVEMENT_THRESHOLD)
                        {
                            // Start recording
                            _aliveStartTick = Math.Max(0, demo.CurrentDemoTick.Value - BUFFER_TICKS);
                            _waitingForMovement = false;
                        }
                    }
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error parsing demo: {ex.Message}");
        }

        // End of demo
        if (_aliveStartTick.HasValue)
        {
            SaveSegment(demo.CurrentDemoTick.Value, "demo_end");
        }

        // Output JSON
        var output = new ParserOutput
        {
            PlayerName = _targetPlayerName,
            SteamId = _targetSteamId.ToString(),
            DemoName = Path.GetFileName(demoPath),
            TickRate = _tickRate,
            Segments = _segments
        };

        string json = JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true });
        string outputPath = Path.Combine(Path.GetDirectoryName(demoPath) ?? "", "segments.json");
        File.WriteAllText(outputPath, json);
        Console.WriteLine($"Segments saved to {outputPath}");
    }

    private static async Task ListPlayers(string demoPath)
    {
        Console.WriteLine($"Scanning demo: {demoPath} for players...");
        var demo = new CsDemoParser();
        var players = new Dictionary<ulong, string>();

        demo.Source1GameEvents.PlayerSpawn += e =>
        {
            var p = e.Player;
            if (p != null && !players.ContainsKey(p.SteamID))
            {
                players[p.SteamID] = p.PlayerName;
            }
        };

        try
        {
            using var stream = File.OpenRead(demoPath);
            var reader = DemoFileReader.Create(demo, stream);
            await reader.ReadAllAsync();

            Console.WriteLine("\n--- Players Found ---");
            foreach (var kvp in players)
            {
                Console.WriteLine($"Name: {kvp.Value}, SteamID: {kvp.Key}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error reading demo: {ex.Message}");
        }
    }

    private static void SaveSegment(int endTick, string reason)
    {
        if (!_aliveStartTick.HasValue) return;

        int start = _aliveStartTick.Value;
        int end = endTick;
        double duration = (end - start) / (double)_tickRate;

        _segments.Add(new Segment
        {
            StartTick = start,
            EndTick = end,
            DurationSec = duration,
            EndReason = reason,
            RoundNumber = _currentRound 
        });
    }
}
