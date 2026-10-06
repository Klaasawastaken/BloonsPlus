using System;
using System.IO;
using System.Web.Script.Serialization;

// App-owned choices only. Steam credentials and bridge keys never enter this file.
internal static class InstallerPreferences {
    private sealed class Choices {
        public int protocolVersion {get;set;}
        public string installRoot {get;set;}
        public bool desktop {get;set;}
        public bool startMenu {get;set;}
        public bool launch {get;set;}
        public bool environment {get;set;}
        public string isoPath {get;set;}
    }
    public static void Save(InstallerOptions options) {
        if(options.Silent)return;
        InstallSession.AtomicWrite(Path.Combine(options.DataRoot,"installer-preferences.json"),new JavaScriptSerializer().Serialize(new Choices {
            protocolVersion=1,installRoot=options.InstallRoot,desktop=options.DesktopShortcut,startMenu=options.StartMenuShortcut,
            launch=options.LaunchAfterInstall,environment=options.RequestedVmSetup,isoPath=options.RequestedIsoPath
        }));
    }
    public static InstallerOptions Load(InstallerOptions fallback) {
        if(fallback.Silent)return fallback;
        string file=Path.Combine(fallback.DataRoot,"installer-preferences.json");
        try {
            if(!File.Exists(file)||new FileInfo(file).Length>65536)return fallback;
            var saved=new JavaScriptSerializer().Deserialize<Choices>(File.ReadAllText(file));
            if(saved==null||saved.protocolVersion!=1||String.IsNullOrWhiteSpace(saved.installRoot)||!Path.IsPathRooted(saved.installRoot))return fallback;
            string root=Path.GetFullPath(saved.installRoot);
            if(String.Equals(root.TrimEnd('\\'),Path.GetPathRoot(root).TrimEnd('\\'),StringComparison.OrdinalIgnoreCase))return fallback;
            string attempt=fallback.AttemptResultPath==null?null:Path.GetFileNameWithoutExtension(fallback.AttemptResultPath).Substring("installer-result-".Length);
            return new InstallerOptions(root,fallback.DataRoot,fallback.InstallerPath,fallback.Silent,attempt) {
                DesktopShortcut=saved.desktop,StartMenuShortcut=saved.startMenu,LaunchAfterInstall=saved.launch,
                RequestedVmSetup=saved.environment,RequestedIsoPath=saved.isoPath??""
            };
        }catch(IOException){return fallback;}catch(UnauthorizedAccessException){return fallback;}catch(ArgumentException){return fallback;}
    }
}
