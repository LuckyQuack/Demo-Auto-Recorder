# Demo Processing Log

**Target Demo**: `gr1ks.dem.zst`
**Target Player**: `76561198370176682`
**Date**: 2026-01-29

## Step 1: Decompression
Convert the compressed Faceit demo (`.dem.zst`) to a raw demo (`.dem`).

```bash
python src/recorder/unpack_demo.py "gr1ks.dem.zst" "gr1ks.dem"
```

## Step 2: Parsing
Run the C# parser to extract player segments.

```powershell
.\src\parser\bin\Debug\net8.0\parser.exe "..\..\..\..\..\gr1ks.dem" 76561198370176682
```
*(Run from `src\parser\bin\Debug\net8.0` directory)*

## Step 3: Auto-Recording
Launch the automation to record clips.

```bash
.venv\Scripts\python src/recorder/auto_recorder.py segments.json --auto
```
