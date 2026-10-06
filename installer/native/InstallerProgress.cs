using System;

internal enum InstallerStage { Prepare = 1, Files, CppRuntime, Python, Finish }

internal sealed class InstallerProgress
{
    private static readonly string[] Names = { "", "Preparation", "App files", "Microsoft C++ runtime", "Python packages", "Finish & open" };
    public string Message { get; internal set; }
    public InstallerStage Stage { get; private set; }
    public int? Percent { get; private set; }
    public long? Numerator { get; private set; }
    public long? Denominator { get; private set; }
    public string Scope { get; private set; }
    public bool Failed { get; private set; }
    public bool IsBusy { get { return !Failed && !Percent.HasValue; } }
    public int Value { get { return Percent.GetValueOrDefault() * 10; } }
    public string Caption {
        get {
            string step = "Install step " + (int)Stage + " of 5 · " + Names[(int)Stage];
            if (Failed) return "Setup paused · " + step;
            return step + " · " + (Percent.HasValue
                ? (String.IsNullOrEmpty(Scope) ? "" : Scope + " ") + Percent.Value + "%"
                : "Working…");
        }
    }
    public InstallerProgress() { Update(InstallerStage.Prepare, null); }
    public void Update(InstallerStage stage, int? percent, string scope = null)
    {
        if ((int)stage < 1 || (int)stage > 5) throw new ArgumentOutOfRangeException("stage");
        if (percent.HasValue && (percent.Value < 0 || percent.Value > 100)) throw new ArgumentOutOfRangeException("percent");
        Stage = stage; Percent = percent; Scope = scope; Failed = false;
        Numerator = percent; Denominator = percent.HasValue ? (long?)100 : null;
    }
    public void Measure(long numerator, long denominator) {
        if (numerator < 0 || denominator <= 0 || numerator > denominator) throw new ArgumentOutOfRangeException("numerator");
        Numerator = numerator; Denominator = denominator;
        Percent = (int)(100.0 * numerator / denominator);
    }
    public void Fail() { Failed = true; }
}

