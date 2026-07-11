using System;
using System.Diagnostics;

class OneClawHelperGatewayShim
{
    static int Main(string[] args)
    {
        string npmOpenClaw = @"C:\Users\scrccpa\AppData\Roaming\npm\openclaw.cmd";
        var psi = new ProcessStartInfo();
        psi.FileName = npmOpenClaw;
        psi.Arguments = "gateway run";
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;
        psi.RedirectStandardOutput = false;
        psi.RedirectStandardError = false;
        var proc = Process.Start(psi);
        if (proc == null) return 1;
        proc.WaitForExit();
        return proc.ExitCode;
    }
}
