using System;
using System.IO;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Web.Script.Serialization;
using System.Text.RegularExpressions;
using System.Reflection;

internal sealed class InstallerInventory {
    internal sealed class Entry { public string path { get; set; } public string sha256 { get; set; } }
    internal sealed class Manifest { public int protocolVersion { get; set; } public string version { get; set; } public string fingerprint { get; set; } public Entry[] files { get; set; } }
    public bool Exists { get; private set; }
    public bool FilesHealthy { get; private set; }
    public bool DifferentBuild { get; private set; }
    public string Version { get; private set; }
    public static string CurrentFingerprint {
        get {
            using(var stream=Assembly.GetExecutingAssembly().GetManifestResourceStream("BloonsPlus.Package")) {
                if(stream==null)return null;
                using(var reader=new StreamReader(stream)) {
                    var manifest=new JavaScriptSerializer {MaxJsonLength=8*1024*1024}.Deserialize<Manifest>(reader.ReadToEnd());
                    return manifest==null?null:manifest.fingerprint;
                }
            }
        }
    }
    private static Manifest Read(string root) {
        string file=Path.Combine(root,"bloons-package.json");
        if(!File.Exists(file))return null;
        if(new FileInfo(file).Length>8*1024*1024)throw new InvalidDataException("App inventory exceeds its size limit.");
        var result=new JavaScriptSerializer {MaxJsonLength=8*1024*1024}.Deserialize<Manifest>(File.ReadAllText(file));
        if(result==null||result.protocolVersion!=1||result.files==null||result.files.Length>20000||!Regex.IsMatch(result.version??"",@"^[0-9A-Za-z.+ -]{1,64}$"))throw new InvalidDataException("App inventory is invalid. Repair the app before removing files.");
        var seen=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach(var entry in result.files) {
            if(entry==null||!Regex.IsMatch(entry.sha256??"",@"^[a-f0-9]{64}$")||!seen.Add(Destination(root,entry.path)))throw new InvalidDataException("App inventory has an invalid entry.");
        }
        return result;
    }
    private static string Destination(string root,string relative) {
        if(String.IsNullOrEmpty(relative)||Path.IsPathRooted(relative)||relative.Contains(":"))throw new InvalidDataException("Invalid app inventory path.");
        string prefix=Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
        string target=Path.GetFullPath(Path.Combine(prefix,relative.Replace('/',Path.DirectorySeparatorChar)));
        if(!target.StartsWith(prefix,StringComparison.OrdinalIgnoreCase))throw new InvalidDataException("App inventory path leaves its installation.");
        // Reparse points can redirect an otherwise contained path outside the app.
        for(string part=target;part!=null;part=Path.GetDirectoryName(part)) {
            if((File.Exists(part)||Directory.Exists(part))&&(File.GetAttributes(part)&FileAttributes.ReparsePoint)!=0)throw new InvalidDataException("App inventory crosses a linked path.");
            if(String.Equals(part,prefix.TrimEnd(Path.DirectorySeparatorChar),StringComparison.OrdinalIgnoreCase))break;
        }
        return target;
    }
    private static bool Matches(string file,string expected) {
        if(!File.Exists(file))return false;
        using(var hash=SHA256.Create())using(var input=File.OpenRead(file))return String.Equals(BitConverter.ToString(hash.ComputeHash(input)).Replace("-","").ToLowerInvariant(),expected,StringComparison.Ordinal);
    }
    private static bool ValidRuntimeMapTable(string file) {
        // The app updates this table from its curated catalog and learned tile
        // positions. Those expected writes are not damaged package binaries.
        if(!File.Exists(file)||new FileInfo(file).Length>2*1024*1024)return false;
        try {
            var maps=new JavaScriptSerializer {MaxJsonLength=2*1024*1024,RecursionLimit=64}.Deserialize<Dictionary<string,object>>(File.ReadAllText(file));
            if(maps==null||maps.Count==0||maps.Count>2000)return false;
            var categories=new HashSet<string>(new[]{"beginner","intermediate","advanced","expert"},StringComparer.OrdinalIgnoreCase);
            foreach(var map in maps) {
                if(!Regex.IsMatch(map.Key,@"\A[a-z0-9_]{1,128}\z"))return false;
                var row=map.Value as Dictionary<string,object>;object category,name,page,pos;
                if(row==null||!row.TryGetValue("category",out category)||!(category is string)||!categories.Contains((string)category)
                    ||!row.TryGetValue("name",out name)||!(name is string)||String.IsNullOrWhiteSpace((string)name)||((string)name).Length>256
                    ||!row.TryGetValue("page",out page)||!(page is int)||(int)page<0
                    ||!row.TryGetValue("pos",out pos)||!(pos is int)||(int)pos<0||(int)pos>5)return false;
            }
            return true;
        }catch(ArgumentException){return false;}catch(InvalidOperationException){return false;}
    }
    private static bool Preserve(string relative) {
        string value="/"+relative.Replace('\\','/').ToLowerInvariant()+"/";
        return value.Contains("/data/config/")||value.Contains("/route-library/")||value.Contains("/playthroughs/")||value.Contains("/.bloons-setup/")
            ||value.Contains("/save/")||value.Contains("/saves/")||value.Contains("/userdata/")||value.Contains("/userconfig.json/")
            ||value.Contains("/automation-progress.json/")||value.Contains("/game-observations.json/")||value.Contains("/route-verification.json/")||value.Contains("/playthrough_stats.json/");
    }
    public static InstallerInventory Inspect(string root,string expectedFingerprint) {
        var observed=new InstallerInventory {Exists=File.Exists(Path.Combine(root,"Bloons+.exe"))||File.Exists(Path.Combine(root,"bloons-package.json"))};
        if(AppFileTransaction.Pending(root)){observed.Exists=true;return observed;}
        try {
            var manifest=Read(root);if(manifest==null)return observed;
            observed.Version=manifest.version;
            observed.FilesHealthy=true;
            foreach(var entry in manifest.files) {
                string file=Destination(root,entry.path);
                bool runtimeMaps=String.Equals(entry.path.Replace('\\','/'),"resources/app/autobtd6/maps.json",StringComparison.OrdinalIgnoreCase);
                if(!(runtimeMaps?ValidRuntimeMapTable(file):Matches(file,entry.sha256))){observed.FilesHealthy=false;break;}
            }
            observed.DifferentBuild=!String.IsNullOrEmpty(expectedFingerprint)&&manifest.fingerprint!=expectedFingerprint;
        }catch(IOException){observed.FilesHealthy=false;}catch(UnauthorizedAccessException){observed.FilesHealthy=false;}catch(ArgumentException){observed.FilesHealthy=false;}
        return observed;
    }
    public static int RemoveUnchangedFiles(string root) {
        if(AppFileTransaction.Pending(root))throw new IOException("App-file recovery is pending. Repair the local app before uninstalling.");
        var manifest=Read(root);if(manifest==null)throw new InvalidDataException("No trusted file inventory exists. Repair the local app before uninstalling.");
        // Validate every path before the first deletion. Modified and unlisted files stay.
        foreach(var entry in manifest.files)Destination(root,entry.path);
        int removed=0;
        foreach(var entry in manifest.files){if(Preserve(entry.path))continue;string file=Destination(root,entry.path);if(Matches(file,entry.sha256)){File.Delete(file);removed++;}}
        return removed;
    }
}
