using System;
using System.Text.RegularExpressions;

internal static class InstallerDiagnostics {
    public static string Redact(string text) {
        string value = text ?? "";
        value = Regex.Replace(value, @"(?s)-----BEGIN [^-]*(?:PRIVATE KEY|TOKEN)[^-]*-----.*?(?:-----END [^-]+-----|$)", "[private credential removed]");
        // Logs may contain JSON or Python dictionaries. Consume complete quoted
        // values, including escaped quotes and line continuations, so a suffix
        // cannot survive export. Dot does not consume LF in .NET regexes.
        value = Regex.Replace(value,
            @"(?i)((?<![\w-])(?:""|')?(?:authorization|password|passwd|secret|token|api[_-]?key|access[_-]?token|refresh[_-]?token|x-bloons-setup-key|session[_-]?id|account[_-]?(?:id|name)|player[_-]?(?:id|name)|steam[_-]?name|user[_-]?name|host[_-]?name)(?:""|')?\s*[:=]\s*)(?:""(?:\\[\s\S]|[^""\\])*(?:""|\\?$)|'(?:\\[\s\S]|[^'\\])*(?:'|\\?$)|[^\s,;}]+)",
            "$1\"[credential removed]\"");
        value = Regex.Replace(value, @"(?i)(?:[a-z]:[\\/]users[\\/]|/home/)[^\r\n""'<>]*", "[user path removed]");
        value = Regex.Replace(value, @"(?i)\b[^\s@]+@(?:[a-z0-9._-]+|\[[^\]]+\])", "[remote account removed]");
        value = Regex.Replace(value, @"(?i)(?:https?|ssh)://[^/\s]+", "[endpoint]");
        value = Regex.Replace(value, @"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[address]");
        value = Regex.Replace(value, @"(?i)(?:authorization|bearer|password|token|x-bloons-setup-key)\s*[:= ]\s*[^\r\n,;]+", "[credential removed]");
        value = Regex.Replace(value, @"(?i)\b[0-9a-f]{32,}\b", "[private identifier]");
        foreach (string identity in new[] { Environment.UserName, Environment.MachineName }) {
            if (!String.IsNullOrEmpty(identity)) value = Regex.Replace(value, Regex.Escape(identity), "[identity]", RegexOptions.IgnoreCase);
        }
        return value.Length <= 65536 ? value : value.Substring(0, 65500) + "\n[details truncated]";
    }
}
