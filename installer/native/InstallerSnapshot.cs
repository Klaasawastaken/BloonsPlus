using System;

internal sealed class InstallerSnapshot
{
    public int ProtocolVersion { get; set; }
    public string SessionId { get; set; }
    public string Operation { get; set; }
    public long Sequence { get; set; }
    public string ObservedAt { get; set; }
    public string Phase { get; set; }
    public string Step { get; set; }
    public string Status { get; set; }
    public long? StageNumerator { get; set; }
    public long? StageDenominator { get; set; }
    public string ProgressScope { get; set; }
    public bool Indeterminate { get; set; }
    public int PlanWeight { get; set; }
    public int CompletedWeight { get; set; }
    public bool EnvironmentRequired { get; set; }
    public bool AppValidated { get; set; }
    public bool EnvironmentValidated { get; set; }
    public bool RestartDeferred { get; set; }
    public string HumanAction { get; set; }
    public string Error { get; set; }
    public string BackupPath { get; set; }
    public string RestartBootIdentity { get; set; }
}
