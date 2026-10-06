using System;
using System.Text.RegularExpressions;

// Presentation decisions are testable without creating a Windows form.
internal sealed class InstallerViewState {
    public string Heading { get; private set; }
    public string Status { get; private set; }
    public string PrimaryAction { get; private set; }
    public string PrimaryText { get; private set; }
    public string SecondaryAction { get; private set; }
    public string SecondaryText { get; private set; }
    public bool PrimaryEnabled { get; private set; }
    public bool ShowProgress { get; private set; }
    public bool ShowDetails { get; private set; }
    public bool ShowIso { get; private set; }
    public bool Animate { get; private set; }
    public int? StagePercent { get; private set; }
    public static InstallerViewState Welcome(string version = null, bool healthy = false, bool newerBuild = false) {
        return new InstallerViewState {
            Heading = "Automate Bloons TD 6",
            Status = version == null ? "Install BloonsPlus and connect your game in one guided setup." : "Installed version: " + version,
            PrimaryAction = version == null ? "start" : !healthy ? "repair" : newerBuild ? "update" : "launch",
            PrimaryText = version == null ? "Install BloonsPlus" : !healthy ? "Repair BloonsPlus" : newerBuild ? "Update BloonsPlus" : "Launch BloonsPlus",
            SecondaryAction = "options", SecondaryText = "Options", PrimaryEnabled = true
        };
    }
    public static InstallerViewState FromSnapshot(InstallerSnapshot snapshot) {
        if (snapshot == null || snapshot.Phase == "idle") return Welcome();
        string phase = snapshot.Phase;
        var view = new InstallerViewState {
            Heading = "Setting up BloonsPlus", Status = FriendlyStatus(snapshot.Status, phase),
            ShowProgress = true, SecondaryAction = "cancel", SecondaryText = "Pause setup"
        };
        bool active = phase != "failed" && phase != "cancelled" && phase != "restart_required" && phase != "complete";
        view.Animate = active && String.IsNullOrEmpty(snapshot.HumanAction) && (snapshot.Indeterminate || !snapshot.StageNumerator.HasValue);
        if (snapshot.StageNumerator.HasValue && snapshot.StageDenominator > 0)
            view.StagePercent = Math.Max(0, Math.Min(100, (int)(100.0 * snapshot.StageNumerator.Value / snapshot.StageDenominator.Value)));
        if (phase == "complete") {
            bool ready = snapshot.AppValidated && (!snapshot.EnvironmentRequired || snapshot.EnvironmentValidated);
            view.Heading = ready ? "BloonsPlus installed" : "Checking setup readiness";
            view.PrimaryAction = ready ? "launch" : null; view.PrimaryText = ready ? "Launch BloonsPlus" : "Checking readiness";
            view.PrimaryEnabled = ready; view.SecondaryAction = "close"; view.SecondaryText = "Close";
            view.Status = !ready ? "Required checks have not finished yet." : snapshot.EnvironmentRequired
                ? "Your app and game environment are ready." : "App installed — environment setup deferred.";
        } else if (phase == "restart_required") {
            view.Heading = "Windows needs a restart"; view.Status = "Completed work is saved. Restart Windows, then reopen setup to continue.";
            view.PrimaryAction = "restart_now"; view.PrimaryText = "Restart now"; view.PrimaryEnabled = true;
            view.SecondaryAction = "restart_later"; view.SecondaryText = "Later";
        } else if (phase == "failed" || phase == "cancelled" || snapshot.HumanAction == "retry" || snapshot.HumanAction == "wait_setup") {
            view.Heading = phase == "cancelled" ? "Setup paused" : "Setup needs attention";
            view.PrimaryAction = phase == "failed" ? "retry" : "resume"; view.PrimaryText = "Continue setup"; view.PrimaryEnabled = true;
            view.SecondaryAction = "details"; view.SecondaryText = "Show details"; view.ShowDetails = true; view.Animate = false;
        } else if (snapshot.HumanAction == "steam_sign_in") {
            view.Heading = "Sign in to Steam"; view.Status = "Sign in and enter any verification code in Steam inside the VM. Continue after BTD6 finishes installing.";
            view.PrimaryAction = "resume"; view.PrimaryText = "Check again"; view.PrimaryEnabled = true;
            view.SecondaryAction = "open_vm"; view.SecondaryText = "Open VM"; view.Animate = false;
        } else if (snapshot.HumanAction == "wait_replay") {
            view.Heading = "Waiting for your replay"; view.Status = "Setup continues after the replay finishes and its status is confirmed.";
            view.Animate = false;
        }
        return view;
    }
    private static string FriendlyStatus(string status, string phase) {
        if (String.IsNullOrWhiteSpace(status)) return "Checking required setup components.";
        if (Regex.IsMatch(status, @"(?i)@|\\users\\|/home/|ssh\.exe|RuntimeError|Traceback|Get-Process|X-Bloons-Setup-Key"))
            return phase == "failed" ? "A setup component needs attention. Open details, then retry." : "Checking setup. Open details for the current operation.";
        return status;
    }
}
